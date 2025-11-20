import os
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from threading import Lock
import requests
import dotenv
import argparse
from tqdm import tqdm
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from structure import Structure

if os.path.exists(".env"):
    dotenv.load_dotenv()
else:
    dotenv.load_dotenv(dotenv.find_dotenv())

script_dir = os.path.dirname(os.path.abspath(__file__))
template = open(os.path.join(script_dir, "template.txt"), "r").read()
system = open(os.path.join(script_dir, "system.txt"), "r").read()

rate_lock = Lock()
next_allowed_at = 0.0


def throttle(interval: float):
    if interval <= 0:
        return

    global next_allowed_at
    with rate_lock:
        now = time.monotonic()
        wait_seconds = next_allowed_at - now
        if wait_seconds > 0:
            time.sleep(wait_seconds)
            now = time.monotonic()
        next_allowed_at = now + interval


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="jsonline data file")
    parser.add_argument("--max_workers", type=int, default=1, help="Maximum number of parallel workers")
    parser.add_argument(
        "--min-interval-secs",
        dest="min_interval_secs",
        type=float,
        default=60.0,
        help="Minimum global interval between LLM calls in seconds",
    )
    return parser.parse_args()


def process_single_item(chain, item: Dict, language: str, min_interval_secs: float) -> Dict:
    def is_sensitive(content: str) -> bool:
        resp = requests.post("https://spam.dw-dengwei.workers.dev", json={"text": content})
        if resp.status_code == 200:
            result = resp.json()
            return result.get("sensitive", True)
        return True

    if is_sensitive(item.get("summary", "")):
        return None

    throttle(min_interval_secs)
    response: Structure = chain.invoke({"language": language, "content": item["summary"]})
    item["AI"] = response.model_dump()

    for v in item.get("AI", {}).values():
        if is_sensitive(str(v)):
            return None
    return item


def process_all_items(
    data: List[Dict], model_name: str, language: str, max_workers: int, min_interval_secs: float
) -> List[Dict]:
    llm = ChatOpenAI(model=model_name).with_structured_output(Structure, method="function_calling")
    print("Connect to:", model_name, file=sys.stderr)

    prompt_template = ChatPromptTemplate.from_messages(
        [SystemMessagePromptTemplate.from_template(system), HumanMessagePromptTemplate.from_template(template=template)]
    )

    chain = prompt_template | llm

    processed_data = [None] * len(data)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(process_single_item, chain, item, language, min_interval_secs): idx
            for idx, item in enumerate(data)
        }

        for future in tqdm(as_completed(future_to_idx), total=len(data), desc="Processing items"):
            idx = future_to_idx[future]
            processed_data[idx] = future.result()

    return processed_data


def main():
    args = parse_args()
    model_name = os.environ.get("MODEL_NAME", "gemini-2.5-pro-preview")
    language = os.environ.get("LANGUAGE", "Japanese")

    target_file = args.data.replace(".jsonl", f"_AI_enhanced_{language}.jsonl")
    if os.path.exists(target_file):
        os.remove(target_file)
        print(f"Removed existing file: {target_file}", file=sys.stderr)

    data = []
    with open(args.data, "r") as f:
        for line in f:
            data.append(json.loads(line))

    seen_ids = set()
    unique_data = []
    for item in data:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_data.append(item)

    data = unique_data
    print("Open:", args.data, file=sys.stderr)

    processed_data = process_all_items(data, model_name, language, args.max_workers, args.min_interval_secs)

    with open(target_file, "w") as f:
        for item in processed_data:
            if item is not None:
                f.write(json.dumps(item) + "\n")


if __name__ == "__main__":
    main()

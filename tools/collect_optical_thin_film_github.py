from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


OUTPUT_DIR = Path("research_data/optical_multilayer_thin_film")
OUTPUT_JSONL = OUTPUT_DIR / "github_repositories.jsonl"
OUTPUT_MANIFEST = OUTPUT_DIR / "github_manifest.json"
SEARCH_URL = "https://api.github.com/search/repositories"

QUERIES: dict[str, str] = {
    "inverse_design": '"multilayer thin film" "inverse design" in:readme language:Python',
    "tmm_jax": '"transfer matrix method" JAX in:readme language:Python',
    "tmm_pytorch": '"transfer matrix method" PyTorch in:readme language:Python',
    "differentiable_thin_film": 'differentiable "thin film" in:readme language:Python',
    "ellipsometry_ml": 'ellipsometry "deep learning" in:readme language:Python',
    "reflectometry_optical_constants": 'reflectometry "optical constants" in:readme language:Python',
}


def request_page(
    session: requests.Session,
    query: str,
    page: int,
) -> dict[str, Any]:
    response = session.get(
        SEARCH_URL,
        params={
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": 100,
            "page": page,
        },
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"GitHub Search API failed: status={response.status_code}, body={response.text[:500]}"
        )
    return response.json()


def serialize_repository(item: dict[str, Any], matched_queries: list[str]) -> dict[str, Any]:
    license_info = item.get("license") or {}
    return {
        "full_name": item["full_name"],
        "name": item["name"],
        "owner": item["owner"]["login"],
        "description": item.get("description"),
        "html_url": item["html_url"],
        "clone_url": item.get("clone_url"),
        "homepage": item.get("homepage"),
        "language": item.get("language"),
        "topics": item.get("topics", []),
        "license_spdx_id": license_info.get("spdx_id"),
        "default_branch": item.get("default_branch"),
        "stargazers_count": item.get("stargazers_count", 0),
        "forks_count": item.get("forks_count", 0),
        "open_issues_count": item.get("open_issues_count", 0),
        "archived": item.get("archived", False),
        "disabled": item.get("disabled", False),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "pushed_at": item.get("pushed_at"),
        "matched_queries": sorted(matched_queries),
        "source": "GitHub Repository Search API",
    }


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "KAFKA2306-daily-arXiv-ai-enhanced",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    session = requests.Session()
    session.headers.update(headers)

    repositories: dict[str, dict[str, Any]] = {}
    matches: dict[str, set[str]] = defaultdict(set)
    query_counts: dict[str, int] = {}
    truncated_queries: list[str] = []

    for query_id, query in QUERIES.items():
        print(f"[取得開始] {query_id}: {query}", flush=True)
        count = 0
        page = 1
        total_count = None

        try:
            while True:
                payload = request_page(session, query, page)
                items = payload.get("items", [])
                if total_count is None:
                    total_count = int(payload.get("total_count", 0))
                    if total_count > 1000:
                        truncated_queries.append(query_id)

                if not items:
                    break

                for item in items:
                    full_name = item["full_name"]
                    repositories[full_name] = item
                    matches[full_name].add(query_id)
                    count += 1

                if len(items) < 100 or count >= min(total_count, 1000):
                    break

                page += 1
                time.sleep(2)
        except Exception as exc:
            print(f"[失敗] {query_id}: {exc}", file=sys.stderr)
            return 1

        query_counts[query_id] = count
        print(f"[取得完了] {query_id}: {count}件", flush=True)

    records = [
        serialize_repository(item, list(matches[full_name]))
        for full_name, item in repositories.items()
    ]
    records.sort(
        key=lambda record: (
            record["archived"],
            -(record["stargazers_count"] or 0),
            record["full_name"].lower(),
        )
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temporary_jsonl = OUTPUT_JSONL.with_suffix(".jsonl.tmp")
    temporary_manifest = OUTPUT_MANIFEST.with_suffix(".json.tmp")

    with temporary_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    manifest = {
        "dataset": "optical-multilayer-thin-film-github",
        "language": "ja",
        "status": "complete" if not truncated_queries else "complete_with_github_1000_result_limit",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": SEARCH_URL,
        "collector": "tools/collect_optical_thin_film_github.py",
        "query_count": len(QUERIES),
        "query_result_counts_before_deduplication": query_counts,
        "repository_count_after_full_name_deduplication": len(records),
        "deduplication_key": "full_name",
        "queries_truncated_by_github_search_limit": truncated_queries,
        "queries": QUERIES,
    }
    temporary_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    temporary_jsonl.replace(OUTPUT_JSONL)
    temporary_manifest.replace(OUTPUT_MANIFEST)

    print(f"[完了] 重複除去後 {len(records)}件を {OUTPUT_JSONL} に保存しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


OUTPUT_DIR = Path("research_data/optical_multilayer_thin_film")
OUTPUT_JSONL = OUTPUT_DIR / "jp_literature.jsonl"
OUTPUT_MANIFEST = OUTPUT_DIR / "jp_manifest.json"
SEARCH_URL = "https://ndlsearch.ndl.go.jp/api/opensearch"

# OpenSearchのanyは、半角スペース区切りで複数語のAND検索になる。
# 個々の検索式を狭くしすぎず、取得後にmatched_queriesで由来を保持する。
QUERIES: dict[str, str] = {
    "multilayer_thin_film": "多層薄膜",
    "optical_thin_film": "光学薄膜",
    "inverse_design": "薄膜 逆設計",
    "reflection_thickness": "反射スペクトル 膜厚",
    "optical_constants_thickness": "光学定数 膜厚",
    "spectral_reflectance": "分光反射率 薄膜",
    "transfer_matrix": "転送行列法 薄膜",
    "ellipsometry": "エリプソメトリ 膜厚",
    "in_process_reflectometry": "インプロセス 反射率",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_texts(item: ET.Element) -> dict[str, list[str]]:
    values: dict[str, list[str]] = defaultdict(list)
    for child in item.iter():
        if child is item:
            continue
        text = " ".join("".join(child.itertext()).split())
        name = local_name(child.tag)
        if text and text not in values[name]:
            values[name].append(text)
    return dict(values)


def first(values: dict[str, list[str]], *keys: str) -> str | None:
    for key in keys:
        entries = values.get(key, [])
        if entries:
            return entries[0]
    return None


def fetch_query(session: requests.Session, query: str) -> tuple[int, list[dict[str, Any]]]:
    response = session.get(
        SEARCH_URL,
        params={
            "any": query,
            "cnt": 500,
            "idx": 1,
        },
        timeout=90,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"NDL Search API failed: status={response.status_code}, body={response.text[:500]}"
        )

    root = ET.fromstring(response.content)
    channel = next((element for element in root.iter() if local_name(element.tag) == "channel"), None)
    if channel is None:
        raise RuntimeError("NDL Search API response does not contain channel")

    total_results = 0
    for child in channel:
        if local_name(child.tag) == "totalResults" and child.text:
            total_results = int(child.text)
            break

    records: list[dict[str, Any]] = []
    items = [element for element in channel if local_name(element.tag) == "item"]
    for item in items:
        values = child_texts(item)
        link = first(values, "link")
        guid = first(values, "guid", "identifier")
        record_key = link or guid or first(values, "title")
        records.append(
            {
                "record_key": record_key,
                "title": first(values, "title"),
                "link": link,
                "identifier": guid,
                "creators": values.get("creator", []),
                "publishers": values.get("publisher", []),
                "publication_names": values.get("publicationName", []),
                "publication_date": first(values, "issued", "date", "pubDate"),
                "descriptions": values.get("description", []),
                "subjects": values.get("subject", []),
                "types": values.get("type", []),
                "raw_metadata": values,
                "source": "国立国会図書館サーチ OpenSearch API",
            }
        )

    return total_results, records


def main() -> int:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.1",
            "User-Agent": "KAFKA2306-daily-arXiv-ai-enhanced/1.0",
        }
    )

    records_by_key: dict[str, dict[str, Any]] = {}
    matches: dict[str, set[str]] = defaultdict(set)
    returned_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    truncated_queries: list[str] = []

    for query_id, query in QUERIES.items():
        print(f"[取得開始] {query_id}: {query}", flush=True)
        try:
            total, records = fetch_query(session, query)
        except Exception as exc:
            print(f"[失敗] {query_id}: {exc}", file=sys.stderr)
            return 1

        total_counts[query_id] = total
        returned_counts[query_id] = len(records)
        if total > 500:
            truncated_queries.append(query_id)

        for record in records:
            key = record.get("record_key")
            if not key:
                continue
            records_by_key[key] = record
            matches[key].add(query_id)

        print(f"[取得完了] {query_id}: 全{total}件中{len(records)}件", flush=True)

    records = []
    for key, record in records_by_key.items():
        enriched = dict(record)
        enriched["matched_queries"] = sorted(matches[key])
        records.append(enriched)

    records.sort(
        key=lambda record: (
            record.get("publication_date") or "",
            record.get("title") or "",
        ),
        reverse=True,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temporary_jsonl = OUTPUT_JSONL.with_suffix(".jsonl.tmp")
    temporary_manifest = OUTPUT_MANIFEST.with_suffix(".json.tmp")

    with temporary_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    manifest = {
        "dataset": "optical-multilayer-thin-film-japanese-literature",
        "language": "ja",
        "status": "complete" if not truncated_queries else "complete_with_ndl_500_result_limit",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": SEARCH_URL,
        "collector": "tools/collect_optical_thin_film_jp.py",
        "query_count": len(QUERIES),
        "query_total_results": total_counts,
        "query_returned_results": returned_counts,
        "record_count_after_record_key_deduplication": len(records),
        "deduplication_key": "link_or_identifier_or_title",
        "queries_truncated_by_ndl_500_result_limit": truncated_queries,
        "queries": QUERIES,
        "credit_ja": "メタデータ提供元：国立国会図書館サーチ",
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

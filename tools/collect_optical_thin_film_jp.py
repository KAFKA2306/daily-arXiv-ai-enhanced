from __future__ import annotations

import json
import sys
import time
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
PAGE_SIZE = 500
MIN_PUBLICATION_YEAR = 1800
MAX_PUBLICATION_YEAR = datetime.now(timezone.utc).year + 1

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


def parse_response(content: bytes) -> tuple[int, list[dict[str, Any]]]:
    root = ET.fromstring(content)
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


def fetch_window(
    session: requests.Session,
    query: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    params: dict[str, Any] = {
        "any": query,
        "cnt": PAGE_SIZE,
        "idx": 1,
    }
    if start_year is not None and end_year is not None:
        params["from"] = f"{start_year:04d}-01-01"
        params["until"] = f"{end_year:04d}-12-31"

    response = session.get(SEARCH_URL, params=params, timeout=90)
    if response.status_code != 200:
        raise RuntimeError(
            f"NDL Search API failed: status={response.status_code}, body={response.text[:500]}"
        )
    return parse_response(response.content)


def collect_year_range(
    session: requests.Session,
    query: str,
    start_year: int,
    end_year: int,
) -> tuple[dict[str, dict[str, Any]], list[tuple[int, int, int]]]:
    total, records = fetch_window(session, query, start_year, end_year)
    print(f"[期間監査] {start_year}-{end_year}: {total}件", flush=True)
    time.sleep(0.5)

    if total <= PAGE_SIZE:
        return {
            record["record_key"]: record
            for record in records
            if record.get("record_key")
        }, []

    if start_year >= end_year:
        return {
            record["record_key"]: record
            for record in records
            if record.get("record_key")
        }, [(start_year, end_year, total)]

    middle_year = (start_year + end_year) // 2
    left_records, left_incomplete = collect_year_range(
        session,
        query,
        start_year,
        middle_year,
    )
    right_records, right_incomplete = collect_year_range(
        session,
        query,
        middle_year + 1,
        end_year,
    )
    left_records.update(right_records)
    return left_records, left_incomplete + right_incomplete


def fetch_query(
    session: requests.Session,
    query: str,
) -> tuple[int, list[dict[str, Any]], list[tuple[int, int, int]]]:
    total_results, first_records = fetch_window(session, query)
    records_by_key = {
        record["record_key"]: record
        for record in first_records
        if record.get("record_key")
    }

    if total_results <= PAGE_SIZE:
        return total_results, list(records_by_key.values()), []

    dated_records, unsplittable_ranges = collect_year_range(
        session,
        query,
        MIN_PUBLICATION_YEAR,
        MAX_PUBLICATION_YEAR,
    )
    records_by_key.update(dated_records)
    return total_results, list(records_by_key.values()), unsplittable_ranges


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
    incomplete_queries: list[str] = []
    unsplittable_ranges: dict[str, list[tuple[int, int, int]]] = {}

    for query_id, query in QUERIES.items():
        print(f"[取得開始] {query_id}: {query}", flush=True)
        try:
            total, records, query_unsplittable = fetch_query(session, query)
        except Exception as exc:
            print(f"[失敗] {query_id}: {exc}", file=sys.stderr)
            return 1

        unique_query_records = {
            record["record_key"]: record
            for record in records
            if record.get("record_key")
        }
        total_counts[query_id] = total
        returned_counts[query_id] = len(unique_query_records)
        if len(unique_query_records) < total or query_unsplittable:
            incomplete_queries.append(query_id)
        if query_unsplittable:
            unsplittable_ranges[query_id] = query_unsplittable

        for key, record in unique_query_records.items():
            records_by_key[key] = record
            matches[key].add(query_id)

        print(
            f"[取得完了] {query_id}: 全{total}件中{len(unique_query_records)}件を一意取得",
            flush=True,
        )

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
        "status": "complete" if not incomplete_queries else "incomplete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": SEARCH_URL,
        "collector": "tools/collect_optical_thin_film_jp.py",
        "api_result_limit": PAGE_SIZE,
        "partition_method": "recursive_publication_year_ranges",
        "publication_year_range": [MIN_PUBLICATION_YEAR, MAX_PUBLICATION_YEAR],
        "query_count": len(QUERIES),
        "query_total_results": total_counts,
        "query_returned_unique_results": returned_counts,
        "record_count_after_record_key_deduplication": len(records),
        "deduplication_key": "link_or_identifier_or_title",
        "incomplete_queries": incomplete_queries,
        "unsplittable_ranges": unsplittable_ranges,
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

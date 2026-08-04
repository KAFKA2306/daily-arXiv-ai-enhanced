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
SEARCH_URL = "https://ndlsearch.ndl.go.jp/api/sru"
PAGE_SIZE = 500
CURRENT_YEAR = datetime.now(timezone.utc).year
INITIAL_YEAR_RANGES = [
    (1800, 1949),
    (1950, 1999),
    (2000, 2009),
    (2010, 2019),
    (2020, CURRENT_YEAR + 1),
]

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


def escape_cql(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def values_by_local_name(root: ET.Element, name: str) -> list[str]:
    values: list[str] = []
    for node in root.iter():
        if local_name(node.tag) != name:
            continue
        text = " ".join("".join(node.itertext()).split())
        if text and text not in values:
            values.append(text)
    return values


def first(values: list[str]) -> str | None:
    return values[0] if values else None


def parse_record_data(record_data: ET.Element) -> ET.Element:
    children = list(record_data)
    if children:
        return children[0]

    escaped_xml = (record_data.text or "").strip()
    if escaped_xml:
        try:
            return ET.fromstring(escaped_xml)
        except ET.ParseError:
            pass

    return record_data


def parse_sru_response(content: bytes) -> tuple[int, list[dict[str, Any]]]:
    root = ET.fromstring(content)
    total_text = first(values_by_local_name(root, "numberOfRecords"))
    total = int(total_text) if total_text else 0

    diagnostics = values_by_local_name(root, "message")
    if diagnostics and total == 0:
        normalized = " ".join(diagnostics).casefold()
        if "record does not exist" in normalized:
            return 0, []
        raise RuntimeError(f"NDL SRU diagnostic: {'; '.join(diagnostics)}")

    records: list[dict[str, Any]] = []
    for record in (node for node in root.iter() if local_name(node.tag) == "record"):
        record_data = next(
            (node for node in record if local_name(node.tag) == "recordData"),
            None,
        )
        if record_data is None:
            continue

        metadata = parse_record_data(record_data)
        record_identifiers = [
            " ".join("".join(node.itertext()).split())
            for node in record
            if local_name(node.tag) == "recordIdentifier"
        ]
        identifiers = values_by_local_name(metadata, "identifier")
        titles = values_by_local_name(metadata, "title")
        creators = values_by_local_name(metadata, "creator")
        dates = values_by_local_name(metadata, "date") + values_by_local_name(metadata, "issued")
        publishers = values_by_local_name(metadata, "publisher")
        descriptions = values_by_local_name(metadata, "description")
        subjects = values_by_local_name(metadata, "subject")
        types = values_by_local_name(metadata, "type")
        languages = values_by_local_name(metadata, "language")

        record_key = (
            first(record_identifiers)
            or first(identifiers)
            or " | ".join(
                part
                for part in [first(titles), first(creators), first(dates)]
                if part
            )
        )
        if not record_key:
            continue

        link = next(
            (value for value in identifiers if value.startswith(("http://", "https://"))),
            None,
        )
        records.append(
            {
                "record_key": record_key,
                "title": first(titles),
                "link": link,
                "identifiers": identifiers,
                "creators": creators,
                "publishers": publishers,
                "publication_date": first(dates),
                "descriptions": descriptions,
                "subjects": subjects,
                "types": types,
                "languages": languages,
                "source": "国立国会図書館サーチ SRU API",
            }
        )

    return total, records


def build_cql(query: str, start_year: int | None = None, end_year: int | None = None) -> str:
    clauses = [f'anywhere all "{escape_cql(query)}"']
    if start_year is not None and end_year is not None:
        clauses.extend([f'from="{start_year}"', f'until="{end_year}"'])
    return " AND ".join(clauses)


def fetch_window(
    session: requests.Session,
    query: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    response = session.get(
        SEARCH_URL,
        params={
            "operation": "searchRetrieve",
            "version": "1.2",
            "recordSchema": "dc",
            "maximumRecords": PAGE_SIZE,
            "startRecord": 1,
            "query": build_cql(query, start_year, end_year),
        },
        timeout=90,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"NDL SRU API failed: status={response.status_code}, body={response.text[:500]}"
        )
    return parse_sru_response(response.content)


def collect_range(
    session: requests.Session,
    query: str,
    start_year: int,
    end_year: int,
) -> tuple[dict[str, dict[str, Any]], list[tuple[int, int, int]]]:
    total, records = fetch_window(session, query, start_year, end_year)
    print(f"[期間取得] {start_year}-{end_year}: {len(records)}/{total}件", flush=True)
    time.sleep(0.5)

    records_by_key = {
        record["record_key"]: record
        for record in records
        if record.get("record_key")
    }
    if total <= PAGE_SIZE:
        return records_by_key, []

    if start_year >= end_year:
        return records_by_key, [(start_year, end_year, total)]

    midpoint = (start_year + end_year) // 2
    left_records, left_incomplete = collect_range(session, query, start_year, midpoint)
    right_records, right_incomplete = collect_range(session, query, midpoint + 1, end_year)
    left_records.update(right_records)
    return left_records, left_incomplete + right_incomplete


def fetch_query(
    session: requests.Session,
    query: str,
) -> tuple[int, list[dict[str, Any]], list[tuple[int, int, int]]]:
    total, first_records = fetch_window(session, query)
    records_by_key = {
        record["record_key"]: record
        for record in first_records
        if record.get("record_key")
    }
    if total <= PAGE_SIZE:
        return total, list(records_by_key.values()), []

    incomplete_ranges: list[tuple[int, int, int]] = []
    for start_year, end_year in INITIAL_YEAR_RANGES:
        range_records, range_incomplete = collect_range(
            session,
            query,
            start_year,
            end_year,
        )
        records_by_key.update(range_records)
        incomplete_ranges.extend(range_incomplete)

    return total, list(records_by_key.values()), incomplete_ranges


def main() -> int:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/xml",
            "User-Agent": "KAFKA2306-daily-arXiv-ai-enhanced/1.0",
        }
    )

    records_by_key: dict[str, dict[str, Any]] = {}
    matches: dict[str, set[str]] = defaultdict(set)
    unique_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    incomplete_queries: list[str] = []
    incomplete_ranges: dict[str, list[tuple[int, int, int]]] = {}

    for query_id, query in QUERIES.items():
        print(f"[取得開始] {query_id}: {query}", flush=True)
        try:
            total, records, query_incomplete_ranges = fetch_query(session, query)
        except Exception as exc:
            print(f"[失敗] {query_id}: {exc}", file=sys.stderr)
            return 1

        unique_query_records = {
            record["record_key"]: record
            for record in records
            if record.get("record_key")
        }
        total_counts[query_id] = total
        unique_counts[query_id] = len(unique_query_records)
        if len(unique_query_records) < total or query_incomplete_ranges:
            incomplete_queries.append(query_id)
        if query_incomplete_ranges:
            incomplete_ranges[query_id] = query_incomplete_ranges

        for key, record in unique_query_records.items():
            records_by_key[key] = record
            matches[key].add(query_id)

        print(
            f"[取得完了] {query_id}: API全{total}件、一意取得{len(unique_query_records)}件",
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
        "collection_method": "first_500_plus_publication_year_partitions",
        "initial_year_ranges": INITIAL_YEAR_RANGES,
        "query_count": len(QUERIES),
        "query_total_results": total_counts,
        "query_unique_results": unique_counts,
        "record_count_after_record_key_deduplication": len(records),
        "deduplication_key": "sru_record_identifier_or_metadata_fingerprint",
        "incomplete_queries": incomplete_queries,
        "incomplete_ranges": incomplete_ranges,
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

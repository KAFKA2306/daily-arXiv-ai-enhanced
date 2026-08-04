from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


OUTPUT_DIR = Path("research_data/optical_multilayer_thin_film")
OUTPUT_UNIQUE_JSONL = OUTPUT_DIR / "jp_literature.jsonl"
OUTPUT_OCCURRENCES_JSONL = OUTPUT_DIR / "jp_query_records.jsonl"
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
        metadata_bytes = ET.tostring(metadata, encoding="utf-8")
        metadata_sha256 = hashlib.sha256(metadata_bytes).hexdigest()
        record_identifiers = [
            " ".join("".join(node.itertext()).split())
            for node in record
            if local_name(node.tag) == "recordIdentifier"
        ]
        position_text = first(
            [
                " ".join("".join(node.itertext()).split())
                for node in record
                if local_name(node.tag) == "recordPosition"
            ]
        )
        if not position_text:
            continue

        identifiers = values_by_local_name(metadata, "identifier")
        titles = values_by_local_name(metadata, "title")
        creators = values_by_local_name(metadata, "creator")
        dates = values_by_local_name(metadata, "date") + values_by_local_name(metadata, "issued")
        publishers = values_by_local_name(metadata, "publisher")
        descriptions = values_by_local_name(metadata, "description")
        subjects = values_by_local_name(metadata, "subject")
        types = values_by_local_name(metadata, "type")
        languages = values_by_local_name(metadata, "language")
        link = next(
            (value for value in identifiers if value.startswith(("http://", "https://"))),
            None,
        )

        records.append(
            {
                "record_position": int(position_text),
                "record_key": f"sha256:{metadata_sha256}",
                "record_identifier": first(record_identifiers),
                "metadata_sha256": metadata_sha256,
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


def annotate_partition(
    records: list[dict[str, Any]],
    partition_id: str,
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        item["partition_id"] = partition_id
        annotated.append(item)
    return annotated


def collect_range(
    session: requests.Session,
    query: str,
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], list[tuple[int, int, int]]]:
    total, records = fetch_window(session, query, start_year, end_year)
    partition_id = f"year:{start_year}-{end_year}"
    print(f"[期間取得] {partition_id}: {len(records)}/{total}件", flush=True)
    time.sleep(0.5)

    if total <= PAGE_SIZE:
        return annotate_partition(records, partition_id), []

    if start_year >= end_year:
        return annotate_partition(records, partition_id), [(start_year, end_year, total)]

    midpoint = (start_year + end_year) // 2
    left_records, left_incomplete = collect_range(session, query, start_year, midpoint)
    right_records, right_incomplete = collect_range(session, query, midpoint + 1, end_year)
    return left_records + right_records, left_incomplete + right_incomplete


def has_partitioned_year(value: str | None) -> bool:
    if not value:
        return False
    for match in re.findall(r"(?<!\d)(\d{4})(?!\d)", value):
        year = int(match)
        if 1800 <= year <= CURRENT_YEAR + 1:
            return True
    return False


def fetch_query(
    session: requests.Session,
    query: str,
) -> tuple[int, list[dict[str, Any]], list[tuple[int, int, int]]]:
    total, first_records = fetch_window(session, query)
    if total <= PAGE_SIZE:
        return total, annotate_partition(first_records, "global"), []

    dated_records: list[dict[str, Any]] = []
    incomplete_ranges: list[tuple[int, int, int]] = []
    for start_year, end_year in INITIAL_YEAR_RANGES:
        range_records, range_incomplete = collect_range(
            session,
            query,
            start_year,
            end_year,
        )
        dated_records.extend(range_records)
        incomplete_ranges.extend(range_incomplete)

    missing_count = total - len(dated_records)
    undated_candidates = [
        record for record in first_records if not has_partitioned_year(record.get("publication_date"))
    ]
    print(
        f"[日付なし監査] 必要{missing_count}件、先頭500件内候補{len(undated_candidates)}件",
        flush=True,
    )
    undated_records = annotate_partition(undated_candidates[: max(missing_count, 0)], "undated")
    return total, dated_records + undated_records, incomplete_ranges


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    temporary_path.replace(path)


def main() -> int:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/xml",
            "User-Agent": "KAFKA2306-daily-arXiv-ai-enhanced/1.0",
        }
    )

    occurrences: list[dict[str, Any]] = []
    unique_records: dict[str, dict[str, Any]] = {}
    matched_queries: dict[str, set[str]] = defaultdict(set)
    total_counts: dict[str, int] = {}
    returned_counts: dict[str, int] = {}
    incomplete_queries: list[str] = []
    incomplete_ranges: dict[str, list[tuple[int, int, int]]] = {}

    for query_id, query in QUERIES.items():
        print(f"[取得開始] {query_id}: {query}", flush=True)
        try:
            total, records, query_incomplete_ranges = fetch_query(session, query)
        except Exception as exc:
            print(f"[失敗] {query_id}: {exc}", file=sys.stderr)
            return 1

        total_counts[query_id] = total
        returned_counts[query_id] = len(records)
        if len(records) != total or query_incomplete_ranges:
            incomplete_queries.append(query_id)
        if query_incomplete_ranges:
            incomplete_ranges[query_id] = query_incomplete_ranges

        for record in records:
            occurrence = dict(record)
            occurrence["occurrence_key"] = (
                f"{query_id}:{record['partition_id']}:{record['record_position']}"
            )
            occurrence["source_query_id"] = query_id
            occurrence["source_query"] = query
            occurrences.append(occurrence)

            record_key = record["record_key"]
            normalized = dict(record)
            normalized.pop("partition_id", None)
            normalized.pop("record_position", None)
            unique_records[record_key] = normalized
            matched_queries[record_key].add(query_id)

        print(
            f"[取得完了] {query_id}: API全{total}件、区間分割取得{len(records)}件",
            flush=True,
        )

    normalized_records: list[dict[str, Any]] = []
    for record_key, record in unique_records.items():
        normalized = dict(record)
        normalized["matched_queries"] = sorted(matched_queries[record_key])
        normalized_records.append(normalized)

    occurrences.sort(key=lambda record: record["occurrence_key"])
    normalized_records.sort(
        key=lambda record: (
            record.get("publication_date") or "",
            record.get("title") or "",
        ),
        reverse=True,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT_OCCURRENCES_JSONL, occurrences)
    write_jsonl(OUTPUT_UNIQUE_JSONL, normalized_records)

    manifest = {
        "dataset": "optical-multilayer-thin-film-japanese-literature",
        "language": "ja",
        "status": "complete" if not incomplete_queries else "incomplete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": SEARCH_URL,
        "collector": "tools/collect_optical_thin_film_jp.py",
        "api_result_limit": PAGE_SIZE,
        "collection_method": "disjoint_publication_year_partitions_plus_undated_from_first_500",
        "initial_year_ranges": INITIAL_YEAR_RANGES,
        "query_count": len(QUERIES),
        "query_total_results": total_counts,
        "query_returned_results": returned_counts,
        "query_occurrence_count": len(occurrences),
        "record_count_after_record_key_deduplication": len(normalized_records),
        "occurrence_key": "source_query_id_partition_id_record_position",
        "deduplication_key": "metadata_xml_sha256",
        "incomplete_queries": incomplete_queries,
        "incomplete_ranges": incomplete_ranges,
        "queries": QUERIES,
        "credit_ja": "メタデータ提供元：国立国会図書館サーチ",
    }
    temporary_manifest = OUTPUT_MANIFEST.with_suffix(".json.tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(OUTPUT_MANIFEST)

    print(
        f"[完了] 検索結果{len(occurrences)}件、一意文献{len(normalized_records)}件を保存しました。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

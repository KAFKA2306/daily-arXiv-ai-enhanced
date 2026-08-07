#!/usr/bin/env python3
"""Build deterministic JSON/CSV/facet distributions from archived arXiv JSONL."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "kafka2306.arxiv-catalog.v1"
SOURCE_NAME = "arXiv"
SOURCE_DOCS = "https://info.arxiv.org/help/api/user-manual.html"
SOURCE_TERMS = "https://info.arxiv.org/help/api/tou.html"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_records(data_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    files = sorted(data_dir.glob("*.jsonl"))
    if not files:
        raise ValueError(f"no JSONL datasets found in {data_dir}")

    by_id: dict[str, dict[str, Any]] = {}
    occurrences = 0
    duplicate_occurrences = 0
    source_hashes: list[dict[str, Any]] = []

    for path in files:
        raw = path.read_bytes()
        file_count = 0
        for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"].strip():
                raise ValueError(f"{path}:{line_no}: record requires non-empty string id")
            occurrences += 1
            file_count += 1
            paper_id = record["id"].strip()
            previous = by_id.get(paper_id)
            if previous is not None:
                duplicate_occurrences += 1
                old_key = str(previous.get("extraction_date") or "")
                new_key = str(record.get("extraction_date") or "")
                if new_key < old_key:
                    continue
            by_id[paper_id] = record
        source_hashes.append({"path": path.as_posix(), "records": file_count, "sha256": _sha256(raw)})

    records = sorted(by_id.values(), key=lambda r: (str(r.get("published") or ""), str(r["id"])), reverse=True)
    published = [str(r.get("published")) for r in records if r.get("published")]
    extraction = [str(r.get("extraction_date")) for r in records if r.get("extraction_date")]
    stats = {
        "source_files": len(files),
        "source_occurrences": occurrences,
        "unique_papers": len(records),
        "duplicate_occurrences": duplicate_occurrences,
        "published_min": min(published) if published else None,
        "published_max": max(published) if published else None,
        "latest_extraction_date": max(extraction) if extraction else None,
        "source_files_manifest": source_hashes,
    }
    return records, stats


def build_facets(records: list[dict[str, Any]]) -> dict[str, Any]:
    primary = Counter()
    categories = Counter()
    years = Counter()
    dates = Counter()
    for record in records:
        if record.get("primary_category"):
            primary[str(record["primary_category"])] += 1
        for category in record.get("categories") or []:
            categories[str(category)] += 1
        published = str(record.get("published") or "")
        if len(published) >= 10:
            dates[published[:10]] += 1
            years[published[:4]] += 1

    def rows(counter: Counter[str]) -> list[dict[str, Any]]:
        return [{"value": key, "count": counter[key]} for key in sorted(counter)]

    return {
        "schema": SCHEMA + ".facets",
        "primary_category": rows(primary),
        "category": rows(categories),
        "published_year": rows(years),
        "published_date": rows(dates),
    }


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = ["id", "title", "authors", "primary_category", "categories", "published", "extraction_date", "arxiv_url", "pdf_url", "doi", "journal_ref", "comment"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["authors"] = "|".join(str(x) for x in (record.get("authors") or []))
            row["categories"] = "|".join(str(x) for x in (record.get("categories") or []))
            writer.writerow({key: "" if row.get(key) is None else row.get(key, "") for key in fields})


def build(data_dir: Path, output_dir: Path) -> dict[str, Any]:
    records, stats = load_records(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    papers_path = output_dir / "papers.json"
    facets_path = output_dir / "facets.json"
    csv_path = output_dir / "papers.csv"

    papers_path.write_bytes(_json_bytes({"schema": SCHEMA, "papers": records}))
    facets_path.write_bytes(_json_bytes(build_facets(records)))
    write_csv(csv_path, records)

    files: dict[str, dict[str, Any]] = {}
    for path in (papers_path, facets_path, csv_path):
        data = path.read_bytes()
        files[path.name] = {"bytes": len(data), "sha256": _sha256(data)}

    manifest = {
        "schema": SCHEMA + ".manifest",
        "version": 1,
        "source": {"name": SOURCE_NAME, "api_manual": SOURCE_DOCS, "terms_of_use": SOURCE_TERMS},
        "generated_from": stats["latest_extraction_date"],
        "stats": {key: value for key, value in stats.items() if key != "source_files_manifest"},
        "source_files": stats["source_files_manifest"],
        "files": files,
        "cache": {"max_age_seconds": 3600, "validation": "sha256"},
    }
    (output_dir / "manifest.json").write_bytes(_json_bytes(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("build/api/v1"))
    args = parser.parse_args()
    manifest = build(args.data_dir, args.output_dir)
    print(json.dumps(manifest["stats"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

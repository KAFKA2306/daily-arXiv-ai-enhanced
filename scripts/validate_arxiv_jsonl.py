#!/usr/bin/env python3
"""Validate published arXiv JSONL datasets without third-party dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ARXIV_ID = re.compile(r"^(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?$", re.IGNORECASE)
REQUIRED = ("id", "pdf", "abs", "authors", "title", "categories", "summary")


def _is_http_url(value: Any, *, host: str | None = None) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return host is None or parsed.netloc.lower() == host


def validate_record(record: Any, *, path: str, line: int) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    def add(code: str, message: str) -> None:
        errors.append({"path": path, "line": line, "code": code, "message": message})

    if not isinstance(record, dict):
        add("record_type", "record must be a JSON object")
        return errors

    missing = [key for key in REQUIRED if key not in record]
    if missing:
        add("missing_fields", f"missing required fields: {', '.join(missing)}")

    arxiv_id = record.get("id")
    if not isinstance(arxiv_id, str) or not ARXIV_ID.fullmatch(arxiv_id):
        add("invalid_id", "id must be a valid arXiv identifier")

    for field, suffix in (("abs", "/abs/"), ("pdf", "/pdf/")):
        value = record.get(field)
        if not _is_http_url(value, host="arxiv.org") or suffix not in value:
            add(f"invalid_{field}_url", f"{field} must be an arxiv.org {suffix.strip('/')} URL")
        elif isinstance(arxiv_id, str) and arxiv_id not in value:
            add(f"{field}_id_mismatch", f"{field} URL must contain the record id")

    for field in ("title", "summary"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            add(f"invalid_{field}", f"{field} must be a non-empty string")

    for field in ("authors", "categories"):
        value = record.get(field)
        if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
            add(f"invalid_{field}", f"{field} must be a non-empty array of non-empty strings")

    comment = record.get("comment")
    if comment is not None and not isinstance(comment, str):
        add("invalid_comment", "comment must be a string or null")

    return errors


def validate_files(paths: list[Path]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    ids: list[tuple[str, str, int]] = []
    record_count = 0

    for path in sorted(paths):
        digest = hashlib.sha256()
        file_records = 0
        try:
            with path.open("rb") as raw:
                for raw_line in raw:
                    digest.update(raw_line)
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    file_records += 1
                    record_count += 1
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append({"path": str(path), "line": line_number, "code": "invalid_json", "message": str(exc)})
                        continue
                    errors.extend(validate_record(record, path=str(path), line=line_number))
                    if isinstance(record, dict) and isinstance(record.get("id"), str):
                        ids.append((record["id"], str(path), line_number))
        except OSError as exc:
            errors.append({"path": str(path), "line": 0, "code": "read_error", "message": str(exc)})
            continue
        files.append({"path": str(path), "sha256": digest.hexdigest(), "records": file_records})

    counts = Counter(identifier for identifier, _, _ in ids)
    for identifier, path, line in ids:
        if counts[identifier] > 1:
            errors.append({"path": path, "line": line, "code": "duplicate_id", "message": f"arXiv id {identifier} appears {counts[identifier]} times in the selected dataset"})

    return {
        "schema_version": "kafka.arxiv-data-audit.v1",
        "files": files,
        "file_count": len(files),
        "record_count": record_count,
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    missing = [str(path) for path in args.paths if not path.is_file()]
    if missing:
        parser.error(f"not files: {', '.join(missing)}")

    result = validate_files(args.paths)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if result["error_count"] else 0


if __name__ == "__main__":
    sys.exit(main())

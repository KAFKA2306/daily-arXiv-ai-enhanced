from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_arxiv_jsonl import validate_files, validate_record


VALID = {
    "id": "2503.11731",
    "pdf": "https://arxiv.org/pdf/2503.11731",
    "abs": "https://arxiv.org/abs/2503.11731",
    "authors": ["Example Author"],
    "title": "Example paper",
    "categories": ["cs.AI"],
    "comment": None,
    "summary": "An example abstract.",
}


class ValidateArxivJsonlTests(unittest.TestCase):
    def test_valid_record(self) -> None:
        self.assertEqual(validate_record(VALID, path="fixture.jsonl", line=1), [])

    def test_url_id_mismatch_is_rejected(self) -> None:
        record = dict(VALID, pdf="https://arxiv.org/pdf/2503.99999")
        codes = {error["code"] for error in validate_record(record, path="fixture.jsonl", line=1)}
        self.assertIn("pdf_id_mismatch", codes)

    def test_duplicate_ids_across_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "a.jsonl"
            second = root / "b.jsonl"
            payload = json.dumps(VALID) + "\n"
            first.write_text(payload, encoding="utf-8")
            second.write_text(payload, encoding="utf-8")
            result = validate_files([first, second])
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(sum(error["code"] == "duplicate_id" for error in result["errors"]), 2)
        self.assertEqual(len(result["files"][0]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

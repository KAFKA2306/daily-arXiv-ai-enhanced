from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_arxiv_catalog import build


class BuildArxivCatalogTests(unittest.TestCase):
    def test_deduplicates_and_builds_manifest_and_facets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            out = root / "out"
            data.mkdir()
            first = {
                "id": "2501.00001v1",
                "title": "A",
                "authors": ["Alice"],
                "categories": ["cs.AI", "cs.LG"],
                "primary_category": "cs.AI",
                "published": "2025-01-01T00:00:00+00:00",
                "extraction_date": "2025-01-01T01:00:00+00:00",
                "arxiv_url": "https://arxiv.org/abs/2501.00001v1",
                "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
            }
            newer = dict(first, title="A revised metadata", extraction_date="2025-01-02T01:00:00+00:00")
            second = dict(first, id="2501.00002v1", title="B", primary_category="cs.LG", categories=["cs.LG"], published="2025-01-02T00:00:00+00:00", extraction_date="2025-01-02T02:00:00+00:00")
            (data / "2025-01-01.jsonl").write_text(json.dumps(first) + "\n", encoding="utf-8")
            (data / "2025-01-02.jsonl").write_text("\n".join(json.dumps(x) for x in (newer, second)) + "\n", encoding="utf-8")

            manifest = build(data, out)
            self.assertEqual(manifest["stats"]["source_occurrences"], 3)
            self.assertEqual(manifest["stats"]["unique_papers"], 2)
            self.assertEqual(manifest["stats"]["duplicate_occurrences"], 1)
            papers = json.loads((out / "papers.json").read_text(encoding="utf-8"))["papers"]
            self.assertEqual(next(x for x in papers if x["id"] == first["id"])["title"], "A revised metadata")
            facets = json.loads((out / "facets.json").read_text(encoding="utf-8"))
            self.assertIn({"value": "cs.LG", "count": 2}, facets["category"])
            raw = (out / "papers.json").read_bytes()
            self.assertEqual(manifest["files"]["papers.json"]["sha256"], hashlib.sha256(raw).hexdigest())

    def test_same_input_produces_same_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            record = {"id": "2501.00001v1", "title": "A", "authors": [], "categories": ["cs.AI"], "primary_category": "cs.AI", "published": "2025-01-01T00:00:00+00:00", "extraction_date": "2025-01-01T01:00:00+00:00"}
            (data / "2025-01-01.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            out1, out2 = root / "one", root / "two"
            build(data, out1)
            build(data, out2)
            for name in ("papers.json", "papers.csv", "facets.json", "manifest.json"):
                self.assertEqual((out1 / name).read_bytes(), (out2 / name).read_bytes())

    def test_rejects_record_without_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            (data / "bad.jsonl").write_text('{"title":"missing id"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requires non-empty string id"):
                build(data, root / "out")


if __name__ == "__main__":
    unittest.main()

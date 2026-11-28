import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]


class ConvertTest(unittest.TestCase):
    def test_writes_table_of_contents_and_category_link(self):
        with tempfile.TemporaryDirectory(prefix="arxivconvert") as temporary_directory:
            workdir = Path(temporary_directory)
            shutil.copy(REPOSITORY / "to_md" / "paper_template.md", workdir)
            data_path = workdir / "papers.jsonl"
            paper = {
                "title": "Example paper",
                "authors": ["A. Author"],
                "summary": "Example abstract",
                "abs": "https://arxiv.org/abs/0000.00000",
                "categories": ["cs.TEST"],
                "AI": {
                    "tldr": "Short summary",
                    "motivation": "Motivation",
                    "method": "Method",
                    "result": "Result",
                    "conclusion": "Conclusion",
                },
            }
            data_path.write_text(json.dumps(paper) + "\n", encoding="utf-8")

            subprocess.run(
                [sys.executable, str(REPOSITORY / "to_md" / "convert.py"), "--data", str(data_path)],
                cwd=workdir,
                check=True,
                capture_output=True,
                text=True,
            )

            markdown = (workdir / "papers.jsonl.md").read_text(encoding="utf-8")
            self.assertIn("# Table of Contents", markdown)
            self.assertIn("[cs.TEST](#cs.TEST)", markdown)


if __name__ == "__main__":
    unittest.main()
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import arxiv


OUTPUT_DIR = Path("research_data/optical_multilayer_thin_film")
OUTPUT_JSONL = OUTPUT_DIR / "arxiv_papers.jsonl"
OUTPUT_MANIFEST = OUTPUT_DIR / "manifest.json"

QUERIES: dict[str, str] = {
    "inverse_design": 'all:"multilayer thin film" AND all:"inverse design"',
    "differentiable_tmm": '(all:"transfer matrix method" OR all:TMM) AND (all:differentiable OR all:"automatic differentiation") AND (all:"thin film" OR all:"optical multilayer")',
    "tandem_network": 'all:"thin film" AND (all:"tandem neural network" OR all:"forward model") AND (all:optical OR all:spectrum)',
    "generative_model": 'all:"optical multilayer" AND (all:"diffusion model" OR all:"flow matching" OR all:autoregressive)',
    "ellipsometry": 'all:ellipsometry AND (all:"inverse problem" OR all:reconstruction) AND (all:"deep learning" OR all:transformer OR all:"flow matching")',
    "reflectometry": 'all:reflectometry AND (all:"refractive index" OR all:"optical constants" OR all:thickness) AND (all:optical OR all:"thin film")',
}


def normalize_base_id(short_id: str) -> str:
    return re.sub(r"v\d+$", "", short_id)


def serialize_result(result: arxiv.Result, matched_queries: list[str]) -> dict[str, Any]:
    short_id = result.get_short_id()
    base_id = normalize_base_id(short_id)
    version_match = re.search(r"v(\d+)$", short_id)
    version = int(version_match.group(1)) if version_match else None

    return {
        "arxiv_id": base_id,
        "arxiv_versioned_id": short_id,
        "version": version,
        "title": " ".join(result.title.split()),
        "authors": [author.name for author in result.authors],
        "summary": " ".join(result.summary.split()),
        "comment": result.comment,
        "journal_reference": result.journal_ref,
        "doi": result.doi,
        "primary_category": result.primary_category,
        "categories": result.categories,
        "published": result.published.astimezone(timezone.utc).isoformat(),
        "updated": result.updated.astimezone(timezone.utc).isoformat(),
        "abstract_url": result.entry_id,
        "pdf_url": result.pdf_url,
        "matched_queries": sorted(matched_queries),
        "source": "arXiv API",
    }


def main() -> int:
    client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=5)
    papers: dict[str, arxiv.Result] = {}
    matches: dict[str, set[str]] = defaultdict(set)
    query_counts: dict[str, int] = {}

    for query_id, query in QUERIES.items():
        print(f"[取得開始] {query_id}: {query}", flush=True)
        search = arxiv.Search(
            query=query,
            max_results=None,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        count = 0
        try:
            for result in client.results(search):
                count += 1
                short_id = result.get_short_id()
                base_id = normalize_base_id(short_id)
                matches[base_id].add(query_id)

                current = papers.get(base_id)
                if current is None or result.updated > current.updated:
                    papers[base_id] = result
        except Exception as exc:
            print(f"[失敗] {query_id}: {exc}", file=sys.stderr)
            return 1

        query_counts[query_id] = count
        print(f"[取得完了] {query_id}: {count}件", flush=True)

    records = [
        serialize_result(result, list(matches[base_id]))
        for base_id, result in papers.items()
    ]
    records.sort(key=lambda record: (record["published"], record["arxiv_id"]), reverse=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temporary_jsonl = OUTPUT_JSONL.with_suffix(".jsonl.tmp")
    temporary_manifest = OUTPUT_MANIFEST.with_suffix(".json.tmp")

    with temporary_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    collected_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "dataset": "optical-multilayer-thin-film-arxiv",
        "language": "ja",
        "status": "complete",
        "collected_at": collected_at,
        "source": "https://export.arxiv.org/api/query",
        "collector": "tools/collect_optical_thin_film_arxiv.py",
        "query_count": len(QUERIES),
        "query_result_counts_before_deduplication": query_counts,
        "paper_count_after_arxiv_id_deduplication": len(records),
        "deduplication_key": "arxiv_id_without_version_suffix",
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

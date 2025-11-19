import os
import re
from typing import Iterable, List, Optional, Set

import arxiv
import scrapy


class ArxivSpider(scrapy.Spider):
    """
    arXiv から人気順（= relevance 優先）で最大 MAX_PAPERS 件を取得するクローラ。
    取得件数や並び順は環境変数で上書きできる。
    """

    name = "arxiv"
    allowed_domains = ["arxiv.org"]

    SORT_MAPPING = {
        "popularity": arxiv.SortCriterion.Relevance,
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted_date": arxiv.SortCriterion.SubmittedDate,
        "last_updated_date": arxiv.SortCriterion.LastUpdatedDate,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = os.environ.get("CATEGORIES", "cs.CV")
        parsed_categories = [c.strip() for c in categories.split(",") if c.strip()]
        self.target_categories: List[str] = parsed_categories or ["cs.CV"]

        self.max_papers = max(1, int(os.environ.get("MAX_PAPERS", "10")))
        sort_key = os.environ.get("SORT_BY", "popularity").strip().lower()
        order_value = os.environ.get("SORT_ORDER", "desc").strip().lower()

        self.sort_criterion = self.SORT_MAPPING.get(sort_key, arxiv.SortCriterion.Relevance)
        self.sort_order = arxiv.SortOrder.Ascending if order_value == "asc" else arxiv.SortOrder.Descending

        self.start_urls = [f"https://arxiv.org/list/{cat}/new" for cat in self.target_categories]

        self.client = arxiv.Client()
        self.seen_ids: Set[str] = set()
        self.yielded = 0

    def parse(self, response):
        if self.yielded >= self.max_papers:
            return

        category = self._extract_category_from_url(response.url)
        if not category:
            self.logger.warning("URL からカテゴリを解読できずスキップ: %s", response.url)
            return

        remaining = self.max_papers - self.yielded
        for paper in self._fetch_ranked_papers(category, remaining):
            arxiv_id = self._normalize_arxiv_id(paper.entry_id)
            if arxiv_id in self.seen_ids:
                continue
            self.seen_ids.add(arxiv_id)

            yield {
                "id": arxiv_id,
                "categories": paper.categories,
            }
            self.yielded += 1

            if self.yielded >= self.max_papers:
                self.logger.info("指定件数 %s 件に到達したため取得を終了します", self.max_papers)
                break

    def _fetch_ranked_papers(self, category: str, limit: int) -> Iterable[arxiv.Result]:
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=max(limit, self.max_papers),
            sort_by=self.sort_criterion,
            sort_order=self.sort_order,
        )
        try:
            for result in self.client.results(search):
                yield result
        except Exception as exc:
            self.logger.error("arXiv API 呼び出しに失敗しました (%s): %s", category, exc)
            return

    @staticmethod
    def _extract_category_from_url(url: str) -> Optional[str]:
        match = re.search(r"/list/([^/]+)/", url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _normalize_arxiv_id(entry_id: str) -> str:
        arxiv_id = entry_id.split("/abs/")[-1]
        return re.sub(r"v\d+$", "", arxiv_id)

import os
import re
from typing import Iterable, List, Optional, Set

import arxiv
import scrapy


class ArxivSpider(scrapy.Spider):
    """arXivから条件に合う論文を最大 ``MAX_PAPERS`` 件取得するクローラー。"""

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
        parsed_categories = [category.strip() for category in categories.split(",") if category.strip()]
        self.target_categories: List[str] = parsed_categories or ["cs.CV"]

        self.custom_query = os.environ.get("ARXIV_QUERY", "").strip() or None
        self.max_papers = max(1, int(os.environ.get("MAX_PAPERS", "10")))

        sort_key = os.environ.get("SORT_BY", "popularity").strip().lower()
        order_value = os.environ.get("SORT_ORDER", "desc").strip().lower()
        self.sort_criterion = self.SORT_MAPPING.get(sort_key, arxiv.SortCriterion.Relevance)
        self.sort_order = (
            arxiv.SortOrder.Ascending if order_value == "asc" else arxiv.SortOrder.Descending
        )

        # Scrapyの開始要求を1件だけ発生させ、実際の検索はarxivパッケージで行う。
        # ARXIV_QUERYが未設定の場合は、従来どおりカテゴリごとに処理する。
        self.start_urls = (
            ["https://arxiv.org/"]
            if self.custom_query
            else [f"https://arxiv.org/list/{category}/new" for category in self.target_categories]
        )

        self.client = arxiv.Client()
        self.seen_ids: Set[str] = set()
        self.yielded = 0

    def parse(self, response):
        if self.yielded >= self.max_papers:
            return

        if self.custom_query:
            yield from self._yield_query_results(self.custom_query)
            return

        category = self._extract_category_from_url(response.url)
        if not category:
            self.logger.warning("URLからカテゴリを解読できずスキップ: %s", response.url)
            return

        yield from self._yield_query_results(f"cat:{category}")

    def _yield_query_results(self, query: str):
        remaining = self.max_papers - self.yielded
        self.logger.info("arXiv検索を実行: %s", query)

        for paper in self._fetch_ranked_papers(query, remaining):
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
                self.logger.info("指定件数%s件に到達したため取得を終了します", self.max_papers)
                break

    def _fetch_ranked_papers(self, query: str, limit: int) -> Iterable[arxiv.Result]:
        search = arxiv.Search(
            query=query,
            max_results=max(limit, self.max_papers),
            sort_by=self.sort_criterion,
            sort_order=self.sort_order,
        )

        try:
            yield from self.client.results(search)
        except Exception as exc:
            self.logger.error("arXiv API呼び出しに失敗しました (%s): %s", query, exc)

    @staticmethod
    def _extract_category_from_url(url: str) -> Optional[str]:
        match = re.search(r"/list/([^/]+)/", url)
        return match.group(1) if match else None

    @staticmethod
    def _normalize_arxiv_id(entry_id: str) -> str:
        arxiv_id = entry_id.split("/abs/")[-1]
        return re.sub(r"v\d+$", "", arxiv_id)

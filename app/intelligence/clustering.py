from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Iterable

from app.database.models import CandidateProject


@dataclass
class BusinessCluster:
    title: str
    market: str
    products: list[CandidateProject] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        if not self.products:
            return 0.0
        return round(mean(float(item.confidence or 0) for item in self.products), 2)

    @property
    def estimated_margin(self) -> float:
        if not self.products:
            return 0.0
        return round(mean(float(item.estimated_margin or 0) for item in self.products), 2)

    @property
    def priority(self) -> int:
        if not self.products:
            return 5
        return max(int(item.priority or 5) for item in self.products)

    @property
    def product_count(self) -> int:
        return len(self.products)

    def product_names(self) -> list[str]:
        return [item.title for item in self.products]


class BusinessClusteringEngine:
    """Groups candidate products into higher-level businesses.

    This is intentionally deterministic for now so the recommendations are
    explainable and testable. LLM-based clustering can plug in later.
    """

    def cluster(self, candidates: Iterable[CandidateProject]) -> list[BusinessCluster]:
        buckets: dict[tuple[str, str], BusinessCluster] = {}

        for candidate in candidates:
            title = candidate.title or "Untitled Product"
            business_title, market = self._classify(title)
            key = (business_title, market)
            if key not in buckets:
                buckets[key] = BusinessCluster(title=business_title, market=market)
            buckets[key].products.append(candidate)

        return sorted(
            buckets.values(),
            key=lambda cluster: (cluster.confidence, cluster.estimated_margin, cluster.product_count),
            reverse=True,
        )

    def _classify(self, title: str) -> tuple[str, str]:
        low = title.lower()
        if any(term in low for term in ["baseball", "lineup", "dugout", "coach", "banner", "senior night"]):
            return "Youth Baseball Coaching Products", "Youth Baseball"
        if any(term in low for term in ["softball"]):
            return "Youth Softball Coaching Products", "Youth Softball"
        if any(term in low for term in ["mom", "team mom", "parent"]):
            return "Youth Sports Parent Gifts", "Youth Sports"
        return "Premium Personalized Products", "Personalized Gifts"

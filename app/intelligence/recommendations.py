from __future__ import annotations

from app.intelligence.clustering import BusinessCluster


class RecommendationEngine:
    """Creates explainable business recommendations from clustered candidates."""

    def recommendation_for_cluster(self, cluster: BusinessCluster) -> dict[str, object]:
        reasons: list[str] = []
        risks: list[str] = []

        if cluster.confidence >= 65:
            reasons.append("strong candidate confidence across the product group")
        elif cluster.confidence >= 55:
            reasons.append("meets the CEO review threshold")
        else:
            risks.append("confidence is below the preferred approval range")

        if cluster.estimated_margin >= 45:
            reasons.append("healthy early margin estimate")
        else:
            risks.append("margin needs Finance Agent validation")

        if cluster.product_count >= 3:
            reasons.append("multiple related products create bundle and brand potential")
        elif cluster.product_count == 2:
            reasons.append("two related products can form a starter product line")
        else:
            risks.append("single-product opportunity until more related products are discovered")

        if cluster.market in {"Youth Baseball", "Youth Softball", "Youth Sports"}:
            reasons.append("clear seasonal buyer segment and repeat team demand")

        if not risks:
            risks.append("supplier cost and fulfillment assumptions still need validation")

        recommended_action = "Approve Business" if cluster.confidence >= 65 and cluster.estimated_margin >= 40 else "Review"
        if cluster.confidence < 55:
            recommended_action = "Park"

        return {
            "recommended_action": recommended_action,
            "reasons": reasons,
            "risks": risks,
            "summary": self.summary(cluster),
        }

    def summary(self, cluster: BusinessCluster) -> str:
        return (
            f"Atlas grouped {cluster.product_count} related product candidate(s) into the "
            f"{cluster.title} business opportunity. Average confidence is "
            f"{cluster.confidence:.1f}% with an early margin estimate of "
            f"{cluster.estimated_margin:.1f}%."
        )

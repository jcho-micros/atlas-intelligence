from __future__ import annotations

from datetime import datetime

from app.database.models import BusinessOpportunity, CandidateProject
from app.intelligence.clustering import BusinessClusteringEngine
from app.intelligence.planner import PlannerEngine
from app.intelligence.recommendations import RecommendationEngine


class BusinessIntelligenceService:
    """Turns product-level candidates into business-level recommendations."""

    def __init__(self, session):
        self.session = session
        self.clustering = BusinessClusteringEngine()
        self.recommendations = RecommendationEngine()
        self.planner = PlannerEngine()

    def refresh_business_opportunities(self) -> list[BusinessOpportunity]:
        candidates = (
            self.session.query(CandidateProject)
            .filter(CandidateProject.status.in_(["candidate", "approved", "parked"]))
            .all()
        )
        clusters = self.clustering.cluster(candidates)
        opportunities: list[BusinessOpportunity] = []

        for cluster in clusters:
            if not cluster.products:
                continue

            recommendation = self.recommendations.recommendation_for_cluster(cluster)
            plan = self.planner.plan_business_launch(cluster.title, cluster.product_names())
            reason = self._format_reason(recommendation, plan)
            summary = recommendation["summary"]
            revenue = self._estimate_revenue(cluster.confidence, cluster.estimated_margin, cluster.product_count)

            existing = (
                self.session.query(BusinessOpportunity)
                .filter_by(title=cluster.title, market=cluster.market, status="candidate")
                .first()
            )

            if existing:
                existing.summary = str(summary)
                existing.confidence = cluster.confidence
                existing.estimated_monthly_revenue = revenue
                existing.estimated_margin = cluster.estimated_margin
                existing.reason = reason
                existing.created_at = existing.created_at or datetime.utcnow()
                opportunity = existing
            else:
                anchor = cluster.products[0]
                opportunity = BusinessOpportunity(
                    candidate_project_id=anchor.id,
                    keyword_id=anchor.keyword_id,
                    title=cluster.title,
                    market=cluster.market,
                    summary=str(summary),
                    confidence=cluster.confidence,
                    estimated_monthly_revenue=revenue,
                    estimated_margin=cluster.estimated_margin,
                    status="candidate",
                    reason=reason,
                    created_at=datetime.utcnow(),
                )
                self.session.add(opportunity)

            opportunities.append(opportunity)

        self.session.commit()
        return opportunities

    def _estimate_revenue(self, confidence: float, margin: float, product_count: int) -> float:
        multiplier = max(1, product_count) * 11.5
        return round(max(3500, confidence * margin * multiplier), 2)

    def _format_reason(self, recommendation: dict[str, object], plan) -> str:
        reasons = recommendation.get("reasons", []) or []
        risks = recommendation.get("risks", []) or []
        tasks = [task.title for task in plan]
        parts = []
        if reasons:
            parts.append("Reasons: " + "; ".join(str(item) for item in reasons))
        if risks:
            parts.append("Risks: " + "; ".join(str(item) for item in risks))
        if tasks:
            parts.append("Planned work: " + "; ".join(tasks[:4]))
        parts.append("Recommended action: " + str(recommendation.get("recommended_action", "Review")))
        return " | ".join(parts)

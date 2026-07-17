from app.database.models import CandidateProject, Keyword, Opportunity


class CandidateProjectService:
    """Creates CEO Inbox candidates from strong marketplace opportunities."""

    def __init__(self, session):
        self.session = session

    def create_from_opportunity(
        self,
        keyword: Keyword,
        opportunity: Opportunity,
        threshold: float = 55,
    ) -> CandidateProject | None:
        if opportunity.score < threshold:
            return None

        existing = (
            self.session.query(CandidateProject)
            .filter_by(keyword_id=keyword.id, status="candidate")
            .first()
        )
        if existing:
            existing.confidence = opportunity.score
            existing.summary = opportunity.notes
            existing.estimated_margin = self._estimate_margin(opportunity)
            existing.priority = self._priority_from_score(opportunity.score)
            existing.reason = self._build_reason(opportunity)
            self.session.commit()
            return existing

        candidate = CandidateProject(
            keyword_id=keyword.id,
            opportunity_id=opportunity.id,
            title=self._build_title(keyword.keyword),
            summary=opportunity.notes,
            confidence=opportunity.score,
            estimated_margin=self._estimate_margin(opportunity),
            priority=self._priority_from_score(opportunity.score),
            reason=self._build_reason(opportunity),
            status="candidate",
        )
        self.session.add(candidate)
        self.session.commit()
        return candidate

    def _build_title(self, keyword: str) -> str:
        lower = keyword.lower()
        if "lineup board" in lower:
            return "Premium Magnetic Baseball Lineup Board"
        if "dugout" in lower:
            return "Personalized Baseball Dugout Sign"
        if "banner" in lower:
            return "Custom Baseball Team Banner"
        if "coach gift" in lower:
            return "Personalized Baseball Coach Gift"
        if "senior night" in lower:
            return "Custom Baseball Senior Night Poster"
        return f"Premium {keyword.title()}"

    def _build_reason(self, opportunity: Opportunity) -> str:
        reasons = []
        if opportunity.avg_price >= 40:
            reasons.append("premium average price")
        if opportunity.demand_score >= 60:
            reasons.append("strong demand signal")
        if opportunity.personalization_score >= 45:
            reasons.append("personalization opportunity")
        if opportunity.competition_score <= 75:
            reasons.append("manageable competition")
        if opportunity.confidence_score >= 60:
            reasons.append("enough listing data for confidence")
        if not reasons:
            reasons.append("meets candidate threshold")
        return "; ".join(reasons)

    def _estimate_margin(self, opportunity: Opportunity) -> float:
        if opportunity.avg_price <= 0:
            return 0.0
        # Placeholder until Finance Agent has real COGS, shipping, ads, and fees.
        return round(min(60, max(20, opportunity.avg_price * 0.75)), 2)

    def _priority_from_score(self, score: float) -> int:
        if score >= 75:
            return 10
        if score >= 65:
            return 8
        if score >= 55:
            return 6
        return 5

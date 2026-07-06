from app.database.models import CandidateProject, Keyword, Opportunity


class CandidateProjectService:
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
            return existing

        title = self._build_title(keyword.keyword)
        reason = self._build_reason(opportunity)

        candidate = CandidateProject(
            keyword_id=keyword.id,
            opportunity_id=opportunity.id,
            title=title,
            summary=opportunity.notes,
            confidence=opportunity.score,
            estimated_margin=self._estimate_margin(opportunity),
            priority=self._priority_from_score(opportunity.score),
            reason=reason,
            status="candidate",
        )

        self.session.add(candidate)
        self.session.commit()

        return candidate

    def _build_title(self, keyword: str) -> str:
        cleaned = keyword.title()

        if "lineup board" in keyword.lower():
            return "Premium Magnetic Baseball Lineup Board"

        if "dugout" in keyword.lower():
            return "Personalized Baseball Dugout Sign"

        if "banner" in keyword.lower():
            return "Custom Baseball Team Banner"

        if "coach gift" in keyword.lower():
            return "Personalized Baseball Coach Gift"

        return f"Premium {cleaned}"

    def _build_reason(self, opportunity: Opportunity) -> str:
        reasons = []

        if opportunity.avg_price >= 40:
            reasons.append("premium average price")

        if opportunity.demand_score >= 60:
            reasons.append("strong demand signal")

        if opportunity.personalization_score >= 50:
            reasons.append("strong personalization opportunity")

        if opportunity.competition_score <= 70:
            reasons.append("manageable competition")

        if not reasons:
            reasons.append("meets candidate threshold")

        return "; ".join(reasons)

    def _estimate_margin(self, opportunity: Opportunity) -> float:
        if opportunity.avg_price <= 0:
            return 0.0

        # Early estimate until Manufacturing/Finance agents provide real costs.
        return round(min(60, max(20, opportunity.avg_price * 0.75)), 2)

    def _priority_from_score(self, score: float) -> int:
        if score >= 75:
            return 10
        if score >= 65:
            return 8
        if score >= 55:
            return 6
        return 5
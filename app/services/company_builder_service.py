from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database.models import Business, BusinessOpportunity, CandidateProject, ProductProject
from app.intelligence.clustering import BusinessClusteringEngine
from app.services.business_intelligence_service import BusinessIntelligenceService
from app.services.ceo_workspace_service import CEOWorkspaceService


@dataclass
class CompanyBuildResult:
    business: Business | None
    opportunity: BusinessOpportunity
    projects: list[ProductProject]
    approved_candidates: int


class CompanyBuilderService:
    """Turns a business-level opportunity into an operating business.

    v1.3 shifts Atlas from approving individual products to approving an entire
    business opportunity. The Company Builder finds the candidate products that
    belong to that business cluster, approves them, creates product projects,
    attaches them to a business/brand, and starts the agent task pipeline.
    """

    def __init__(self, session):
        self.session = session
        self.ceo = CEOWorkspaceService(session)
        self.clustering = BusinessClusteringEngine()

    def approve_business_opportunity(self, opportunity_id: int) -> CompanyBuildResult:
        opportunity = self._opportunity(opportunity_id)
        candidates = self._candidate_products_for(opportunity)
        projects: list[ProductProject] = []

        for candidate in candidates:
            if candidate.status != "candidate":
                continue
            projects.append(self.ceo.approve_candidate(candidate.id))

        opportunity.status = "approved"
        opportunity.reviewed_at = datetime.utcnow()
        self.session.flush()

        business = None
        if projects:
            business = projects[-1].business
        else:
            business = self._matching_business(opportunity)

        self.session.commit()
        return CompanyBuildResult(
            business=business,
            opportunity=opportunity,
            projects=projects,
            approved_candidates=len(projects),
        )

    def park_business_opportunity(self, opportunity_id: int) -> BusinessOpportunity:
        opportunity = self._opportunity(opportunity_id)
        opportunity.status = "parked"
        opportunity.reviewed_at = datetime.utcnow()
        self.session.commit()
        return opportunity

    def reject_business_opportunity(self, opportunity_id: int) -> BusinessOpportunity:
        opportunity = self._opportunity(opportunity_id)
        opportunity.status = "rejected"
        opportunity.reviewed_at = datetime.utcnow()
        self.session.commit()
        return opportunity

    def refresh(self) -> list[BusinessOpportunity]:
        return BusinessIntelligenceService(self.session).refresh_business_opportunities()

    def _opportunity(self, opportunity_id: int) -> BusinessOpportunity:
        opportunity = self.session.query(BusinessOpportunity).filter_by(id=opportunity_id).first()
        if opportunity is None:
            raise ValueError(f"BusinessOpportunity not found: {opportunity_id}")
        return opportunity

    def _candidate_products_for(self, opportunity: BusinessOpportunity) -> list[CandidateProject]:
        candidates = (
            self.session.query(CandidateProject)
            .filter(CandidateProject.status.in_(["candidate", "parked", "approved"]))
            .all()
        )
        clusters = self.clustering.cluster(candidates)
        for cluster in clusters:
            if cluster.title == opportunity.title and cluster.market == opportunity.market:
                return list(cluster.products)

        if opportunity.candidate_project_id:
            candidate = self.session.query(CandidateProject).filter_by(id=opportunity.candidate_project_id).first()
            return [candidate] if candidate else []
        return []

    def _matching_business(self, opportunity: BusinessOpportunity) -> Business | None:
        return (
            self.session.query(Business)
            .filter_by(name=opportunity.title, market=opportunity.market)
            .first()
        )

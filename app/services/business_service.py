from __future__ import annotations

from datetime import datetime

from app.database.models import (
    AgentEvent,
    Brand,
    Business,
    BusinessMetric,
    BusinessOpportunity,
    CandidateProject,
    Product,
    ProductProject,
)


class BusinessService:
    """Business Engine service.

    The Business Engine groups approved product projects into larger businesses.
    A business can own many products, projects, metrics, and future departments.
    """

    def __init__(self, session):
        self.session = session

    def create_opportunity_from_candidate(self, candidate: CandidateProject) -> BusinessOpportunity:
        existing = (
            self.session.query(BusinessOpportunity)
            .filter_by(candidate_project_id=candidate.id)
            .first()
        )
        if existing:
            return existing

        opportunity = BusinessOpportunity(
            candidate_project_id=candidate.id,
            keyword_id=candidate.keyword_id,
            title=self._business_title(candidate.title),
            market=self._market_from_title(candidate.title),
            summary=candidate.summary,
            confidence=candidate.confidence,
            estimated_monthly_revenue=self._estimate_revenue(candidate.confidence, candidate.estimated_margin),
            estimated_margin=candidate.estimated_margin,
            status="candidate",
            reason=candidate.reason,
            created_at=datetime.utcnow(),
        )
        self.session.add(opportunity)
        self.session.flush()
        return opportunity

    def create_or_attach_business_for_project(
        self,
        candidate: CandidateProject,
        project: ProductProject,
    ) -> Business:
        market = self._market_from_title(candidate.title)
        business_name = self._business_title(candidate.title)
        brand_name = self._brand_name(market)

        business = (
            self.session.query(Business)
            .filter_by(name=business_name, market=market)
            .first()
        )

        if business is None:
            business = Business(
                name=business_name,
                brand_name=brand_name,
                market=market,
                status="active",
                vision=self._vision(market),
                confidence=candidate.confidence,
                estimated_monthly_revenue=self._estimate_revenue(candidate.confidence, candidate.estimated_margin),
                estimated_margin=candidate.estimated_margin,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(business)
            self.session.flush()
            self.session.add(
                Brand(
                    business_id=business.id,
                    name=brand_name,
                    positioning=self._brand_positioning(market),
                )
            )
        else:
            business.confidence = max(business.confidence, candidate.confidence)
            business.estimated_margin = max(business.estimated_margin, candidate.estimated_margin)
            business.estimated_monthly_revenue = max(
                business.estimated_monthly_revenue,
                self._estimate_revenue(candidate.confidence, candidate.estimated_margin),
            )
            business.updated_at = datetime.utcnow()

        product = self._create_or_get_product(business, candidate, project)
        project.business_id = business.id
        project.product_id = product.id

        self._record_metric(business)
        self._event(project, "COO Agent", "business_created", f"Project attached to business: {business.name}")
        self.session.flush()
        return business

    def _create_or_get_product(
        self,
        business: Business,
        candidate: CandidateProject,
        project: ProductProject,
    ) -> Product:
        product = (
            self.session.query(Product)
            .filter_by(business_id=business.id, name=project.project_name)
            .first()
        )
        if product:
            return product

        product_idea = project.product_idea
        product = Product(
            business_id=business.id,
            product_idea_id=project.product_idea_id,
            name=project.project_name,
            status="concept",
            category=self._market_from_title(candidate.title),
            target_customer=product_idea.target_customer if product_idea else "Youth sports coaches, parents, and team organizers",
            suggested_price_min=product_idea.suggested_price_min if product_idea else 0.0,
            suggested_price_max=product_idea.suggested_price_max if product_idea else 0.0,
            confidence=candidate.confidence,
            summary=candidate.summary or project.summary,
        )
        self.session.add(product)
        self.session.flush()
        return product

    def _record_metric(self, business: Business) -> None:
        products = list(business.products)
        projects = list(business.product_projects)
        product_count = len(products)
        active_project_count = len([p for p in projects if p.status == "active"])
        avg_confidence = (
            sum([p.confidence for p in products]) / product_count if product_count else business.confidence
        )
        avg_readiness = (
            sum([p.readiness_score for p in projects]) / len(projects) if projects else 0
        )
        self.session.add(
            BusinessMetric(
                business_id=business.id,
                product_count=product_count,
                active_project_count=active_project_count,
                avg_confidence=round(avg_confidence, 2),
                estimated_monthly_revenue=business.estimated_monthly_revenue,
                estimated_margin=business.estimated_margin,
                launch_readiness=round(avg_readiness, 2),
            )
        )

    def _event(self, project: ProductProject, agent_name: str, event_type: str, message: str) -> None:
        self.session.add(
            AgentEvent(
                project_id=project.id,
                agent_name=agent_name,
                event_type=event_type,
                message=message,
                created_at=datetime.utcnow(),
            )
        )

    def _business_title(self, title: str) -> str:
        low = title.lower()
        if any(term in low for term in ["lineup", "dugout", "coach", "banner", "baseball"]):
            return "Little League Coaching Products"
        return "Premium Personalized Products"

    def _market_from_title(self, title: str) -> str:
        low = title.lower()
        if "baseball" in low or "dugout" in low or "lineup" in low or "coach" in low:
            return "Youth Baseball"
        return "Personalized Gifts"

    def _brand_name(self, market: str) -> str:
        if market == "Youth Baseball":
            return "Diamond Edge Coaching"
        return "Atlas Crafted"

    def _vision(self, market: str) -> str:
        if market == "Youth Baseball":
            return "Build a premium product line for youth baseball coaches, team parents, and tournament organizers."
        return "Build a premium personalized product brand around practical, giftable products."

    def _brand_positioning(self, market: str) -> str:
        if market == "Youth Baseball":
            return "Premium, coach-focused tools that make dugout organization and team management easier."
        return "Useful, personalized products with premium presentation and fast fulfillment."

    def _estimate_revenue(self, confidence: float, margin: float) -> float:
        # Early planning estimate until sales/channel data exists.
        return round(max(2500, confidence * margin * 9.5), 2)

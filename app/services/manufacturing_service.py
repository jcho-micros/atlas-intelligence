from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database.models import AgentEvent, AgentTask, Business, ManufacturingOption, ProductProject


@dataclass
class ManufacturingSummary:
    business: Business
    options_created: int
    recommended_option: ManufacturingOption | None
    average_margin: float
    average_lead_time: float


class ManufacturingService:
    """Deterministic manufacturing intelligence for approved businesses.

    v1.5 intentionally avoids external supplier APIs. It creates realistic local
    supplier scenarios from the business/product data Atlas already has, scores
    the options, and prepares finance-ready unit economics for the next agent.
    """

    SUPPLIER_PROFILES = [
        {
            "name": "Local Laser & Print Studio",
            "type": "local maker",
            "country": "United States",
            "cost_factor": 0.42,
            "setup": 35,
            "moq": 1,
            "lead": 5,
            "ship": 6,
            "quality": 92,
            "risk": 18,
            "notes": "Fast turnaround and low MOQ; best for validation, samples, and premium personalized work.",
        },
        {
            "name": "Domestic Print-on-Demand Partner",
            "type": "print-on-demand",
            "country": "United States",
            "cost_factor": 0.34,
            "setup": 10,
            "moq": 1,
            "lead": 8,
            "ship": 8,
            "quality": 84,
            "risk": 26,
            "notes": "Balanced fulfillment option with low upfront risk and easy scaling.",
        },
        {
            "name": "Overseas Production Partner",
            "type": "bulk manufacturer",
            "country": "China / Vietnam",
            "cost_factor": 0.22,
            "setup": 95,
            "moq": 50,
            "lead": 21,
            "ship": 3,
            "quality": 76,
            "risk": 48,
            "notes": "Lowest unit cost, but higher MOQ and longer lead time. Best after product-market validation.",
        },
    ]

    def __init__(self, session):
        self.session = session

    def generate_for_business(self, business_id: int, refresh: bool = True) -> ManufacturingSummary:
        business = self.session.query(Business).filter_by(id=business_id).first()
        if business is None:
            raise ValueError(f"Business not found: {business_id}")

        projects = list(business.product_projects)
        if refresh:
            existing = self.session.query(ManufacturingOption).filter_by(business_id=business.id).all()
            for option in existing:
                self.session.delete(option)
            self.session.flush()

        options: list[ManufacturingOption] = []
        for project in projects:
            options.extend(self._options_for_project(business, project))
            project.manufacturing_status = "supplier_options_ready"
            project.stage = "manufacturing"
            project.readiness_score = max(project.readiness_score or 0, 35)

        for option in options:
            self.session.add(option)

        self.session.flush()
        recommended = self._recommended(options)
        self._ensure_manufacturing_tasks(projects)
        self._log_events(business, projects, recommended, len(options))
        self.session.commit()

        margins = [o.margin_estimate for o in options if o.margin_estimate]
        leads = [o.lead_time_days for o in options if o.lead_time_days]
        return ManufacturingSummary(
            business=business,
            options_created=len(options),
            recommended_option=recommended,
            average_margin=round(sum(margins) / len(margins), 1) if margins else 0.0,
            average_lead_time=round(sum(leads) / len(leads), 1) if leads else 0.0,
        )

    def recommended_for_business(self, business_id: int) -> ManufacturingOption | None:
        return (
            self.session.query(ManufacturingOption)
            .filter_by(business_id=business_id)
            .order_by(ManufacturingOption.vendor_score.desc())
            .first()
        )

    def _options_for_project(self, business: Business, project: ProductProject) -> list[ManufacturingOption]:
        selling_price = self._selling_price(project)
        complexity = self._complexity_multiplier(project.project_name)
        options: list[ManufacturingOption] = []

        for profile in self.SUPPLIER_PROFILES:
            unit_cost = round(max(3.5, selling_price * profile["cost_factor"] * complexity), 2)
            shipping = float(profile["ship"])
            landed = round(unit_cost + shipping, 2)
            margin = round(((selling_price - landed) / selling_price) * 100, 1) if selling_price else 0.0
            score = self._vendor_score(margin, profile["quality"], profile["risk"], profile["lead"], profile["moq"])
            options.append(
                ManufacturingOption(
                    business_id=business.id,
                    project_id=project.id,
                    supplier_name=profile["name"],
                    supplier_type=profile["type"],
                    country=profile["country"],
                    unit_cost=unit_cost,
                    setup_cost=float(profile["setup"]),
                    moq=int(profile["moq"]),
                    lead_time_days=int(profile["lead"]),
                    shipping_estimate=shipping,
                    landed_cost=landed,
                    quality_score=float(profile["quality"]),
                    risk_score=float(profile["risk"]),
                    margin_estimate=margin,
                    vendor_score=score,
                    recommendation="recommended" if score >= 75 else "review" if score >= 55 else "defer",
                    notes=f"{profile['notes']} Estimated selling price: ${selling_price:.2f}.",
                    status="candidate",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
        return options

    def _selling_price(self, project: ProductProject) -> float:
        if project.product:
            low = float(project.product.suggested_price_min or 0)
            high = float(project.product.suggested_price_max or 0)
            if high > 0:
                return round((low + high) / 2 if low > 0 else high, 2)
        # Conservative fallback based on current business model.
        return 59.99

    def _complexity_multiplier(self, name: str) -> float:
        name = (name or "").lower()
        if "banner" in name:
            return 0.82
        if "dugout" in name or "sign" in name:
            return 1.05
        if "lineup" in name or "magnetic" in name:
            return 1.18
        return 1.0

    def _vendor_score(self, margin: float, quality: float, risk: float, lead: int, moq: int) -> float:
        lead_score = max(0, 100 - lead * 2.5)
        moq_score = 100 if moq <= 1 else max(20, 100 - moq)
        raw = margin * 0.35 + quality * 0.25 + lead_score * 0.15 + moq_score * 0.10 + (100 - risk) * 0.15
        return round(max(0, min(100, raw)), 1)

    def _recommended(self, options: list[ManufacturingOption]) -> ManufacturingOption | None:
        if not options:
            return None
        best = max(options, key=lambda option: option.vendor_score or 0)
        for option in options:
            option.recommendation = "recommended" if option is best else option.recommendation
        return best

    def _ensure_manufacturing_tasks(self, projects: list[ProductProject]) -> None:
        for project in projects:
            existing = (
                self.session.query(AgentTask)
                .filter_by(project_id=project.id, agent_name="Manufacturing Agent", task_type="supplier_validation")
                .first()
            )
            if existing:
                existing.status = "complete"
                existing.completed_at = existing.completed_at or datetime.utcnow()
                continue
            self.session.add(
                AgentTask(
                    project_id=project.id,
                    agent_name="Manufacturing Agent",
                    task_type="supplier_validation",
                    title="Review supplier options and validate production path",
                    description="Atlas generated supplier options with cost, MOQ, lead time, risk, and margin estimates.",
                    status="complete",
                    priority=8,
                    completed_at=datetime.utcnow(),
                )
            )

    def _log_events(
        self,
        business: Business,
        projects: list[ProductProject],
        recommended: ManufacturingOption | None,
        option_count: int,
    ) -> None:
        if not projects:
            return
        anchor = projects[0]
        message = (
            f"Manufacturing generated {option_count} supplier option(s) for {business.name}."
        )
        if recommended:
            message += f" Recommended supplier: {recommended.supplier_name} ({recommended.vendor_score}% vendor score)."
        self.session.add(
            AgentEvent(
                project_id=anchor.id,
                agent_name="Manufacturing Agent",
                event_type="manufacturing_options_generated",
                message=message,
                created_at=datetime.utcnow(),
            )
        )

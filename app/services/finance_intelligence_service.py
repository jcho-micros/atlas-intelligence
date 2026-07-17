from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.database.models import (
    AgentEvent,
    AgentTask,
    Business,
    FinanceAnalysis,
    FinanceEvent,
    FinanceScenario,
    ProductProject,
    VendorQuote,
)


@dataclass
class FinanceSummary:
    analyses_created: int
    approved: int
    review: int
    rejected: int
    average_margin: float
    monthly_profit_estimate: float


class FinanceIntelligenceService:
    """Finance intelligence for Atlas Enterprise.

    This service turns product projects and vendor/cost assumptions into unit
    economics, break-even estimates, scenario comparisons, and finance approval
    recommendations. It is intentionally deterministic for now so Atlas can be
    tested locally before connecting to accounting or payment platforms.
    """

    MARKETPLACE_FEE_RATE = 0.065
    PAYMENT_FEE_RATE = 0.03
    PAYMENT_FIXED_FEE = 0.25
    AD_RATE = 0.10
    RESERVE_RATE = 0.02
    TARGET_MARGIN = 0.50
    DEFAULT_FIXED_LAUNCH_COST = 350.0

    def __init__(self, session):
        self.session = session

    def generate_for_business(self, business_id: int, refresh: bool = True) -> FinanceSummary:
        business = self.session.query(Business).filter_by(id=business_id).first()
        if business is None:
            raise ValueError(f"Business not found: {business_id}")

        projects = list(business.product_projects)
        if refresh:
            for existing in self.session.query(FinanceAnalysis).filter_by(business_id=business.id).all():
                self.session.delete(existing)
            self.session.flush()

        analyses: list[FinanceAnalysis] = []
        for project in projects:
            analysis = self._analysis_for_project(business, project)
            analyses.append(analysis)
            self.session.add(analysis)
            self.session.flush()
            self._create_scenarios(analysis)
            self._create_events(analysis)
            project.finance_status = analysis.approval_status
            project.stage = "finance" if analysis.approval_status != "approved" else "finance_approved"
            project.readiness_score = max(project.readiness_score or 0, 55 if analysis.approval_status == "approved" else 45)

        self.session.flush()
        self._ensure_finance_tasks(projects)
        self._log_project_events(projects, analyses)
        self._update_business_forecast(business, analyses)
        self.session.commit()

        margins = [a.gross_margin for a in analyses]
        return FinanceSummary(
            analyses_created=len(analyses),
            approved=sum(1 for a in analyses if a.approval_status == "approved"),
            review=sum(1 for a in analyses if a.approval_status == "review"),
            rejected=sum(1 for a in analyses if a.approval_status == "rejected"),
            average_margin=round(sum(margins) / len(margins), 1) if margins else 0.0,
            monthly_profit_estimate=round(sum(a.monthly_profit_estimate for a in analyses), 2),
        )

    def ensure_finance_for_all_businesses(self) -> None:
        for business in self.session.query(Business).all():
            existing = self.session.query(FinanceAnalysis).filter_by(business_id=business.id).first()
            if existing is None and business.product_projects:
                self.generate_for_business(business.id, refresh=False)

    def _analysis_for_project(self, business: Business, project: ProductProject) -> FinanceAnalysis:
        selling_price = self._selling_price(project)
        unit_cost = self._unit_cost(project, selling_price)
        packaging = round(max(1.75, selling_price * 0.04), 2)
        outbound_shipping = round(6.50 if selling_price < 75 else 8.50, 2)
        marketplace_fee = round(selling_price * self.MARKETPLACE_FEE_RATE, 2)
        payment_fee = round(selling_price * self.PAYMENT_FEE_RATE + self.PAYMENT_FIXED_FEE, 2)
        ad_cost = round(selling_price * self.AD_RATE, 2)
        reserve = round(selling_price * self.RESERVE_RATE, 2)
        total = round(unit_cost + packaging + outbound_shipping + marketplace_fee + payment_fee + ad_cost + reserve, 2)
        profit = round(selling_price - total, 2)
        margin = round((profit / selling_price) * 100, 1) if selling_price else 0.0
        break_even = int(self.DEFAULT_FIXED_LAUNCH_COST / profit) + 1 if profit > 0 else 9999
        target_price = round(total / (1 - self.TARGET_MARGIN), 2) if total else selling_price
        units = self._monthly_units(project, margin)
        monthly_profit = round(max(0, profit) * units, 2)
        approval = self._approval_status(margin)

        return FinanceAnalysis(
            business_id=business.id,
            project_id=project.id,
            scenario_name="base",
            selling_price=selling_price,
            unit_cost=unit_cost,
            packaging_cost=packaging,
            outbound_shipping_cost=outbound_shipping,
            marketplace_fee=marketplace_fee,
            payment_fee=payment_fee,
            ad_cost=ad_cost,
            reserve_cost=reserve,
            total_variable_cost=total,
            gross_profit=profit,
            gross_margin=margin,
            break_even_units=break_even,
            target_price=target_price,
            monthly_units_estimate=units,
            monthly_profit_estimate=monthly_profit,
            approval_status=approval,
            recommendation=self._recommendation(project, margin, target_price),
            assumptions=(
                "Includes estimated Etsy fee, payment processing, packaging, outbound shipping, "
                "ad spend, and operating reserve. Replace assumptions with real accounting/vendor inputs later."
            ),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _selling_price(self, project: ProductProject) -> float:
        if project.product:
            low = float(project.product.suggested_price_min or 0)
            high = float(project.product.suggested_price_max or 0)
            if low and high:
                return round((low + high) / 2, 2)
            if high:
                return round(high, 2)
        return 59.99

    def _unit_cost(self, project: ProductProject, selling_price: float) -> float:
        quote = (
            self.session.query(VendorQuote)
            .filter(VendorQuote.product_name.ilike(f"%{project.project_name[:24]}%"))
            .order_by(VendorQuote.landed_cost.asc())
            .first()
        )
        if quote and quote.landed_cost:
            return round(float(quote.landed_cost), 2)
        if project.manufacturing_options:
            best = sorted(project.manufacturing_options, key=lambda o: o.vendor_score or 0, reverse=True)[0]
            if best.landed_cost:
                return round(float(best.landed_cost), 2)
        name = (project.project_name or "").lower()
        factor = 0.32
        if "banner" in name:
            factor = 0.24
        elif "dugout" in name or "sign" in name:
            factor = 0.35
        elif "lineup" in name or "magnetic" in name:
            factor = 0.42
        return round(max(4.50, selling_price * factor), 2)

    def _monthly_units(self, project: ProductProject, margin: float) -> int:
        base = 18
        if project.keyword and project.keyword.opportunity:
            base += int((project.keyword.opportunity.demand_score or 0) / 8)
            base += int((project.keyword.opportunity.confidence_score or 0) / 18)
        if margin >= 50:
            base += 8
        elif margin < 30:
            base -= 6
        return max(4, base)

    def _approval_status(self, margin: float) -> str:
        if margin >= 45:
            return "approved"
        if margin >= 30:
            return "review"
        return "rejected"

    def _recommendation(self, project: ProductProject, margin: float, target_price: float) -> str:
        if margin >= 50:
            return f"Finance approves {project.project_name}. Margin is strong; protect premium pricing and monitor ad spend."
        if margin >= 35:
            return f"Finance recommends review. Consider pricing near ${target_price:.2f} or lowering unit/shipping cost."
        return f"Finance does not approve current economics. Raise price toward ${target_price:.2f} or find cheaper manufacturing."

    def _create_scenarios(self, analysis: FinanceAnalysis) -> None:
        scenarios = [
            ("Conservative", analysis.selling_price * 0.92, analysis.unit_cost * 1.08, max(4, int(analysis.monthly_units_estimate * 0.65)), "lower demand and higher costs"),
            ("Base", analysis.selling_price, analysis.unit_cost, analysis.monthly_units_estimate, "current working model"),
            ("Upside", analysis.selling_price * 1.10, analysis.unit_cost * 0.95, int(analysis.monthly_units_estimate * 1.35), "premium pricing and cost improvement"),
        ]
        for name, price, cost, units, notes in scenarios:
            variable = cost + analysis.packaging_cost + analysis.outbound_shipping_cost + price * self.MARKETPLACE_FEE_RATE + (price * self.PAYMENT_FEE_RATE + self.PAYMENT_FIXED_FEE) + price * self.AD_RATE + price * self.RESERVE_RATE
            profit = price - variable
            margin = (profit / price) * 100 if price else 0
            self.session.add(
                FinanceScenario(
                    analysis_id=analysis.id,
                    name=name,
                    selling_price=round(price, 2),
                    unit_cost=round(cost, 2),
                    gross_margin=round(margin, 1),
                    monthly_units=int(units),
                    monthly_profit=round(max(0, profit) * int(units), 2),
                    risk_level="low" if margin >= 45 else "medium" if margin >= 30 else "high",
                    notes=notes,
                )
            )

    def _create_events(self, analysis: FinanceAnalysis) -> None:
        self.session.add(
            FinanceEvent(
                analysis_id=analysis.id,
                event_type="unit_economics_calculated",
                message=(
                    f"Finance calculated {analysis.gross_margin:.1f}% margin, "
                    f"${analysis.gross_profit:.2f} gross profit, and {analysis.break_even_units} break-even units."
                ),
                actor="Michael",
            )
        )

    def _ensure_finance_tasks(self, projects: list[ProductProject]) -> None:
        for project in projects:
            task = (
                self.session.query(AgentTask)
                .filter_by(project_id=project.id, agent_name="Finance Agent", task_type="unit_economics")
                .first()
            )
            if task:
                task.status = "complete"
                task.completed_at = task.completed_at or datetime.utcnow()
            else:
                self.session.add(
                    AgentTask(
                        project_id=project.id,
                        agent_name="Finance Agent",
                        task_type="unit_economics",
                        title="Calculate unit economics and finance approval",
                        description="Finance Intelligence generated margins, break-even, fee model, target price, and scenario analysis.",
                        status="complete",
                        priority=9,
                        completed_at=datetime.utcnow(),
                    )
                )

    def _log_project_events(self, projects: list[ProductProject], analyses: list[FinanceAnalysis]) -> None:
        for project, analysis in zip(projects, analyses):
            self.session.add(
                AgentEvent(
                    project_id=project.id,
                    agent_name="Finance Agent",
                    event_type="finance_analysis_complete",
                    message=(
                        f"Finance analysis complete for {project.project_name}: "
                        f"{analysis.gross_margin:.1f}% margin, {analysis.approval_status.upper()} status."
                    ),
                    created_at=datetime.utcnow(),
                )
            )

    def _update_business_forecast(self, business: Business, analyses: list[FinanceAnalysis]) -> None:
        if not analyses:
            return
        business.estimated_monthly_revenue = round(sum(a.selling_price * a.monthly_units_estimate for a in analyses), 2)
        business.estimated_margin = round(sum(a.gross_margin for a in analyses) / len(analyses), 1)
        business.updated_at = datetime.utcnow()

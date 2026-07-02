from __future__ import annotations

from datetime import datetime
import json

from app.agents.business_agents import AccountingAgent, CustomerSuccessAgent, FinanceAgent, LogisticsAgent, ManufacturingAgent
from app.database.models import Keyword, ProductIdea, ProductLaunchPlan
from app.services.product_idea_service import ProductIdeaService


class LaunchPlanService:
    def __init__(self, session):
        self.session = session
        self.product_service = ProductIdeaService(session)
        self.manufacturing = ManufacturingAgent()
        self.logistics = LogisticsAgent()
        self.finance = FinanceAgent()
        self.customer_success = CustomerSuccessAgent()
        self.accounting = AccountingAgent()

    def latest_for_keyword(self, keyword_text: str) -> ProductLaunchPlan | None:
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            return None
        return (
            self.session.query(ProductLaunchPlan)
            .filter_by(keyword_id=keyword.id)
            .order_by(ProductLaunchPlan.created_at.desc())
            .first()
        )

    def generate_for_keyword(self, keyword_text: str) -> ProductLaunchPlan:
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            raise ValueError(f"Unknown keyword: {keyword_text}")

        product_idea = self.product_service.latest_for_keyword(keyword_text)
        if product_idea is None:
            self.product_service.generate_for_keyword(keyword_text)
            product_idea = self.product_service.latest_for_keyword(keyword_text)

        if product_idea is None:
            raise ValueError(f"Could not create product idea for: {keyword_text}")

        opportunity = keyword.opportunity
        avg_price = getattr(opportunity, "avg_price", 0.0) if opportunity else 0.0

        manufacturing = self.manufacturing.evaluate(
            keyword.keyword,
            product_idea.product_name,
            product_idea.suggested_price_min,
            product_idea.suggested_price_max,
        )
        logistics = self.logistics.plan(keyword.keyword, product_idea.product_name)
        finance = self.finance.calculate(avg_price, product_idea.suggested_price_min, product_idea.suggested_price_max)
        customer_success = self.customer_success.prepare(keyword.keyword, product_idea.product_name)
        accounting = self.accounting.setup(product_idea.product_name)

        plan = ProductLaunchPlan(
            keyword_id=keyword.id,
            product_idea_id=product_idea.id,
            status="draft",
            manufacturing_json=json.dumps(manufacturing.__dict__, default=str),
            logistics_json=json.dumps(logistics.__dict__, default=str),
            finance_json=json.dumps(finance.__dict__, default=str),
            customer_service_json=json.dumps(customer_success.__dict__, default=str),
            accounting_json=json.dumps(accounting.__dict__, default=str),
            next_actions="|".join([
                "Request three vendor quotes",
                "Order one production sample",
                "Calculate real unit economics",
                "Create customer service templates",
                "Decide whether to launch as test listing",
            ]),
            created_at=datetime.utcnow(),
        )
        self.session.add(plan)
        self.session.commit()
        return plan

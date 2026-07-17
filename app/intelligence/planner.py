from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlannedTask:
    agent_name: str
    task_type: str
    title: str
    description: str
    priority: int = 5


class PlannerEngine:
    """Creates an execution plan for a business opportunity.

    This is the first deterministic version of the planner. Later versions can
    let an LLM produce or refine these plans while keeping this interface stable.
    """

    def plan_business_launch(self, business_title: str, product_names: list[str]) -> list[PlannedTask]:
        products = ", ".join(product_names[:5]) or business_title
        return [
            PlannedTask(
                agent_name="COO Agent",
                task_type="business_plan",
                title="Create business launch plan",
                description=f"Create an execution roadmap for {business_title} covering products: {products}.",
                priority=10,
            ),
            PlannedTask(
                agent_name="Manufacturing Agent",
                task_type="supplier_discovery",
                title="Find production options",
                description="Identify third-party production options, likely materials, MOQs, risks, and lead times.",
                priority=9,
            ),
            PlannedTask(
                agent_name="Finance Agent",
                task_type="unit_economics",
                title="Validate unit economics",
                description="Estimate COGS, shipping, marketplace fees, ad allowance, break-even, and margin range.",
                priority=9,
            ),
            PlannedTask(
                agent_name="Marketing Agent",
                task_type="brand_positioning",
                title="Create brand and launch positioning",
                description="Draft product positioning, Etsy SEO, launch angles, and bundle strategy.",
                priority=8,
            ),
            PlannedTask(
                agent_name="Customer Success Agent",
                task_type="support_readiness",
                title="Prepare customer support assets",
                description="Draft FAQ, personalization instructions, returns language, and support macros.",
                priority=7,
            ),
        ]

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentOutput:
    summary: str
    recommendations: list[str]
    risks: list[str]
    next_steps: list[str]


def _keyword_lower(keyword: str) -> str:
    return (keyword or "").lower()


class ManufacturingAgent:
    name = "manufacturing"

    def evaluate(self, keyword: str, product_name: str, price_min: float, price_max: float) -> AgentOutput:
        k = _keyword_lower(keyword + " " + product_name)
        if any(term in k for term in ["lineup", "dugout", "sign", "banner", "board"]):
            vendors = [
                "Local laser engraving / CNC shop for wood or acrylic prototypes",
                "Print-on-demand sign vendor for low-risk test orders",
                "Custom magnet supplier for player cards or add-on packs",
                "Packaging supplier for rigid mailers, corner protectors, and branded inserts",
            ]
            risks = [
                "Physical products need quality control before scaling",
                "Custom team names/logos increase proofing time",
                "Large signs may raise shipping cost and damage risk",
            ]
        elif "shirt" in k or "apparel" in k:
            vendors = [
                "Printify or Printful for no-inventory apparel testing",
                "Local screen printer once demand is proven",
                "Blank apparel supplier for margin optimization",
            ]
            risks = [
                "Apparel is competitive and return-sensitive",
                "Sizing and color expectations can create support load",
            ]
        else:
            vendors = [
                "Start with print-on-demand or made-to-order fulfillment",
                "Request samples from two suppliers before publishing",
                "Use a local vendor for fast iteration and quality checks",
            ]
            risks = [
                "Unknown production cost until supplier quotes are collected",
                "Need sample validation before launch",
            ]

        return AgentOutput(
            summary="Find a low-MOQ production path first, then validate margin with real supplier quotes.",
            recommendations=vendors,
            risks=risks,
            next_steps=[
                "Create a simple product specification sheet with size, materials, personalization fields, and packaging needs",
                "Request quotes from at least three vendors",
                "Order one sample before publishing or accepting orders",
            ],
        )


class LogisticsAgent:
    name = "logistics"

    def plan(self, keyword: str, product_name: str) -> AgentOutput:
        k = _keyword_lower(keyword + " " + product_name)
        if any(term in k for term in ["board", "sign", "banner"]):
            recommendations = [
                "Use USPS Ground Advantage or UPS Ground depending on size and weight",
                "Use rigid packaging, corner protection, and waterproof sleeve",
                "Set processing time at 3-5 business days until production is proven",
                "Offer paid rush processing only after vendor turnaround is reliable",
            ]
            risks = [
                "Oversized packages can erase margin",
                "Damage claims can become expensive if packaging is weak",
            ]
        else:
            recommendations = [
                "Use made-to-order fulfillment until sales volume is predictable",
                "Keep processing promises conservative during launch",
                "Use tracking on every order",
            ]
            risks = [
                "Supplier delays can hurt Etsy reviews",
                "Unclear delivery promises can increase customer messages",
            ]
        return AgentOutput(
            summary="Logistics should be designed before publishing so pricing includes packaging and shipping risk.",
            recommendations=recommendations,
            risks=risks,
            next_steps=[
                "Estimate packaged weight and dimensions",
                "Calculate shipping cost for local, regional, and cross-country orders",
                "Decide whether shipping is built into price or charged separately",
            ],
        )


class FinanceAgent:
    name = "finance"

    def calculate(self, avg_price: float, suggested_min: float, suggested_max: float) -> AgentOutput:
        target_price = round((suggested_min + suggested_max) / 2, 2) if suggested_min and suggested_max else round(avg_price, 2)
        if target_price <= 0:
            target_price = 39.99
        estimated_cogs = round(target_price * 0.32, 2)
        packaging = round(max(1.75, target_price * 0.04), 2)
        shipping = round(max(5.95, target_price * 0.13), 2)
        marketplace_fees = round(target_price * 0.12, 2)
        ad_allowance = round(target_price * 0.08, 2)
        profit = round(target_price - estimated_cogs - packaging - shipping - marketplace_fees - ad_allowance, 2)
        margin = round((profit / target_price) * 100, 1) if target_price else 0
        return AgentOutput(
            summary=f"Estimated target price ${target_price:.2f}, estimated profit ${profit:.2f}, estimated margin {margin}%.",
            recommendations=[
                f"Target launch price around ${target_price:.2f}",
                f"Keep all-in production cost under ${estimated_cogs + packaging:.2f}",
                f"Reserve about ${ad_allowance:.2f} per order for ads/testing",
                "Reject or rework the product if quote-based margin falls below 30%",
            ],
            risks=[
                "These are planning estimates, not accounting records",
                "Actual Etsy fees, ads, returns, and shipping zones can materially change margin",
                "Taxes and bookkeeping rules should be reviewed with a qualified professional",
            ],
            next_steps=[
                "Collect real supplier quotes",
                "Calculate landed cost including packaging and damages",
                "Create a simple SKU-level profit sheet before launch",
            ],
        )


class CustomerSuccessAgent:
    name = "customer_success"

    def prepare(self, keyword: str, product_name: str) -> AgentOutput:
        return AgentOutput(
            summary="Customer service should be mostly templated before launch, especially for personalized products.",
            recommendations=[
                "Create canned responses for personalization questions, proof approvals, rush orders, and address changes",
                "Require personalization details in structured fields before checkout",
                "Set a clear proofing policy if customer approval is required",
                "Create replacement/refund rules before publishing",
            ],
            risks=[
                "Personalization mistakes can create refunds and bad reviews",
                "Unclear proofing expectations can slow fulfillment",
                "Fast turnaround promises increase support pressure",
            ],
            next_steps=[
                "Write three customer message templates",
                "Write personalization instructions for the listing",
                "Define refund/replacement policy for custom items",
            ],
        )


class AccountingAgent:
    name = "accounting"

    def setup(self, product_name: str) -> AgentOutput:
        return AgentOutput(
            summary="Accounting should track each product idea as an experiment with clear cost, revenue, and profit fields.",
            recommendations=[
                "Create one SKU/project code for this product concept",
                "Track samples, design costs, supplier costs, shipping, ads, Etsy fees, refunds, and net profit",
                "Separate product validation spend from operating expenses",
                "Review taxes and sales-tax obligations with a qualified professional",
            ],
            risks=[
                "Blended expenses hide whether a product is actually profitable",
                "Untracked samples and ads can make margins look better than reality",
            ],
            next_steps=[
                "Create a profit tracker spreadsheet or database table",
                "Record sample order cost before launch",
                "Track every order by SKU after launch",
            ],
        )

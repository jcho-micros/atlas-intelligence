from __future__ import annotations

from datetime import datetime

from app.database.models import Vendor, VendorContact, VendorEvent, VendorQuote


class VendorIntelligenceService:
    """Creates and maintains Atlas vendor intelligence demo data.

    This service is intentionally deterministic for now. Later releases can plug in
    Alibaba, Thomasnet, Printify, Printful, Gmail, or supplier portal connectors.
    """

    def __init__(self, session):
        self.session = session

    def ensure_seed_vendors(self) -> dict[str, int]:
        vendors = [
            {
                "name": "Precision Acrylic Works",
                "category": "Acrylic Fabrication",
                "relationship_status": "preferred",
                "location": "Pennsylvania, USA",
                "website": "https://example.com/precision-acrylic",
                "contact_name": "Morgan Lee",
                "contact_email": "quotes@precision-acrylic.example",
                "capabilities": "laser cutting|acrylic panels|UV printing|small batch production",
                "notes": "Best fit for premium lineup boards and dry erase coach products.",
                "trust_score": 94,
                "quality_score": 96,
                "communication_score": 91,
                "pricing_score": 88,
                "delivery_score": 93,
                "average_lead_time_days": 8,
                "minimum_order_quantity": 25,
                "average_margin": 58,
                "projects_completed": 14,
                "risk_level": "low",
                "recommendation": "Use for premium acrylic products where quality matters more than lowest cost.",
                "quotes": [
                    ("Premium Magnetic Baseball Lineup Board", 18.75, 4.80, 23.55, 25, 8, "recommended"),
                    ("Dry Erase Practice Planner", 12.40, 3.50, 15.90, 50, 7, "active"),
                ],
            },
            {
                "name": "Midwest Wood & Sign Co.",
                "category": "Wood Products",
                "relationship_status": "strategic",
                "location": "Ohio, USA",
                "website": "https://example.com/midwest-sign",
                "contact_name": "Alex Carter",
                "contact_email": "sales@midwest-sign.example",
                "capabilities": "birch plywood|engraving|painted signs|team gifts|packaging",
                "notes": "Strong fit for dugout signs, coach plaques, and bundled gift products.",
                "trust_score": 90,
                "quality_score": 92,
                "communication_score": 87,
                "pricing_score": 90,
                "delivery_score": 88,
                "average_lead_time_days": 10,
                "minimum_order_quantity": 30,
                "average_margin": 54,
                "projects_completed": 22,
                "risk_level": "low",
                "recommendation": "Best all-around domestic supplier for wooden baseball products.",
                "quotes": [
                    ("Personalized Baseball Dugout Sign", 14.20, 5.25, 19.45, 30, 10, "recommended"),
                    ("Coach Clipboard Gift Holder", 7.80, 2.60, 10.40, 75, 9, "active"),
                ],
            },
            {
                "name": "Global Team Banner Supply",
                "category": "Printed Goods",
                "relationship_status": "prospect",
                "location": "Shenzhen, China",
                "website": "https://example.com/global-banner",
                "contact_name": "Ivy Zhang",
                "contact_email": "ivy@global-banner.example",
                "capabilities": "vinyl banners|team flags|bulk printing|custom packaging",
                "notes": "Lowest banner cost, but longer lead time and higher logistics uncertainty.",
                "trust_score": 78,
                "quality_score": 80,
                "communication_score": 76,
                "pricing_score": 96,
                "delivery_score": 70,
                "average_lead_time_days": 18,
                "minimum_order_quantity": 100,
                "average_margin": 62,
                "projects_completed": 4,
                "risk_level": "medium",
                "recommendation": "Use for bulk banners after sample approval. Avoid rush launches.",
                "quotes": [
                    ("Custom Baseball Team Banner", 8.95, 6.75, 15.70, 100, 18, "needs_sample"),
                ],
            },
            {
                "name": "QuickTurn Sports Prints",
                "category": "Print-on-Demand",
                "relationship_status": "backup",
                "location": "Texas, USA",
                "website": "https://example.com/quickturn-sports",
                "contact_name": "Jordan Smith",
                "contact_email": "support@quickturn-sports.example",
                "capabilities": "posters|senior night prints|short run banners|drop shipping",
                "notes": "Fast turnaround and low MOQ, but unit economics are weaker.",
                "trust_score": 84,
                "quality_score": 85,
                "communication_score": 89,
                "pricing_score": 73,
                "delivery_score": 92,
                "average_lead_time_days": 4,
                "minimum_order_quantity": 1,
                "average_margin": 41,
                "projects_completed": 9,
                "risk_level": "low",
                "recommendation": "Use for validation runs, samples, and urgent custom print orders.",
                "quotes": [
                    ("Baseball Senior Night Poster", 9.50, 3.25, 12.75, 1, 4, "backup"),
                ],
            },
        ]

        created = 0
        for row in vendors:
            vendor = self.session.query(Vendor).filter_by(name=row["name"]).first()
            if vendor is None:
                vendor = Vendor(**{k: v for k, v in row.items() if k != "quotes"})
                self.session.add(vendor)
                self.session.flush()
                self.session.add(VendorContact(
                    vendor_id=vendor.id,
                    name=row["contact_name"],
                    title="Sales / Quote Contact",
                    email=row["contact_email"],
                    is_primary=True,
                ))
                for product_name, unit_cost, shipping_cost, landed_cost, moq, lead_time_days, status in row["quotes"]:
                    self.session.add(VendorQuote(
                        vendor_id=vendor.id,
                        product_name=product_name,
                        unit_cost=unit_cost,
                        shipping_cost=shipping_cost,
                        landed_cost=landed_cost,
                        moq=moq,
                        lead_time_days=lead_time_days,
                        quote_status=status,
                        notes=self._quote_notes(product_name, landed_cost, moq, lead_time_days),
                    ))
                self.session.add(VendorEvent(
                    vendor_id=vendor.id,
                    event_type="vendor_profile_created",
                    actor="David",
                    message=f"Created vendor intelligence profile for {row['name']}.",
                ))
                created += 1
            else:
                # Keep evolving demo vendors when the release is rerun.
                for key, value in row.items():
                    if key != "quotes":
                        setattr(vendor, key, value)
                vendor.updated_at = datetime.utcnow()

        self.session.commit()
        return {"vendors_created": created, "vendors_total": self.session.query(Vendor).count()}

    def recommend_vendor(self, product_name: str | None = None) -> Vendor | None:
        query = self.session.query(Vendor)
        if product_name:
            product_name_l = product_name.lower()
            if "banner" in product_name_l:
                query = query.filter(Vendor.category.in_(["Printed Goods", "Print-on-Demand"]))
            elif "dugout" in product_name_l or "wood" in product_name_l or "sign" in product_name_l:
                query = query.filter(Vendor.category == "Wood Products")
            elif "lineup" in product_name_l or "acrylic" in product_name_l:
                query = query.filter(Vendor.category == "Acrylic Fabrication")
        return query.order_by(Vendor.trust_score.desc(), Vendor.average_margin.desc()).first()

    def create_rfq_event(self, vendor_id: int, product_name: str) -> VendorEvent:
        vendor = self.session.get(Vendor, vendor_id)
        if vendor is None:
            raise ValueError(f"Vendor {vendor_id} not found")
        event = VendorEvent(
            vendor_id=vendor.id,
            event_type="rfq_prepared",
            actor="David",
            message=f"Prepared RFQ for {product_name} to send to {vendor.name}.",
        )
        self.session.add(event)
        self.session.commit()
        return event

    def _quote_notes(self, product_name: str, landed_cost: float, moq: int, lead_time_days: int) -> str:
        return (
            f"Estimated landed cost for {product_name}: ${landed_cost:.2f}; "
            f"MOQ {moq}; lead time {lead_time_days} days."
        )

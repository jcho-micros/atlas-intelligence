from __future__ import annotations

from datetime import datetime

from app.ai.product_designer import ProductDesigner
from app.ai.product_models import ProductIdeaDraft
from app.database.models import Keyword, Listing, ProductIdea


class ProductIdeaService:
    def __init__(self, session):
        self.session = session
        self.designer = ProductDesigner()

    def generate_for_keyword(self, keyword_text: str) -> ProductIdeaDraft:
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            raise ValueError(f"Unknown keyword: {keyword_text}")

        opportunity = keyword.opportunity
        listings = (
            self.session.query(Listing)
            .filter_by(keyword_id=keyword.id)
            .order_by(Listing.views.desc(), Listing.num_favorers.desc())
            .limit(25)
            .all()
        )

        latest_snapshot = keyword.snapshots[-1] if keyword.snapshots else None
        opportunity_payload = {
            "keyword": keyword.keyword,
            "avg_price": getattr(opportunity, "avg_price", 0) if opportunity else 0,
            "median_price": getattr(opportunity, "median_price", 0) if opportunity else 0,
            "score": getattr(opportunity, "score", 0) if opportunity else 0,
            "listings": getattr(opportunity, "listing_count", len(listings)) if opportunity else len(listings),
            "avg_views": getattr(latest_snapshot, "avg_views", 0) if latest_snapshot else 0,
            "avg_favorites": getattr(latest_snapshot, "avg_favorites", 0) if latest_snapshot else 0,
            "personalized_count": getattr(latest_snapshot, "personalized_count", 0) if latest_snapshot else 0,
            "digital_count": getattr(latest_snapshot, "digital_count", 0) if latest_snapshot else 0,
        }
        listing_payload = [
            {
                "title": item.title,
                "price": item.price,
                "views": item.views,
                "favorites": item.num_favorers,
                "tags": item.tags,
                "is_personalized": item.is_personalized,
                "is_digital": item.is_digital,
            }
            for item in listings
        ]
        draft = self.designer.design(opportunity_payload, listing_payload)
        self._save(keyword, draft)
        return draft

    def latest_for_keyword(self, keyword_text: str) -> ProductIdea | None:
        keyword = self.session.query(Keyword).filter_by(keyword=keyword_text).first()
        if keyword is None:
            return None
        return (
            self.session.query(ProductIdea)
            .filter_by(keyword_id=keyword.id)
            .order_by(ProductIdea.created_at.desc())
            .first()
        )

    def _save(self, keyword: Keyword, draft: ProductIdeaDraft) -> ProductIdea:
        idea = ProductIdea(
            keyword_id=keyword.id,
            product_name=draft.product_name,
            target_customer=draft.target_customer,
            suggested_price_min=draft.price_min,
            suggested_price_max=draft.price_max,
            confidence=draft.confidence,
            materials="|".join(draft.materials),
            features="|".join(draft.features),
            differentiators="|".join(draft.differentiators),
            etsy_title=draft.etsy_title,
            etsy_description=draft.etsy_description,
            etsy_tags="|".join(draft.etsy_tags),
            faq="|".join(draft.faq),
            image_prompt=draft.image_prompt,
            rationale=draft.rationale,
            created_at=datetime.utcnow(),
        )
        self.session.add(idea)
        self.session.commit()
        return idea

from datetime import datetime
from sqlalchemy.orm import Session
from app.connectors.base import MarketplaceListing
from app.database.models import Listing, Opportunity, Keyword
from app.scoring.opportunity import OpportunityScorer


class ListingService:
    def __init__(self, session: Session):
        self.session = session
        self.scorer = OpportunityScorer()

    def replace_keyword_listings(
        self,
        keyword: Keyword,
        marketplace: str,
        listings: list[MarketplaceListing],
    ) -> None:
        self.session.query(Listing).filter_by(keyword_id=keyword.id, marketplace=marketplace).delete()
        for item in listings:
            self.session.add(
                Listing(
                    keyword_id=keyword.id,
                    marketplace=marketplace,
                    external_id=item.external_id,
                    title=item.title,
                    price=item.price,
                    currency=item.currency,
                    shop_name=item.shop_name,
                    review_count=item.review_count,
                    rating=item.rating,
                    url=item.url,
                    image_url=item.image_url,
                    is_personalized=item.is_personalized,
                    is_digital=item.is_digital,
                    last_seen_at=datetime.utcnow(),
                )
            )
        scores = self.scorer.score(listings)
        opportunity = self.session.query(Opportunity).filter_by(keyword_id=keyword.id).one_or_none()
        if opportunity is None:
            opportunity = Opportunity(keyword_id=keyword.id)
            self.session.add(opportunity)
        for field, value in scores.items():
            setattr(opportunity, field, value)
        opportunity.updated_at = datetime.utcnow()
        keyword.status = "completed" if listings else "no_data"
        self.session.commit()

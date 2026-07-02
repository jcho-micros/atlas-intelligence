from statistics import median
from app.database.models import Keyword, KeywordSnapshot, Listing, ListingSnapshot, Opportunity, ResearchRun


class SnapshotService:
    def __init__(self, session):
        self.session = session

    def snapshot_keyword(self, keyword: Keyword, run: ResearchRun, listings: list[Listing]) -> KeywordSnapshot:
        prices = [listing.price for listing in listings if listing.price > 0]
        listing_count = len(listings)
        avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
        median_price = round(median(prices), 2) if prices else 0.0
        avg_views = round(sum((listing.views or 0) for listing in listings) / listing_count, 2) if listing_count else 0.0
        avg_favorites = round(sum((listing.num_favorers or 0) for listing in listings) / listing_count, 2) if listing_count else 0.0
        personalized_count = sum(1 for listing in listings if listing.is_personalized)
        digital_count = sum(1 for listing in listings if listing.is_digital)
        opportunity = self.session.query(Opportunity).filter_by(keyword_id=keyword.id).first()
        opportunity_score = opportunity.score if opportunity else 0.0

        for listing in listings:
            self.session.add(ListingSnapshot(
                research_run_id=run.id,
                listing_id=listing.id,
                keyword_id=keyword.id,
                price=listing.price,
                num_favorers=listing.num_favorers,
                views=listing.views,
                quantity=listing.quantity,
            ))

        snapshot = KeywordSnapshot(
            research_run_id=run.id,
            keyword_id=keyword.id,
            listing_count=listing_count,
            avg_price=avg_price,
            median_price=median_price,
            avg_views=avg_views,
            avg_favorites=avg_favorites,
            personalized_count=personalized_count,
            digital_count=digital_count,
            opportunity_score=opportunity_score,
        )
        self.session.add(snapshot)
        self.session.commit()
        return snapshot

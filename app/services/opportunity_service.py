from statistics import median

from app.database.models import Keyword, Listing, Opportunity


class OpportunityService:
    def __init__(self, session):
        self.session = session

    def calculate_for_keyword(self, keyword: Keyword) -> Opportunity:
        listings = self.session.query(Listing).filter_by(keyword_id=keyword.id).all()

        listing_count = len(listings)
        prices = [item.price for item in listings if item.price > 0]

        avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
        median_price = round(median(prices), 2) if prices else 0.0

        personalized_count = sum(1 for item in listings if item.is_personalized)
        digital_count = sum(1 for item in listings if item.is_digital)

        personalization_score = (
            round((personalized_count / listing_count) * 100, 2)
            if listing_count
            else 0.0
        )

        demand_score = min(100, listing_count * 1.5)
        competition_score = min(100, listing_count * 4)
        profit_score = min(100, avg_price * 1.5)
        confidence_score = min(100, listing_count * 4)

        raw_score = (
            demand_score * 1.0
            + profit_score * 1.0
            + personalization_score * 0.7
            - competition_score * 0.8
        )

        score = round(max(0, min(100, raw_score)), 2)

        recommendation = "BUILD" if score >= 80 else "WATCH" if score >= 55 else "WAIT"

        notes = (
            f"{listing_count} listings analyzed; "
            f"avg price ${avg_price}; "
            f"{personalized_count} personalized; "
            f"{digital_count} digital"
        )

        opportunity = (
            self.session.query(Opportunity).filter_by(keyword_id=keyword.id).first()
        )

        if not opportunity:
            opportunity = Opportunity(keyword_id=keyword.id)
            self.session.add(opportunity)

        opportunity.score = score
        opportunity.demand_score = demand_score
        opportunity.competition_score = competition_score
        opportunity.profit_score = profit_score
        opportunity.personalization_score = personalization_score
        opportunity.confidence_score = confidence_score
        opportunity.avg_price = avg_price
        opportunity.median_price = median_price
        opportunity.listing_count = listing_count
        opportunity.recommendation = recommendation
        opportunity.notes = notes

        self.session.commit()
        return opportunity
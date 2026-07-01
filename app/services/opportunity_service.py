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

        total_views = sum(item.views or 0 for item in listings)
        total_favorites = sum(item.num_favorers or 0 for item in listings)

        personalized_count = sum(1 for item in listings if item.is_personalized)
        digital_count = sum(1 for item in listings if item.is_digital)

        personalized_ratio = personalized_count / listing_count if listing_count else 0
        digital_ratio = digital_count / listing_count if listing_count else 0

        avg_views = total_views / listing_count if listing_count else 0
        avg_favorites = total_favorites / listing_count if listing_count else 0

        demand_score = min(100, (avg_views / 500) * 50 + (avg_favorites / 50) * 50)
        competition_score = min(100, listing_count * 4)
        profit_score = min(100, avg_price * 1.5)
        personalization_score = round(personalized_ratio * 100, 2)

        # Digital products are easier to fulfill, but too many digital listings can mean saturation.
        digital_bonus = 8 if 0.15 <= digital_ratio <= 0.55 else 0

        raw_score = (
            demand_score * 0.35
            + profit_score * 0.30
            + personalization_score * 0.20
            + digital_bonus
            - competition_score * 0.15
        )

        score = round(max(0, min(100, raw_score)), 2)
        confidence_score = min(100, listing_count * 4)

        recommendation = "BUILD" if score >= 75 else "WATCH" if score >= 45 else "WAIT"

        notes = (
            f"{listing_count} listings; "
            f"avg ${avg_price}; "
            f"avg views {round(avg_views)}; "
            f"avg favorites {round(avg_favorites)}; "
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
        opportunity.demand_score = round(demand_score, 2)
        opportunity.competition_score = round(competition_score, 2)
        opportunity.profit_score = round(profit_score, 2)
        opportunity.personalization_score = personalization_score
        opportunity.confidence_score = round(confidence_score, 2)
        opportunity.avg_price = avg_price
        opportunity.median_price = median_price
        opportunity.listing_count = listing_count
        opportunity.recommendation = recommendation
        opportunity.notes = notes

        self.session.commit()
        return opportunity
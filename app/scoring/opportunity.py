from statistics import mean
from app.connectors.base import MarketplaceListing


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


class OpportunityScorer:
    def score(self, listings: list[MarketplaceListing]) -> dict:
        if not listings:
            return {
                "score": 0,
                "demand_score": 0,
                "competition_score": 0,
                "profit_score": 0,
                "personalization_score": 0,
                "confidence_score": 0,
                "avg_price": 0,
                "listing_count": 0,
                "recommendation": "NO DATA",
                "notes": "No listings were found. Check connector, API key, or keyword.",
            }

        prices = [x.price for x in listings if x.price > 0]
        avg_price = mean(prices) if prices else 0
        listing_count = len(listings)
        personalized_count = sum(1 for x in listings if x.is_personalized)
        digital_count = sum(1 for x in listings if x.is_digital)
        avg_reviews = mean([x.review_count for x in listings]) if listings else 0
        unique_shops = len(set(x.shop_name for x in listings))

        demand_score = clamp((avg_reviews / 20) + (listing_count * 0.8))
        competition_score = clamp(unique_shops * 5.5 + listing_count * 1.2)
        profit_score = clamp((avg_price - 12) * 2.2)
        personalization_score = clamp((personalized_count / listing_count) * 100)
        confidence_score = clamp(listing_count * 3)

        raw_score = (
            demand_score * 0.8
            + profit_score * 1.1
            + personalization_score * 0.45
            + confidence_score * 0.25
            - competition_score * 0.85
        )
        score = round(clamp(raw_score), 2)

        if score >= 75:
            recommendation = "BUILD NOW"
        elif score >= 55:
            recommendation = "RESEARCH MORE"
        elif score >= 35:
            recommendation = "WATCH"
        else:
            recommendation = "WAIT"

        notes = []
        if avg_price >= 30:
            notes.append("Healthy price point")
        if personalization_score >= 50:
            notes.append("Strong personalization angle")
        if digital_count / listing_count >= 0.5:
            notes.append("Mostly digital products")
        if competition_score >= 75:
            notes.append("Crowded market")
        if not notes:
            notes.append("Needs more evidence")

        return {
            "score": score,
            "demand_score": round(demand_score, 2),
            "competition_score": round(competition_score, 2),
            "profit_score": round(profit_score, 2),
            "personalization_score": round(personalization_score, 2),
            "confidence_score": round(confidence_score, 2),
            "avg_price": round(avg_price, 2),
            "listing_count": listing_count,
            "recommendation": recommendation,
            "notes": "; ".join(notes),
        }

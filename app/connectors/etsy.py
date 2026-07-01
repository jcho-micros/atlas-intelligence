import os
import requests

from app.connectors.base import MarketplaceListing


class EtsyConnector:
    """
    Etsy API v3 Connector
    """

    name = "etsy"

    BASE_URL = "https://openapi.etsy.com/v3/application"

    def __init__(self):
        self.keystring = os.getenv("ETSY_API_KEY")
        self.shared_secret = os.getenv("ETSY_SHARED_SECRET")

        if not self.keystring:
            raise ValueError("Missing ETSY_API_KEY in .env")

        if not self.shared_secret:
            raise ValueError("Missing ETSY_SHARED_SECRET in .env")

    def _headers(self):
        """
        Authentication headers.
        """
        return {
            "x-api-key": f"{self.keystring}:{self.shared_secret}",
            "Accept": "application/json",
        }

    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]:

        url = f"{self.BASE_URL}/listings/active"

        params = {
            "keywords": keyword,
            "limit": limit,
        }

        response = requests.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Etsy API Error {response.status_code}\n"
                f"{response.text}"
            )

        data = response.json()

        listings: list[MarketplaceListing] = []

        for item in data.get("results", []):

            price = 0.0
            currency = "USD"

            if isinstance(item.get("price"), dict):
                amount = item["price"].get("amount", 0)
                divisor = item["price"].get("divisor", 100)

                try:
                    price = float(amount) / float(divisor)
                except Exception:
                    price = 0.0

                currency = item["price"].get(
                    "currency_code",
                    "USD",
                )

            listings.append(
                MarketplaceListing(
                    external_id=str(item.get("listing_id", "")),
                    title=item.get("title", ""),
                    price=price,
                    currency=currency,
                    shop_name=str(item.get("shop_id", "")),
                    review_count=0,
                    rating=0.0,
                    url=item.get("url", ""),
                    image_url="",
                    is_personalized=item.get(
                        "is_personalizable",
                        False,
                    ),
                    is_digital=item.get(
                        "is_digital",
                        False,
                    ),
                )
            )

        return listings
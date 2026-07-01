import os

import requests

from app.connectors.base import MarketplaceListing


class EtsyConnector:
    name = "etsy"

    BASE_URL = "https://openapi.etsy.com/v3/application"

    def __init__(self):
        self.keystring = os.getenv("ETSY_API_KEY")
        self.shared_secret = os.getenv("ETSY_SHARED_SECRET")

        if not self.keystring:
            raise ValueError("Missing ETSY_API_KEY in .env")

        if not self.shared_secret:
            raise ValueError("Missing ETSY_SHARED_SECRET in .env")

    def _headers(self) -> dict[str, str]:
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
                f"Etsy API Error {response.status_code}\n{response.text}"
            )

        data = response.json()
        listings: list[MarketplaceListing] = []

        for item in data.get("results", []):
            price = 0.0
            currency = "USD"

            price_data = item.get("price")
            if isinstance(price_data, dict):
                amount = price_data.get("amount", 0)
                divisor = price_data.get("divisor", 100) or 100
                price = round(float(amount) / float(divisor), 2)
                currency = price_data.get("currency_code", "USD")

            processing_min = item.get("processing_min")
            processing_max = item.get("processing_max")

            processing_time = ""
            if processing_min is not None and processing_max is not None:
                processing_time = f"{processing_min}-{processing_max} days"

            listings.append(
                MarketplaceListing(
                    external_id=str(item.get("listing_id", "")),
                    title=item.get("title", ""),
                    price=price,
                    currency=currency,
                    shop_name=str(item.get("shop_id", "Unknown")),
                    review_count=0,
                    rating=0.0,
                    url=item.get("url", ""),
                    image_url="",
                    is_personalized=bool(item.get("is_personalizable", False)),
                    is_digital=item.get("listing_type") == "download",
                    shipping_price=0.0,
                    processing_time=processing_time,
                    num_favorers=int(item.get("num_favorers") or 0),
                    views=int(item.get("views") or 0),
                    quantity=int(item.get("quantity") or 0),
                    tags="|".join(item.get("tags") or []),
                    materials="|".join(item.get("materials") or []),
                    processing_min=processing_min,
                    processing_max=processing_max,
                    created_timestamp=item.get("created_timestamp"),
                    updated_timestamp=item.get("updated_timestamp"),
                )
            )

        return listings
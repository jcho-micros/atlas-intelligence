import os
import requests
from app.connectors.base import MarketplaceConnector, MarketplaceListing


class EtsyConnector(MarketplaceConnector):
    marketplace_name = "etsy"

    def __init__(self):
        self.api_key = os.getenv("ETSY_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("ETSY_API_KEY is missing. Use ATLAS_DATA_MODE=sample until Etsy approval is complete.")

    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]:
        url = "https://openapi.etsy.com/v3/application/listings/active"
        params = {"keywords": keyword, "limit": min(limit, 100)}
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        listings = []
        for row in results:
            price_info = row.get("price") or {}
            amount = price_info.get("amount")
            divisor = price_info.get("divisor", 100)
            price = float(amount or 0) / float(divisor or 100)
            title = row.get("title") or "Untitled"
            lower_title = title.lower()
            listings.append(
                MarketplaceListing(
                    external_id=str(row.get("listing_id")),
                    title=title,
                    price=round(price, 2),
                    currency=price_info.get("currency_code", "USD"),
                    shop_name=str(row.get("shop_id", "Unknown")),
                    url=row.get("url") or "",
                    is_personalized="personalized" in lower_title or "custom" in lower_title,
                    is_digital="digital" in lower_title or "download" in lower_title,
                )
            )
        return listings

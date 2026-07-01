from __future__ import annotations

import os
from typing import Any

import requests

from app.connectors.base import MarketplaceListing


class EtsyConnector:
    name = "etsy"
    marketplace_name = "etsy"
    base_url = "https://openapi.etsy.com/v3/application"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ETSY_API_KEY", "")
        if not self.api_key:
            raise ValueError("ETSY_API_KEY is required for the Etsy connector.")

    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]:
        url = f"{self.base_url}/listings/active"
        params = {"keywords": keyword, "limit": min(limit, 100), "includes": "Images,Shop"}
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return [self._normalize(item) for item in data.get("results", [])]

    def _normalize(self, item: dict[str, Any]) -> MarketplaceListing:
        images = item.get("Images") or []
        image_url = images[0].get("url_fullxfull", "") if images else ""
        shop = item.get("Shop") or {}
        title = item.get("title", "")
        description = item.get("description", "") or ""
        text = f"{title} {description}".lower()
        price = item.get("price", {})
        amount = price.get("amount") if isinstance(price, dict) else None
        divisor = price.get("divisor", 100) if isinstance(price, dict) else 100
        currency = price.get("currency_code", "USD") if isinstance(price, dict) else "USD"
        normalized_price = round(float(amount or 0) / float(divisor or 100), 2)
        listing_id = str(item.get("listing_id", ""))
        url = item.get("url") or f"https://www.etsy.com/listing/{listing_id}"

        return MarketplaceListing(
            external_id=listing_id,
            title=title,
            price=normalized_price,
            currency=currency,
            shop_name=shop.get("shop_name", "Unknown"),
            review_count=0,
            rating=0.0,
            url=url,
            image_url=image_url,
            is_personalized="personalized" in text or "custom" in text,
            is_digital="digital" in text or "download" in text,
        )

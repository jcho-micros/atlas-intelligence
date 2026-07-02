from dataclasses import dataclass
from typing import Protocol


@dataclass
class MarketplaceListing:
    external_id: str
    title: str
    price: float
    currency: str = "USD"
    shop_name: str = "Unknown"
    review_count: int = 0
    rating: float = 0.0
    url: str = ""
    image_url: str = ""
    is_personalized: bool = False
    is_digital: bool = False
    shipping_price: float = 0.0
    processing_time: str | None = None
    num_favorers: int = 0
    views: int = 0
    quantity: int = 0
    tags: str = ""
    materials: str = ""
    processing_min: int | None = None
    processing_max: int | None = None
    created_timestamp: int | None = None
    updated_timestamp: int | None = None


class MarketplaceConnector(Protocol):
    name: str
    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]: ...

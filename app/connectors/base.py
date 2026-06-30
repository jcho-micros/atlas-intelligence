from dataclasses import dataclass


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


class MarketplaceConnector:
    marketplace_name = "base"

    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]:
        raise NotImplementedError

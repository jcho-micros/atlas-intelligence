import random

from app.connectors.base import MarketplaceListing


class SampleConnector:
    name = "sample"

    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]:
        listings = []

        for i in range(limit):
            price = round(random.uniform(12.99, 54.99), 2)
            listings.append(
                MarketplaceListing(
                    external_id=f"sample-{keyword.replace(' ', '-')}-{i}",
                    title=f"{keyword.title()} Product {i + 1}",
                    price=price,
                    shop_name=f"Sample Shop {random.randint(1, 10)}",
                    review_count=random.randint(0, 1500),
                    rating=round(random.uniform(3.8, 5.0), 1),
                    url=f"https://example.com/{keyword.replace(' ', '-')}/{i}",
                    image_url="",
                    is_personalized=random.choice([True, False]),
                    is_digital=random.choice([False, False, True]),
                    shipping_price=round(random.uniform(0, 7.99), 2),
                    processing_time=random.choice(["1-2 days", "3-5 days", "1 week"]),
                )
            )

        return listings
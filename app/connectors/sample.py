import hashlib
import random
from app.connectors.base import MarketplaceListing


class SampleConnector:
    name = "sample"
    marketplace_name = "sample"

    def search(self, keyword: str, limit: int = 25) -> list[MarketplaceListing]:
        seed = int(hashlib.md5(keyword.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        listings = []
        base_price = rng.uniform(14, 48)
        for i in range(limit):
            title_bits = [keyword.title()]
            if rng.random() > 0.35:
                title_bits.append("Personalized")
            if rng.random() > 0.75:
                title_bits.append("Digital Download")
            price = max(4.99, base_price + rng.uniform(-8, 12))
            views = rng.randint(50, 12000)
            favorites = rng.randint(0, 600)
            listings.append(MarketplaceListing(
                external_id=f"sample-{seed}-{i}",
                title=" - ".join(title_bits),
                price=round(price, 2),
                shop_name=f"Sample Shop {rng.randint(1, 18)}",
                review_count=rng.randint(0, 900),
                rating=round(rng.uniform(3.8, 5.0), 2),
                url="https://example.com/sample-listing",
                image_url="https://via.placeholder.com/160",
                is_personalized="Personalized" in title_bits,
                is_digital="Digital Download" in title_bits,
                num_favorers=favorites,
                views=views,
                quantity=rng.randint(1, 999),
                tags="baseball|gift|custom|coach",
                processing_min=rng.randint(1, 3),
                processing_max=rng.randint(3, 7),
            ))
        return listings

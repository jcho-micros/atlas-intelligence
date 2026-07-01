from datetime import datetime

from app.connectors.base import MarketplaceListing
from app.database.models import Keyword, Listing, Shop


class ListingService:
    def __init__(self, session):
        self.session = session

    def save_listings(self, keyword: Keyword, marketplace: str, listings: list[MarketplaceListing]) -> int:
        saved = 0
        for item in listings:
            shop = self._get_or_create_shop(item, marketplace)
            existing = (
                self.session.query(Listing)
                .filter_by(keyword_id=keyword.id, marketplace=marketplace, external_id=item.external_id)
                .first()
            )
            if existing:
                existing.title = item.title
                existing.price = item.price
                existing.currency = item.currency
                existing.shop_name = item.shop_name
                existing.review_count = item.review_count
                existing.rating = item.rating
                existing.url = item.url
                existing.image_url = item.image_url
                existing.is_personalized = item.is_personalized
                existing.is_digital = item.is_digital
                existing.shipping_price = item.shipping_price
                existing.processing_time = item.processing_time
                existing.last_seen_at = datetime.utcnow()
                existing.shop_id = shop.id
            else:
                self.session.add(
                    Listing(
                        keyword_id=keyword.id,
                        shop_id=shop.id,
                        marketplace=marketplace,
                        external_id=item.external_id,
                        title=item.title,
                        price=item.price,
                        currency=item.currency,
                        shop_name=item.shop_name,
                        review_count=item.review_count,
                        rating=item.rating,
                        url=item.url,
                        image_url=item.image_url,
                        is_personalized=item.is_personalized,
                        is_digital=item.is_digital,
                        shipping_price=item.shipping_price,
                        processing_time=item.processing_time,
                    )
                )
                saved += 1
        self.session.commit()
        return saved

    def _get_or_create_shop(self, item: MarketplaceListing, marketplace: str) -> Shop:
        shop = self.session.query(Shop).filter_by(marketplace=marketplace, shop_name=item.shop_name).first()
        if shop:
            shop.rating = max(shop.rating, item.rating)
            shop.review_count = max(shop.review_count, item.review_count)
            shop.last_seen_at = datetime.utcnow()
            return shop
        shop = Shop(marketplace=marketplace, shop_name=item.shop_name, rating=item.rating, review_count=item.review_count)
        self.session.add(shop)
        self.session.flush()
        return shop

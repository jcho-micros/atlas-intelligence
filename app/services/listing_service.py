from datetime import datetime

from app.connectors.base import MarketplaceListing
from app.database.models import Keyword, Listing, Shop


class ListingService:
    def __init__(self, session):
        self.session = session

    def save_listings(
        self,
        keyword: Keyword,
        marketplace: str,
        listings: list[MarketplaceListing],
    ) -> int:
        saved = 0

        for item in listings:
            shop = self._get_or_create_shop(item, marketplace)

            existing = (
                self.session.query(Listing)
                .filter_by(
                    keyword_id=keyword.id,
                    marketplace=marketplace,
                    external_id=item.external_id,
                )
                .first()
            )

            if existing:
                self._update_listing(existing, item, shop.id)
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
                        num_favorers=item.num_favorers,
                        views=item.views,
                        quantity=item.quantity,
                        tags=item.tags,
                        materials=item.materials,
                        processing_min=item.processing_min,
                        processing_max=item.processing_max,
                        created_timestamp=item.created_timestamp,
                        updated_timestamp=item.updated_timestamp,
                    )
                )
                saved += 1

        self.session.commit()
        return saved

    def _update_listing(
        self,
        listing: Listing,
        item: MarketplaceListing,
        shop_id: int,
    ) -> None:
        listing.shop_id = shop_id
        listing.title = item.title
        listing.price = item.price
        listing.currency = item.currency
        listing.shop_name = item.shop_name
        listing.review_count = item.review_count
        listing.rating = item.rating
        listing.url = item.url
        listing.image_url = item.image_url
        listing.is_personalized = item.is_personalized
        listing.is_digital = item.is_digital
        listing.shipping_price = item.shipping_price
        listing.processing_time = item.processing_time
        listing.num_favorers = item.num_favorers
        listing.views = item.views
        listing.quantity = item.quantity
        listing.tags = item.tags
        listing.materials = item.materials
        listing.processing_min = item.processing_min
        listing.processing_max = item.processing_max
        listing.created_timestamp = item.created_timestamp
        listing.updated_timestamp = item.updated_timestamp
        listing.last_seen_at = datetime.utcnow()

    def _get_or_create_shop(self, item: MarketplaceListing, marketplace: str) -> Shop:
        shop = (
            self.session.query(Shop)
            .filter_by(marketplace=marketplace, shop_name=item.shop_name)
            .first()
        )

        if shop:
            shop.rating = max(shop.rating, item.rating)
            shop.review_count = max(shop.review_count, item.review_count)
            shop.last_seen_at = datetime.utcnow()
            return shop

        shop = Shop(
            marketplace=marketplace,
            shop_name=item.shop_name,
            rating=item.rating,
            review_count=item.review_count,
        )
        self.session.add(shop)
        self.session.flush()
        return shop
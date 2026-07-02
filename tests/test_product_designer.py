from app.ai.product_designer import ProductDesigner


def test_product_designer_generates_structured_brief():
    opportunity = {
        "keyword": "baseball lineup board",
        "avg_price": 59.43,
        "avg_views": 3384,
        "avg_favorites": 47,
        "listings": 25,
        "personalized_count": 11,
        "digital_count": 8,
    }
    listings = [{"tags": "baseball|coach gift|lineup board", "title": "Custom lineup board"}]

    draft = ProductDesigner().design(opportunity, listings)

    assert draft.product_name
    assert draft.etsy_title
    assert draft.etsy_tags
    assert len(draft.etsy_tags) <= 13
    assert draft.price_min > 0
    assert draft.price_max >= draft.price_min

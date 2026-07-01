import pandas as pd
import streamlit as st

from app.database.manager import DatabaseManager
from app.database.models import Keyword, Listing, Opportunity, Project, ResearchRun, Shop
from app.utils.config import get_db_path, load_config


st.set_page_config(page_title="Atlas Intelligence", layout="wide")
st.title("Atlas Intelligence")
st.caption("Local-first commerce intelligence platform")

config = load_config()
db = DatabaseManager(get_db_path(config))
db.initialize()

with db.get_session() as session:
    cols = st.columns(5)
    cols[0].metric("Projects", session.query(Project).count())
    cols[1].metric("Keywords", session.query(Keyword).count())
    cols[2].metric("Listings", session.query(Listing).count())
    cols[3].metric("Shops", session.query(Shop).count())
    cols[4].metric("Runs", session.query(ResearchRun).count())

    st.subheader("Opportunities")
    rows = (
        session.query(Opportunity, Keyword)
        .join(Keyword, Opportunity.keyword_id == Keyword.id)
        .order_by(Opportunity.score.desc())
        .all()
    )
    data = [
        {
            "keyword": kw.keyword,
            "score": opp.score,
            "recommendation": opp.recommendation,
            "avg_price": opp.avg_price,
            "median_price": opp.median_price,
            "listings": opp.listing_count,
            "notes": opp.notes,
        }
        for opp, kw in rows
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

    st.subheader("Latest Listings")
    listings = session.query(Listing).order_by(Listing.last_seen_at.desc()).limit(100).all()
    listing_data = [
        {
            "title": item.title,
            "price": item.price,
            "shop": item.shop_name,
            "marketplace": item.marketplace,
            "personalized": item.is_personalized,
            "digital": item.is_digital,
            "url": item.url,
        }
        for item in listings
    ]
    st.dataframe(pd.DataFrame(listing_data), use_container_width=True)

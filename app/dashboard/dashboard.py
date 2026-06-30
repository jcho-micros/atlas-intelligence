from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from app.utils.config import load_config, get_db_path

st.set_page_config(page_title="Atlas Intelligence", layout="wide")
st.title("Atlas Intelligence")
st.caption("Local commerce research dashboard")

config = load_config()
db_path = get_db_path(config)

if not Path(db_path).exists():
    st.warning("Database not found yet. Run `python main.py` first.")
    st.stop()

engine = create_engine(f"sqlite:///{db_path}")

opportunities = pd.read_sql_query(
    """
    SELECT k.keyword, k.category, k.priority, o.score, o.recommendation,
           o.avg_price, o.listing_count, o.demand_score, o.competition_score,
           o.profit_score, o.personalization_score, o.confidence_score, o.notes, o.updated_at
    FROM opportunities o
    JOIN keywords k ON k.id = o.keyword_id
    ORDER BY o.score DESC
    """,
    engine,
)
listings = pd.read_sql_query(
    """
    SELECT k.keyword, l.marketplace, l.title, l.price, l.shop_name,
           l.review_count, l.rating, l.is_personalized, l.is_digital, l.url
    FROM listings l
    JOIN keywords k ON k.id = l.keyword_id
    ORDER BY k.keyword, l.price DESC
    """,
    engine,
)
runs = pd.read_sql_query(
    """
    SELECT k.keyword, r.connector, r.status, r.listings_found, r.error_message,
           r.started_at, r.finished_at
    FROM research_runs r
    JOIN keywords k ON k.id = r.keyword_id
    ORDER BY r.started_at DESC
    LIMIT 100
    """,
    engine,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Opportunities", len(opportunities))
c2.metric("Listings", len(listings))
c3.metric("Avg Score", round(opportunities["score"].mean(), 1) if not opportunities.empty else 0)
c4.metric("Research Runs", len(runs))

st.subheader("Top Opportunities")
st.dataframe(opportunities, use_container_width=True, hide_index=True)

st.subheader("Opportunity Scores")
if not opportunities.empty:
    st.bar_chart(opportunities.set_index("keyword")["score"])

st.subheader("Listings Explorer")
keyword_options = ["All"] + sorted(listings["keyword"].unique().tolist()) if not listings.empty else ["All"]
selected = st.selectbox("Keyword", keyword_options)
filtered = listings if selected == "All" else listings[listings["keyword"] == selected]
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.subheader("Research Runs")
st.dataframe(runs, use_container_width=True, hide_index=True)

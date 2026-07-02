import json

import pandas as pd
import plotly.express as px
import streamlit as st

from app.analytics import queries
from app.analytics.insights import build_opportunity_insight, opportunity_badges, suggested_price_range
from app.database.manager import DatabaseManager
from app.services.ceo_workspace_service import CEOWorkspaceService
from app.services.launch_plan_service import LaunchPlanService
from app.services.product_idea_service import ProductIdeaService
from app.utils.settings import Settings

st.set_page_config(page_title="Atlas Intelligence", layout="wide")


@st.cache_resource
def db_manager():
    db = DatabaseManager(Settings.DB_PATH)
    db.initialize()
    return db


def as_currency(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def as_int(value) -> str:
    try:
        return f"{int(round(float(value))):,}"
    except Exception:
        return "0"


def short_title(title: str, max_len: int = 92) -> str:
    title = str(title or "")
    return title if len(title) <= max_len else title[: max_len - 3] + "..."


def _split_pipe(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


def render_metric_row(row: pd.Series) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Score", round(float(row.get("score") or 0), 2))
    c2.metric("Recommendation", str(row.get("recommendation") or "WAIT"))
    c3.metric("Avg Price", as_currency(row.get("avg_price") or 0))
    c4.metric("Avg Views", as_int(row.get("avg_views") or 0))
    c5.metric("Avg Favorites", as_int(row.get("avg_favorites") or 0))


def render_opportunity_card(row: pd.Series) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.subheader(str(row["keyword"]).title())
            st.caption(build_opportunity_insight(row))
            badges = opportunity_badges(row)
            if badges:
                st.write(" ".join([f"`{badge}`" for badge in badges]))
        with right:
            st.metric("Score", round(float(row.get("score") or 0), 2))
            st.metric("Action", str(row.get("recommendation") or "WAIT"))

        render_metric_row(row)
        details = st.columns(4)
        details[0].metric("Suggested Price", suggested_price_range(float(row.get("avg_price") or 0)))
        details[1].metric("Listings", as_int(row.get("listings") or 0))
        details[2].metric("Personalized", as_int(row.get("personalized_count") or 0))
        details[3].metric("Digital", as_int(row.get("digital_count") or 0))


def render_listing_card(row: pd.Series) -> None:
    with st.container(border=True):
        image_url = str(row.get("image_url") or "")
        if image_url:
            st.image(image_url, use_container_width=True)
        st.markdown(f"**{short_title(row.get('title'))}**")
        st.caption(str(row.get("shop") or "Unknown"))
        m1, m2, m3 = st.columns(3)
        m1.metric("Price", as_currency(row.get("price") or 0))
        m2.metric("Views", as_int(row.get("views") or 0))
        m3.metric("Favorites", as_int(row.get("favorites") or 0))
        badges = []
        if bool(row.get("personalized")):
            badges.append("Personalized")
        if bool(row.get("digital")):
            badges.append("Digital")
        if badges:
            st.write(" ".join([f"`{badge}`" for badge in badges]))
        url = str(row.get("url") or "")
        if url:
            st.link_button("Open on Etsy", url)


def render_product_idea(idea) -> None:
    if idea is None:
        st.info("No product idea generated yet for this opportunity.")
        return

    with st.container(border=True):
        top_left, top_right = st.columns([3, 1])
        with top_left:
            st.subheader(idea.product_name)
            st.caption(idea.rationale)
        with top_right:
            st.metric("Confidence", f"{idea.confidence}%")
            st.metric("Suggested Price", f"${idea.suggested_price_min:.2f} - ${idea.suggested_price_max:.2f}")

        st.markdown("**Target customer**")
        st.write(idea.target_customer)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Materials**")
            for item in _split_pipe(idea.materials):
                st.write(f"- {item}")
        with c2:
            st.markdown("**Features**")
            for item in _split_pipe(idea.features):
                st.write(f"- {item}")
        with c3:
            st.markdown("**Differentiators**")
            for item in _split_pipe(idea.differentiators):
                st.write(f"- {item}")

        st.markdown("**Etsy title**")
        st.code(idea.etsy_title, language="text")
        st.markdown("**Etsy tags**")
        st.write(" ".join([f"`{tag}`" for tag in _split_pipe(idea.etsy_tags)]))
        st.markdown("**Listing description draft**")
        st.text_area("Description", idea.etsy_description, height=220, label_visibility="collapsed")
        st.markdown("**Image prompt**")
        st.text_area("Image prompt", idea.image_prompt, height=120, label_visibility="collapsed")
        st.markdown("**FAQ**")
        for item in _split_pipe(idea.faq):
            st.write(f"- {item}")


def _render_agent_output(title: str, payload_json: str) -> None:
    try:
        payload = json.loads(payload_json or "{}")
    except Exception:
        payload = {}

    with st.container(border=True):
        st.subheader(title)
        st.write(payload.get("summary", "No summary available."))
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Recommendations**")
            for item in payload.get("recommendations", []):
                st.write(f"- {item}")
        with c2:
            st.markdown("**Risks**")
            for item in payload.get("risks", []):
                st.write(f"- {item}")
        with c3:
            st.markdown("**Next steps**")
            for item in payload.get("next_steps", []):
                st.write(f"- {item}")


def render_launch_plan(plan) -> None:
    if plan is None:
        st.info("No launch plan generated yet. Generate an agent-managed plan from this opportunity.")
        return

    st.success("Agent launch plan is ready.")
    st.caption(f"Status: {plan.status} | Created: {plan.created_at}")
    _render_agent_output("Manufacturing Agent", plan.manufacturing_json)
    _render_agent_output("Logistics Agent", plan.logistics_json)
    _render_agent_output("Finance Agent", plan.finance_json)
    _render_agent_output("Customer Success Agent", plan.customer_service_json)
    _render_agent_output("Accounting Agent", plan.accounting_json)
    st.subheader("CEO Agent Next Actions")
    for item in _split_pipe(plan.next_actions):
        st.write(f"- {item}")


def render_ceo_project(project: pd.Series) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.subheader(project["project_name"])
            st.caption(project["summary"])
            st.progress(int(project["readiness_score"]) / 100, text=f"Launch readiness: {int(project['readiness_score'])}%")
        with right:
            st.metric("Stage", str(project["stage"]).replace("_", " ").title())
            st.metric("Status", str(project["status"]).title())
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Research", project["research_status"])
        c2.metric("Product", project["product_status"])
        c3.metric("Mfg", project["manufacturing_status"])
        c4.metric("Finance", project["finance_status"])
        c5.metric("Marketing", project["marketing_status"])
        c6.metric("Launch", project["launch_status"])


db = db_manager()
engine = db.engine
opps = queries.opportunity_overview(engine)
listings = queries.listing_explorer(engine)
shops = queries.shop_intelligence(engine)
trends = queries.keyword_trends(engine)
runs = queries.research_runs(engine)
tags = queries.top_tags(engine)
projects_df = queries.product_projects(engine)
all_tasks_df = queries.agent_tasks(engine)
all_events_df = queries.agent_events(engine)

st.title("Atlas Intelligence")
st.caption("Local-first commerce intelligence platform")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Keywords", len(opps))
k2.metric("Listings", len(listings))
k3.metric("Shops", len(shops))
k4.metric("Runs", len(runs))
k5.metric("Snapshots", len(trends))

k6, k7, k8, k9 = st.columns(4)
k6.metric("Avg Opportunity Score", round(opps["score"].mean(), 1) if not opps.empty else 0)
k7.metric("Avg Listing Price", as_currency(listings["price"].mean()) if not listings.empty else "$0.00")
k8.metric("Avg Views", as_int(listings["views"].mean()) if not listings.empty else "0")
k9.metric("Avg Favorites", as_int(listings["favorites"].mean()) if not listings.empty else "0")

st.divider()

tabs = st.tabs([
    "CEO Workspace",
    "Overview",
    "Opportunity Workspace",
    "AI Product Designer",
    "Agent Command Center",
    "Listings Gallery",
    "Shop Intelligence",
    "Trends",
    "Research Runs",
])

with tabs[0]:
    st.header("CEO Workspace")
    st.caption("Run Atlas like a product business: projects, agent tasks, readiness, and daily brief.")
    with db.get_session() as session:
        ceo_service = CEOWorkspaceService(session)
        brief = ceo_service.daily_brief()

    with st.container(border=True):
        st.subheader("Daily Brief")
        st.write(brief["headline"])
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Active Projects", brief["projects"])
        b2.metric("Open Agent Tasks", brief["open_tasks"])
        b3.metric("Launch Ready", brief["launch_ready"])
        b4.metric("Needs Attention", brief["needs_attention"])

    if opps.empty:
        st.info("Run research first with `python main.py`.")
    else:
        st.subheader("Create Product Project")
        keyword = st.selectbox("Select opportunity", opps["keyword"].tolist(), key="ceo_create_project_keyword")
        selected = opps[opps["keyword"] == keyword].iloc[0]
        with st.container(border=True):
            st.subheader(str(selected["keyword"]).title())
            render_metric_row(selected)
            st.write(build_opportunity_insight(selected))
        if st.button("Create / Refresh Product Project", type="primary"):
            with db.get_session() as session:
                ceo_service = CEOWorkspaceService(session)
                project = ceo_service.create_project_from_keyword(keyword)
            st.success(f"Created project: {project.project_name}")
            st.rerun()

    st.subheader("Active Product Projects")
    if projects_df.empty:
        st.info("No product projects yet. Create one from an opportunity above.")
    else:
        for _, project in projects_df.iterrows():
            render_ceo_project(project)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Agent Task Queue")
        if all_tasks_df.empty:
            st.info("No agent tasks yet.")
        else:
            st.dataframe(all_tasks_df[["project_name", "agent_name", "task_name", "status", "priority"]], use_container_width=True, hide_index=True)
    with c2:
        st.subheader("Agent Activity Timeline")
        if all_events_df.empty:
            st.info("No agent activity yet.")
        else:
            st.dataframe(all_events_df[["created_at", "agent_name", "event_type", "message"]], use_container_width=True, hide_index=True)

with tabs[1]:
    st.header("Executive Overview")
    if opps.empty:
        st.info("Run research first with `python main.py`.")
    else:
        best = opps.iloc[0]
        with st.container(border=True):
            st.subheader(f"Top Opportunity: {str(best['keyword']).title()}")
            render_metric_row(best)
            st.write(build_opportunity_insight(best))
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(opps, x="keyword", y="score", title="Opportunity Scores")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Top Tags")
            st.dataframe(tags.head(15), use_container_width=True, hide_index=True)
        st.subheader("Opportunity Table")
        visible_cols = ["keyword", "score", "recommendation", "avg_price", "median_price", "listings", "avg_views", "avg_favorites", "personalized_count", "digital_count"]
        st.dataframe(opps[visible_cols], use_container_width=True, hide_index=True)

with tabs[2]:
    st.header("Opportunity Workspace")
    if opps.empty:
        st.info("No opportunities yet.")
    else:
        keyword = st.selectbox("Select opportunity", opps["keyword"].tolist())
        selected = opps[opps["keyword"] == keyword].iloc[0]
        render_opportunity_card(selected)
        st.subheader("Top Listings for This Opportunity")
        keyword_listings = queries.top_listings_for_keyword(engine, keyword, limit=20)
        if keyword_listings.empty:
            st.info("No listings found for this keyword.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                fig = px.scatter(keyword_listings, x="views", y="favorites", size="price", hover_data=["title", "shop"], title="Views vs Favorites")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig = px.histogram(keyword_listings, x="price", nbins=12, title="Price Distribution")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(keyword_listings[["title", "price", "shop", "views", "favorites", "personalized", "digital", "url"]], use_container_width=True, hide_index=True, column_config={"url": st.column_config.LinkColumn("Etsy")})

with tabs[3]:
    st.header("AI Product Designer")
    st.caption("Turn a researched opportunity into a product concept, Etsy listing draft, tags, FAQ, and image prompt.")
    if opps.empty:
        st.info("Run research first with `python main.py`.")
    else:
        keyword = st.selectbox("Select opportunity", opps["keyword"].tolist(), key="product_designer_keyword")
        selected = opps[opps["keyword"] == keyword].iloc[0]
        with st.container(border=True):
            st.subheader(str(selected["keyword"]).title())
            render_metric_row(selected)
            st.write(build_opportunity_insight(selected))
        with db.get_session() as session:
            service = ProductIdeaService(session)
            current_idea = service.latest_for_keyword(keyword)
            if st.button("Generate Product Idea", type="primary"):
                service.generate_for_keyword(keyword)
                current_idea = service.latest_for_keyword(keyword)
                st.success("Generated product idea.")
            render_product_idea(current_idea)

with tabs[4]:
    st.header("Agent Command Center")
    st.caption("Manage the business departments needed to turn a product idea into a sellable product.")
    if opps.empty:
        st.info("Run research first with `python main.py`.")
    else:
        keyword = st.selectbox("Select opportunity", opps["keyword"].tolist(), key="agent_center_keyword")
        selected = opps[opps["keyword"] == keyword].iloc[0]
        with st.container(border=True):
            st.subheader(str(selected["keyword"]).title())
            render_metric_row(selected)
            st.write(build_opportunity_insight(selected))
        with db.get_session() as session:
            service = LaunchPlanService(session)
            plan = service.latest_for_keyword(keyword)
            if st.button("Generate Agent Launch Plan", type="primary"):
                plan = service.generate_for_keyword(keyword)
            render_launch_plan(plan)

with tabs[5]:
    st.header("Listings Gallery")
    if listings.empty:
        st.info("No listings yet.")
    else:
        keyword_options = ["All"] + sorted(listings["keyword"].dropna().unique().tolist())
        selected_keyword = st.selectbox("Keyword filter", keyword_options)
        filtered = listings if selected_keyword == "All" else listings[listings["keyword"] == selected_keyword]
        min_views = st.slider("Minimum views", 0, int(max(filtered["views"].max(), 1)), 0)
        filtered = filtered[filtered["views"] >= min_views]
        st.caption(f"Showing {len(filtered)} listings")
        display_mode = st.radio("View", ["Gallery", "Table"], horizontal=True)
        if display_mode == "Gallery":
            for start in range(0, min(len(filtered), 30), 3):
                cols = st.columns(3)
                for col, (_, row) in zip(cols, filtered.iloc[start : start + 3].iterrows()):
                    with col:
                        render_listing_card(row)
        else:
            st.dataframe(filtered[["keyword", "title", "price", "shop", "views", "favorites", "personalized", "digital", "tags", "url"]], use_container_width=True, hide_index=True, column_config={"url": st.column_config.LinkColumn("Etsy")})

with tabs[6]:
    st.header("Shop Intelligence")
    if shops.empty:
        st.info("No shop data yet.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(shops.head(20), x="shop", y="avg_views", title="Top Shops by Average Views")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(shops.head(20), x="shop", y="avg_favorites", title="Top Shops by Average Favorites")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(shops, use_container_width=True, hide_index=True)

with tabs[7]:
    st.header("Trend Intelligence")
    if trends.empty:
        st.info("Run research multiple times to build trend history.")
    else:
        metric = st.selectbox("Metric", ["opportunity_score", "avg_price", "avg_views", "avg_favorites", "listing_count"])
        fig = px.line(trends, x="captured_at", y=metric, color="keyword", markers=True, title=f"{metric} Over Time")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(trends, use_container_width=True, hide_index=True)

with tabs[8]:
    st.header("Research Runs")
    st.dataframe(runs, use_container_width=True, hide_index=True)

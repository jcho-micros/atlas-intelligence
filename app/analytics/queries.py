import pandas as pd
from sqlalchemy import text


def read_sql(engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def opportunity_overview(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT k.keyword, o.score, o.recommendation, o.avg_price, o.median_price,
               o.listing_count AS listings,
               ks.avg_views, ks.avg_favorites, ks.personalized_count, ks.digital_count,
               o.demand_score, o.competition_score, o.profit_score, o.personalization_score,
               o.confidence_score, o.notes
        FROM opportunities o
        JOIN keywords k ON k.id = o.keyword_id
        LEFT JOIN keyword_snapshots ks ON ks.keyword_id = k.id
        WHERE ks.id IS NULL OR ks.id = (
            SELECT MAX(id) FROM keyword_snapshots ks2 WHERE ks2.keyword_id = k.id
        )
        ORDER BY o.score DESC
    """)


def listing_explorer(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT k.keyword, l.title, l.price, l.currency, l.shop_name AS shop, l.marketplace,
               l.views, l.num_favorers AS favorites, l.quantity,
               l.is_personalized AS personalized, l.is_digital AS digital,
               l.processing_time, l.tags, l.image_url, l.url
        FROM listings l
        JOIN keywords k ON k.id = l.keyword_id
        ORDER BY l.views DESC, l.num_favorers DESC
    """)


def shop_intelligence(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT l.shop_name AS shop, COUNT(*) AS listings,
               ROUND(AVG(l.price), 2) AS avg_price,
               ROUND(AVG(l.views), 0) AS avg_views,
               ROUND(AVG(l.num_favorers), 0) AS avg_favorites,
               SUM(l.views) AS total_views,
               SUM(l.num_favorers) AS total_favorites,
               SUM(CASE WHEN l.is_personalized THEN 1 ELSE 0 END) AS personalized_count,
               SUM(CASE WHEN l.is_digital THEN 1 ELSE 0 END) AS digital_count
        FROM listings l
        GROUP BY l.shop_name
        ORDER BY avg_views DESC, avg_favorites DESC
    """)


def keyword_trends(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT k.keyword, ks.captured_at, ks.opportunity_score, ks.avg_price,
               ks.avg_views, ks.avg_favorites, ks.listing_count,
               ks.personalized_count, ks.digital_count
        FROM keyword_snapshots ks
        JOIN keywords k ON k.id = ks.keyword_id
        ORDER BY ks.captured_at ASC
    """)


def research_runs(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT rr.id, k.keyword, rr.connector, rr.status, rr.listings_found,
               rr.started_at, rr.finished_at, rr.error_message
        FROM research_runs rr
        JOIN keywords k ON k.id = rr.keyword_id
        ORDER BY rr.started_at DESC
    """)


def top_tags(engine, limit: int = 30) -> pd.DataFrame:
    listings = listing_explorer(engine)
    counts: dict[str, int] = {}
    for tags in listings.get("tags", []):
        for tag in str(tags or "").split("|"):
            tag = tag.strip().lower()
            if tag:
                counts[tag] = counts.get(tag, 0) + 1
    return pd.DataFrame(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit], columns=["tag", "count"])


def top_listings_for_keyword(engine, keyword: str, limit: int = 15) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT k.keyword, l.title, l.price, l.shop_name AS shop,
               l.views, l.num_favorers AS favorites, l.is_personalized AS personalized,
               l.is_digital AS digital, l.tags, l.image_url, l.url
        FROM listings l
        JOIN keywords k ON k.id = l.keyword_id
        WHERE k.keyword = :keyword
        ORDER BY l.views DESC, l.num_favorers DESC
        LIMIT :limit
    """, {"keyword": keyword, "limit": limit})


def product_ideas(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT pi.id, k.keyword, pi.product_name, pi.target_customer,
               pi.suggested_price_min, pi.suggested_price_max, pi.confidence,
               pi.materials, pi.features, pi.differentiators,
               pi.etsy_title, pi.etsy_description, pi.etsy_tags, pi.faq,
               pi.image_prompt, pi.rationale, pi.created_at
        FROM product_ideas pi
        JOIN keywords k ON k.id = pi.keyword_id
        ORDER BY pi.created_at DESC
    """)


def product_projects(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT pp.id, k.keyword, pp.project_name, pp.status, pp.stage,
               pp.readiness_score, pp.priority,
               pp.research_status, pp.product_status, pp.manufacturing_status,
               pp.finance_status, pp.marketing_status, pp.customer_success_status,
               pp.launch_status, pp.summary, pp.created_at, pp.updated_at
        FROM product_projects pp
        JOIN keywords k ON k.id = pp.keyword_id
        ORDER BY pp.created_at DESC
    """)


def agent_tasks(engine, project_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT at.id, pp.project_name, at.agent_name, at.task_name,
               at.status, at.priority, at.output, at.created_at, at.completed_at
        FROM agent_tasks at
        JOIN product_projects pp ON pp.id = at.project_id
    """
    params = {}
    if project_id is not None:
        sql += " WHERE at.project_id = :project_id"
        params["project_id"] = project_id
    sql += " ORDER BY at.priority DESC, at.created_at DESC"
    return read_sql(engine, sql, params)


def agent_events(engine, project_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT ae.id, pp.project_name, ae.agent_name, ae.event_type,
               ae.message, ae.created_at
        FROM agent_events ae
        LEFT JOIN product_projects pp ON pp.id = ae.project_id
    """
    params = {}
    if project_id is not None:
        sql += " WHERE ae.project_id = :project_id"
        params["project_id"] = project_id
    sql += " ORDER BY ae.created_at DESC"
    return read_sql(engine, sql, params)

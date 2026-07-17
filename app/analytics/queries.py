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
        SELECT at.id, pp.project_name, at.agent_name, at.task_type, at.title,
               at.description, at.status, at.priority, at.created_at,
               at.started_at, at.completed_at
        FROM agent_tasks at
        JOIN product_projects pp ON pp.id = at.project_id
    """
    params = {}
    if project_id is not None:
        sql += " WHERE at.project_id = :project_id"
        params["project_id"] = project_id
    sql += " ORDER BY at.priority DESC, at.created_at DESC"
    return read_sql(engine, sql, params)


def candidate_projects(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT cp.id, k.keyword, cp.title, cp.summary, cp.confidence,
               cp.estimated_margin, cp.priority, cp.reason, cp.status,
               cp.created_at, cp.reviewed_at
        FROM candidate_projects cp
        LEFT JOIN keywords k ON k.id = cp.keyword_id
        ORDER BY cp.priority DESC, cp.confidence DESC, cp.created_at DESC
    """)


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


def businesses(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT b.id, b.name, b.brand_name, b.market, b.status, b.vision,
               b.confidence, b.estimated_monthly_revenue, b.estimated_margin,
               COALESCE(COUNT(DISTINCT p.id), 0) AS products,
               COALESCE(COUNT(DISTINCT pp.id), 0) AS projects,
               ROUND(COALESCE(AVG(pp.readiness_score), 0), 1) AS avg_readiness,
               b.created_at, b.updated_at
        FROM businesses b
        LEFT JOIN products p ON p.business_id = b.id
        LEFT JOIN product_projects pp ON pp.business_id = b.id
        GROUP BY b.id
        ORDER BY b.estimated_monthly_revenue DESC, b.confidence DESC
    """)


def products_for_business(engine, business_id: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT p.id, p.name, p.status, p.category, p.target_customer,
               p.suggested_price_min, p.suggested_price_max, p.confidence,
               p.summary, pp.project_name, pp.stage, pp.readiness_score,
               pp.manufacturing_status, pp.finance_status, pp.marketing_status,
               pp.launch_status, p.created_at
        FROM products p
        LEFT JOIN product_projects pp ON pp.product_id = p.id
        WHERE p.business_id = :business_id
        ORDER BY p.confidence DESC, p.created_at DESC
    """, {"business_id": business_id})


def business_metrics(engine, business_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT bm.id, b.name AS business, bm.product_count, bm.active_project_count,
               bm.avg_confidence, bm.estimated_monthly_revenue,
               bm.estimated_margin, bm.launch_readiness, bm.captured_at
        FROM business_metrics bm
        JOIN businesses b ON b.id = bm.business_id
    """
    params = {}
    if business_id is not None:
        sql += " WHERE bm.business_id = :business_id"
        params["business_id"] = business_id
    sql += " ORDER BY bm.captured_at DESC"
    return read_sql(engine, sql, params)


def business_opportunities(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT bo.id, bo.title, bo.market, bo.summary, bo.confidence,
               bo.estimated_monthly_revenue, bo.estimated_margin,
               bo.status, bo.reason, bo.created_at, bo.reviewed_at
        FROM business_opportunities bo
        ORDER BY bo.confidence DESC, bo.created_at DESC
    """)


def departments(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT d.id, d.name, d.description, COUNT(e.id) AS employees
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        GROUP BY d.id
        ORDER BY d.name
    """)


def employees(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT e.id, e.avatar_emoji, e.name, e.title,
               COALESCE(d.name, 'Unassigned') AS department,
               COALESCE(m.name, '') AS manager,
               e.status, e.current_task, e.mission, e.personality, e.goals,
               e.performance_score, e.workload, e.started_at, e.last_active_at,
               COUNT(DISTINCT s.id) AS skills_count,
               COUNT(DISTINCT t.id) AS tools_count,
               COUNT(DISTINCT msg.id) AS inbox_count
        FROM employees e
        LEFT JOIN departments d ON d.id = e.department_id
        LEFT JOIN employees m ON m.id = e.manager_id
        LEFT JOIN employee_skills s ON s.employee_id = e.id
        LEFT JOIN employee_tools t ON t.employee_id = e.id
        LEFT JOIN employee_messages msg ON msg.recipient_id = e.id AND msg.status = 'unread'
        GROUP BY e.id
        ORDER BY d.name, e.title
    """)


def employee_skills(engine, employee_id: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT skill, proficiency, created_at
        FROM employee_skills
        WHERE employee_id = :employee_id
        ORDER BY skill
    """, {"employee_id": employee_id})


def employee_tools(engine, employee_id: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT tool_name, access_level, created_at
        FROM employee_tools
        WHERE employee_id = :employee_id
        ORDER BY tool_name
    """, {"employee_id": employee_id})


def employee_memories(engine, employee_id: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT memory_type, content, importance, created_at, last_used_at
        FROM employee_memories
        WHERE employee_id = :employee_id
        ORDER BY importance DESC, created_at DESC
    """, {"employee_id": employee_id})


def employee_messages(engine, employee_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT em.id,
               COALESCE(sender.name, 'Atlas') AS sender,
               COALESCE(recipient.name, 'Atlas') AS recipient,
               em.subject, em.body, em.status, em.created_at, em.read_at
        FROM employee_messages em
        LEFT JOIN employees sender ON sender.id = em.sender_id
        LEFT JOIN employees recipient ON recipient.id = em.recipient_id
    """
    params = {}
    if employee_id is not None:
        sql += " WHERE em.sender_id = :employee_id OR em.recipient_id = :employee_id"
        params["employee_id"] = employee_id
    sql += " ORDER BY em.created_at DESC"
    return read_sql(engine, sql, params)


def employee_kpis(engine, employee_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT e.name, ek.metric_name, ek.metric_value, ek.target_value, ek.captured_at
        FROM employee_kpis ek
        JOIN employees e ON e.id = ek.employee_id
    """
    params = {}
    if employee_id is not None:
        sql += " WHERE ek.employee_id = :employee_id"
        params["employee_id"] = employee_id
    sql += " ORDER BY ek.captured_at DESC"
    return read_sql(engine, sql, params)


def employee_goals(engine, employee_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT eg.id, e.name, e.title, eg.goal_type, eg.title AS goal_title,
               eg.description, eg.status, eg.priority, eg.progress,
               eg.created_at, eg.updated_at
        FROM employee_goals eg
        JOIN employees e ON e.id = eg.employee_id
    """
    params = {}
    if employee_id is not None:
        sql += " WHERE eg.employee_id = :employee_id"
        params["employee_id"] = employee_id
    sql += " ORDER BY eg.priority DESC, eg.created_at DESC"
    return read_sql(engine, sql, params)


def employee_thoughts(engine, employee_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT et.id, e.name, e.title, et.thought_type, et.content,
               et.confidence, et.created_at
        FROM employee_thoughts et
        JOIN employees e ON e.id = et.employee_id
    """
    params = {}
    if employee_id is not None:
        sql += " WHERE et.employee_id = :employee_id"
        params["employee_id"] = employee_id
    sql += " ORDER BY et.created_at DESC"
    return read_sql(engine, sql, params)


def employee_decisions(engine, employee_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT ed.id, e.name, e.title AS employee_title, ed.decision_type,
               ed.title, ed.reasoning, ed.outcome, ed.confidence, ed.created_at
        FROM employee_decisions ed
        JOIN employees e ON e.id = ed.employee_id
    """
    params = {}
    if employee_id is not None:
        sql += " WHERE ed.employee_id = :employee_id"
        params["employee_id"] = employee_id
    sql += " ORDER BY ed.created_at DESC"
    return read_sql(engine, sql, params)


def employee_reflections(engine, employee_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT er.id, e.name, er.content, er.lesson, er.importance, er.created_at
        FROM employee_reflections er
        JOIN employees e ON e.id = er.employee_id
    """
    params = {}
    if employee_id is not None:
        sql += " WHERE er.employee_id = :employee_id"
        params["employee_id"] = employee_id
    sql += " ORDER BY er.importance DESC, er.created_at DESC"
    return read_sql(engine, sql, params)


def vendors(engine) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT v.id, v.name, v.category, v.relationship_status, v.location,
               v.website, v.contact_name, v.contact_email, v.capabilities,
               v.notes, v.trust_score, v.quality_score, v.communication_score,
               v.pricing_score, v.delivery_score, v.average_lead_time_days,
               v.minimum_order_quantity, v.average_margin, v.projects_completed,
               v.risk_level, v.recommendation, v.created_at, v.updated_at,
               COUNT(DISTINCT q.id) AS quote_count,
               COUNT(DISTINCT ev.id) AS event_count
        FROM vendors v
        LEFT JOIN vendor_quotes q ON q.vendor_id = v.id
        LEFT JOIN vendor_events ev ON ev.vendor_id = v.id
        GROUP BY v.id
        ORDER BY v.trust_score DESC, v.average_margin DESC
    """)


def vendor_quotes(engine, vendor_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT q.id, v.name AS vendor, q.product_name, q.unit_cost,
               q.shipping_cost, q.landed_cost, q.moq, q.lead_time_days,
               q.quote_status, q.notes, q.created_at
        FROM vendor_quotes q
        JOIN vendors v ON v.id = q.vendor_id
    """
    params = {}
    if vendor_id is not None:
        sql += " WHERE q.vendor_id = :vendor_id"
        params["vendor_id"] = vendor_id
    sql += " ORDER BY q.landed_cost ASC, q.lead_time_days ASC"
    return read_sql(engine, sql, params)


def vendor_events(engine, vendor_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT ev.id, v.name AS vendor, ev.event_type, ev.message,
               ev.actor, ev.created_at
        FROM vendor_events ev
        JOIN vendors v ON v.id = ev.vendor_id
    """
    params = {}
    if vendor_id is not None:
        sql += " WHERE ev.vendor_id = :vendor_id"
        params["vendor_id"] = vendor_id
    sql += " ORDER BY ev.created_at DESC"
    return read_sql(engine, sql, params)


def vendor_contacts(engine, vendor_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT vc.id, v.name AS vendor, vc.name, vc.title, vc.email,
               vc.phone, vc.is_primary, vc.created_at
        FROM vendor_contacts vc
        JOIN vendors v ON v.id = vc.vendor_id
    """
    params = {}
    if vendor_id is not None:
        sql += " WHERE vc.vendor_id = :vendor_id"
        params["vendor_id"] = vendor_id
    sql += " ORDER BY vc.is_primary DESC, vc.name"
    return read_sql(engine, sql, params)


def finance_analyses(engine, business_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT fa.id, b.name AS business, pp.project_name,
               fa.scenario_name, fa.selling_price, fa.unit_cost,
               fa.packaging_cost, fa.outbound_shipping_cost,
               fa.marketplace_fee, fa.payment_fee, fa.ad_cost, fa.reserve_cost,
               fa.total_variable_cost, fa.gross_profit, fa.gross_margin,
               fa.break_even_units, fa.target_price, fa.monthly_units_estimate,
               fa.monthly_profit_estimate, fa.approval_status,
               fa.recommendation, fa.assumptions, fa.created_at, fa.updated_at
        FROM finance_analyses fa
        LEFT JOIN businesses b ON b.id = fa.business_id
        LEFT JOIN product_projects pp ON pp.id = fa.project_id
    """
    params = {}
    if business_id is not None:
        sql += " WHERE fa.business_id = :business_id"
        params["business_id"] = business_id
    sql += " ORDER BY fa.gross_margin DESC, fa.monthly_profit_estimate DESC"
    return read_sql(engine, sql, params)


def finance_scenarios(engine, analysis_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT fs.id, fa.id AS analysis_id, pp.project_name,
               fs.name, fs.selling_price, fs.unit_cost, fs.gross_margin,
               fs.monthly_units, fs.monthly_profit, fs.risk_level,
               fs.notes, fs.created_at
        FROM finance_scenarios fs
        JOIN finance_analyses fa ON fa.id = fs.analysis_id
        LEFT JOIN product_projects pp ON pp.id = fa.project_id
    """
    params = {}
    if analysis_id is not None:
        sql += " WHERE fs.analysis_id = :analysis_id"
        params["analysis_id"] = analysis_id
    sql += " ORDER BY fs.monthly_profit DESC, fs.gross_margin DESC"
    return read_sql(engine, sql, params)


def finance_events(engine, business_id: int | None = None) -> pd.DataFrame:
    sql = """
        SELECT fe.id, b.name AS business, pp.project_name,
               fe.event_type, fe.message, fe.actor, fe.created_at
        FROM finance_events fe
        JOIN finance_analyses fa ON fa.id = fe.analysis_id
        LEFT JOIN businesses b ON b.id = fa.business_id
        LEFT JOIN product_projects pp ON pp.id = fa.project_id
    """
    params = {}
    if business_id is not None:
        sql += " WHERE fa.business_id = :business_id"
        params["business_id"] = business_id
    sql += " ORDER BY fe.created_at DESC"
    return read_sql(engine, sql, params)


def design_concepts(engine, project_id=None):
    sql = """
    SELECT dc.id, dc.project_id, pp.project_name, dc.designer_name, dc.concept_name,
           dc.concept_version, dc.design_rationale, dc.materials, dc.dimensions,
           dc.target_customer, dc.suggested_price, dc.image_prompt, dc.mockup_svg,
           dc.designer_notes, dc.status, dc.created_at, dc.reviewed_at
    FROM design_concepts dc JOIN product_projects pp ON pp.id = dc.project_id
    """
    params = {}
    if project_id is not None:
        sql += " WHERE dc.project_id = :project_id"
        params["project_id"] = project_id
    sql += " ORDER BY dc.created_at DESC, dc.id DESC"
    return read_sql(engine, sql, params)


def sourcing_assignments(engine):
    return read_sql(engine, """
    SELECT sa.id, sa.project_id, pp.project_name, sa.owner_name, sa.title,
           sa.requirements, sa.status, sa.created_at, sa.completed_at
    FROM sourcing_assignments sa JOIN product_projects pp ON pp.id = sa.project_id
    ORDER BY sa.created_at DESC
    """)


def supplier_recommendations(engine):
    return read_sql(engine, """
    SELECT sr.id, sr.project_id, pp.project_name, sr.supplier_name, sr.confidence,
           sr.reason, sr.landed_cost, sr.lead_time_days, sr.moq, sr.status,
           sr.created_at, sr.reviewed_at
    FROM supplier_recommendations sr JOIN product_projects pp ON pp.id = sr.project_id
    ORDER BY sr.created_at DESC
    """)

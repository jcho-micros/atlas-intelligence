import base64
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from app.analytics import queries
from app.analytics.insights import build_opportunity_insight, opportunity_badges, suggested_price_range
from app.database.manager import DatabaseManager
from app.employees.employee_service import EmployeeService
from app.employees.runtime_service import EmployeeRuntimeService
from app.employees.workflow_service import EmployeeWorkflowService
from app.services.ceo_workspace_service import CEOWorkspaceService
from app.services.launch_plan_service import LaunchPlanService
from app.services.product_idea_service import ProductIdeaService
from app.services.vendor_intelligence_service import VendorIntelligenceService
from app.services.finance_intelligence_service import FinanceIntelligenceService
from app.services.design_manufacturing_service import DesignManufacturingService
from app.dashboard.company_page import render_company_management
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




def humanize_employee_action(action: str) -> str:
    mapping = {
        "review_inbox": "Reviewing inbox and priorities",
        "reflect": "Reflecting and updating memory",
        "assigned_work": "Assigning work to the team",
        "start_task": "Starting assigned work",
        "complete_task": "Completing assigned work",
        "message_sent": "Sending an internal update",
    }
    return mapping.get(str(action or "").strip(), str(action or "Working").replace("_", " ").title())

def employee_status_badge(status: str) -> str:
    status = str(status or "available").lower()
    if status in {"working", "leading", "researching", "planning"}:
        return "🟢 Working"
    if status in {"waiting", "blocked"}:
        return "🟡 Waiting"
    return "⚪ Available"

def employee_current_thought(employee) -> str:
    name = str(employee.get("name") or "This employee")
    title = str(employee.get("title") or "employee")
    task = str(employee.get("current_task") or "reviewing priorities")
    department = str(employee.get("department") or "the company")
    if "Manufacturing" in title or department == "Manufacturing":
        return f"I'm checking supplier paths and manufacturing risks before making a recommendation."
    if "Financial" in title or department == "Finance":
        return f"I'm protecting margin assumptions and waiting for cost inputs before approving launch."
    if "Marketing" in title or department == "Marketing":
        return f"I'm shaping positioning so the offer feels premium and easy to understand."
    if "Operating" in title or department == "Operations":
        return f"I'm reviewing company priorities and routing work to the right employees."
    if "Research" in title or department == "Research":
        return f"I'm looking for related opportunities that can become full product lines."
    return f"I'm {task.lower()}."

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


def vendor_status_badge(status: str) -> str:
    status = str(status or "prospect").lower()
    if status in {"preferred", "strategic"}:
        return "🟢 " + status.title()
    if status in {"backup", "prospect"}:
        return "🟡 " + status.title()
    return "⚪ " + status.title()


def vendor_recommendation_summary(row: pd.Series) -> str:
    return (
        f"Trust {round(float(row.get('trust_score') or 0), 1)} · "
        f"Margin {round(float(row.get('average_margin') or 0), 1)}% · "
        f"Lead time {int(row.get('average_lead_time_days') or 0)} days · "
        f"MOQ {int(row.get('minimum_order_quantity') or 0)}"
    )


def render_vendor_card(row: pd.Series) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.subheader(str(row.get("name") or "Vendor"))
            st.caption(f"{row.get('category')} · {row.get('location')} · {vendor_status_badge(row.get('relationship_status'))}")
            st.write(row.get("recommendation") or row.get("notes") or "No recommendation yet.")
            capabilities = _split_pipe(row.get("capabilities") or "")
            if capabilities:
                st.write(" ".join([f"`{cap}`" for cap in capabilities[:6]]))
        with right:
            st.metric("Trust", f"{round(float(row.get('trust_score') or 0), 1)}%")
            st.metric("Margin", f"{round(float(row.get('average_margin') or 0), 1)}%")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Quality", round(float(row.get("quality_score") or 0), 1))
        c2.metric("Communication", round(float(row.get("communication_score") or 0), 1))
        c3.metric("Lead Time", f"{int(row.get('average_lead_time_days') or 0)} days")
        c4.metric("MOQ", int(row.get("minimum_order_quantity") or 0))


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
with db.get_session() as session:
    EmployeeService(session).ensure_default_workforce()
    EmployeeWorkflowService(session).ensure_workflows()
    VendorIntelligenceService(session).ensure_seed_vendors()
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
candidates_df = queries.candidate_projects(engine)
businesses_df = queries.businesses(engine)
business_opps_df = queries.business_opportunities(engine)
departments_df = queries.departments(engine)
employees_df = queries.employees(engine)
employee_messages_df = queries.employee_messages(engine)
employee_kpis_df = queries.employee_kpis(engine)
employee_goals_df = queries.employee_goals(engine)
employee_thoughts_df = queries.employee_thoughts(engine)
employee_decisions_df = queries.employee_decisions(engine)
employee_reflections_df = queries.employee_reflections(engine)
vendors_df = queries.vendors(engine)
vendor_quotes_df = queries.vendor_quotes(engine)
vendor_events_df = queries.vendor_events(engine)
finance_df = queries.finance_analyses(engine)
finance_scenarios_df = queries.finance_scenarios(engine)
finance_events_df = queries.finance_events(engine)

st.title("Atlas Enterprise")
st.caption("AI-native company headquarters powered by Atlas OS")

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

k10, k11, k12 = st.columns(3)
k10.metric("Businesses", len(businesses_df))
k11.metric("Business Opportunities", len(business_opps_df))
k12.metric("Business Forecast", as_currency(businesses_df["estimated_monthly_revenue"].sum()) if not businesses_df.empty else "$0.00")

k13, k14, k15 = st.columns(3)
k13.metric("Employees", len(employees_df))
k14.metric("Employees Working", len(employees_df[employees_df["status"].isin(["working", "leading"])]) if not employees_df.empty else 0)
k15.metric("Unread Employee Messages", len(employee_messages_df[employee_messages_df["status"] == "unread"]) if not employee_messages_df.empty else 0)

k16, k17, k18 = st.columns(3)
k16.metric("Vendors", len(vendors_df))
k17.metric("Preferred Vendors", len(vendors_df[vendors_df["relationship_status"].isin(["preferred", "strategic"])]) if not vendors_df.empty else 0)
k18.metric("Avg Vendor Trust", round(vendors_df["trust_score"].mean(), 1) if not vendors_df.empty else 0)

st.divider()

NAVIGATION = {
    "🏢 Company": [
        "Headquarters",
        "Company Management",
        "Executive Office",
        "Strategy Room",
        "Portfolio Office",
        "Business Workspace",
    ],
    "👥 Workforce": [
        "People Directory",
        "Employee Office",
        "Operations Center",
        "Employee Mind",
        "Communications Center",
        "Agent Command Center",
    ],
    "📊 Intelligence": [
        "Overview",
        "Opportunity Workspace",
        "AI Product Designer",
        "Listings Gallery",
        "Shop Intelligence",
        "Trends",
        "Research Runs",
    ],
    "🎨 Design & Manufacturing": [
        "Design Studio",
        "Manufacturing Execution",
        "Design Timeline",
    ],
    "🏭 Vendor Intelligence": [
        "Vendor Workspace",
        "Vendor Directory",
        "RFQ Center",
        "Vendor Timeline",
    ],
    "💰 Finance Intelligence": [
        "Finance Workspace",
        "Unit Economics",
        "Profit Scenarios",
        "Finance Timeline",
    ],
}

st.sidebar.title("Atlas Navigation")
st.sidebar.caption("Grouped by company function")
section = st.sidebar.selectbox("Section", list(NAVIGATION.keys()))
active_page = st.sidebar.selectbox("Page", NAVIGATION[section])
st.sidebar.divider()
st.sidebar.caption("Tip: Atlas is organized like a headquarters: Company, Workforce, and Intelligence.")

if active_page == "Company Management":
    with db.get_session() as session:
        render_company_management(session)


if active_page == "Headquarters":
    st.header("Atlas Headquarters")
    st.caption("Walk into the company: employees, businesses, messages, and the work needing CEO attention.")

    avg_perf = employees_df["performance_score"].mean() if not employees_df.empty else 0
    avg_workload = employees_df["workload"].mean() if not employees_df.empty else 0
    company_health = min(100, (avg_perf * 0.7) + ((100 - avg_workload) * 0.3)) if not employees_df.empty else 0

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Company Health", f"{company_health:.1f}%")
    h2.metric("Employees", len(employees_df))
    h3.metric("Working", len(employees_df[employees_df["status"].isin(["working", "leading"])]) if not employees_df.empty else 0)
    h4.metric("Messages", len(employee_messages_df[employee_messages_df["status"] == "unread"]) if not employee_messages_df.empty else 0)

    st.subheader("Morning Brief")
    with st.container(border=True):
        st.write("Good morning John. Atlas Enterprise is online. Your AI employees are loaded, departments are active, and the company is ready for CEO decisions.")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Businesses", len(businesses_df))
        b2.metric("Candidates", len(candidates_df[candidates_df["status"] == "candidate"]) if not candidates_df.empty else 0)
        b3.metric("Open Tasks", len(all_tasks_df[~all_tasks_df["status"].isin(["complete", "completed"])]) if not all_tasks_df.empty else 0)
        b4.metric("Revenue Forecast", as_currency(businesses_df["estimated_monthly_revenue"].sum()) if not businesses_df.empty else "$0.00")

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Employees at Work")
        if employees_df.empty:
            st.info("No employees loaded yet. Run `python main.py`.")
        else:
            for _, employee in employees_df.head(8).iterrows():
                with st.container(border=True):
                    st.markdown(f"### {employee['avatar_emoji']} {employee['name']}")
                    st.caption(f"{employee['title']} · {employee['department']} · {employee_status_badge(employee.get('status'))}")
                    st.write(f"*{employee_current_thought(employee)}*")
                    st.progress(min(100, float(employee.get('workload') or 0)) / 100, text=f"Workload {round(float(employee.get('workload') or 0), 1)}%")
                    st.caption(f"Next: {employee.get('current_task') or 'Ready for assignment'}")
    with c2:
        st.subheader("Internal Messages")
        if employee_messages_df.empty:
            st.info("No employee messages yet.")
        else:
            for _, msg in employee_messages_df.head(8).iterrows():
                with st.container(border=True):
                    st.markdown(f"**{msg['sender']} → {msg['recipient']}**")
                    st.caption(f"{msg['subject']} · {msg['status']}")
                    st.write(msg["body"])

    st.subheader("Company Timeline")
    if all_events_df.empty and employee_messages_df.empty:
        st.info("No timeline events yet.")
    else:
        timeline_rows = []
        if not all_events_df.empty:
            for _, event in all_events_df.head(8).iterrows():
                timeline_rows.append({"time": event["created_at"], "actor": event["agent_name"], "event": event["event_type"], "message": event["message"]})
        if not employee_messages_df.empty:
            for _, msg in employee_messages_df.head(6).iterrows():
                timeline_rows.append({"time": msg["created_at"], "actor": msg["sender"], "event": "message_sent", "message": f"{msg['subject']} → {msg['recipient']}"})
        st.dataframe(pd.DataFrame(timeline_rows), use_container_width=True, hide_index=True)

if active_page == "People Directory":
    st.header("People Directory")
    st.caption("Every Atlas agent is now modeled as an AI employee with identity, manager, skills, tools, inbox, memory, and KPIs.")

    if employees_df.empty:
        st.info("No employees loaded yet. Run `python main.py`.")
    else:
        department_filter = st.selectbox("Department", ["All"] + sorted(employees_df["department"].dropna().unique().tolist()))
        filtered = employees_df if department_filter == "All" else employees_df[employees_df["department"] == department_filter]

        left, right = st.columns([1, 2])
        with left:
            selected_name = st.selectbox("Employee", filtered["name"].tolist())
            employee = employees_df[employees_df["name"] == selected_name].iloc[0]
            st.metric("Performance", f"{round(float(employee['performance_score']), 1)}%")
            st.metric("Workload", f"{round(float(employee['workload']), 1)}%")
            st.metric("Inbox", int(employee["inbox_count"]))
        with right:
            st.subheader(f"{employee['avatar_emoji']} {employee['name']}")
            st.caption(f"{employee['title']} · {employee['department']} · Reports to {employee['manager'] or 'CEO'}")
            st.write(employee.get("mission") or "No mission defined.")
            st.markdown("**Current task**")
            st.write(employee.get("current_task") or "No current task.")
            st.markdown("**Personality**")
            st.write(employee.get("personality") or "No personality profile.")

        selected_id = int(employee["id"])
        s1, s2, s3 = st.columns(3)
        with s1:
            st.subheader("Skills")
            skills_df = queries.employee_skills(engine, selected_id)
            if skills_df.empty:
                st.caption("No skills recorded.")
            else:
                for _, skill in skills_df.iterrows():
                    st.write(f"- {skill['skill']}")
        with s2:
            st.subheader("Tools")
            tools_df = queries.employee_tools(engine, selected_id)
            if tools_df.empty:
                st.caption("No tools recorded.")
            else:
                for _, tool in tools_df.iterrows():
                    st.write(f"- {tool['tool_name']} ({tool['access_level']})")
        with s3:
            st.subheader("Memory")
            memory_df = queries.employee_memories(engine, selected_id)
            if memory_df.empty:
                st.caption("No memories recorded.")
            else:
                for _, memory in memory_df.head(5).iterrows():
                    st.write(f"- {memory['content']}")

        st.subheader("Employee Inbox")
        inbox_df = queries.employee_messages(engine, selected_id)
        if inbox_df.empty:
            st.info("No messages for this employee.")
        else:
            st.dataframe(inbox_df[["created_at", "sender", "recipient", "subject", "status", "body"]], use_container_width=True, hide_index=True)

        st.subheader("Org Chart")
        org_cols = ["avatar_emoji", "name", "title", "department", "manager", "status", "performance_score", "workload"]
        st.dataframe(employees_df[org_cols], use_container_width=True, hide_index=True)


if active_page in {"Employee Workflows", "Communications Center"}:
    st.header("Employee Workflows")
    st.caption("Employees now receive assignments, message one another, and can answer questions from their own role context.")

    with db.get_session() as session:
        workflow_summary = EmployeeWorkflowService(session).ensure_workflows()

    w1, w2, w3 = st.columns(3)
    w1.metric("Tasks Routed", workflow_summary.get("tasks_routed", 0))
    w2.metric("Open Employee Work", workflow_summary.get("open_tasks", 0))
    w3.metric("Unread Messages", workflow_summary.get("unread_messages", 0))

    st.subheader("Sarah's Operating Board")
    st.caption("COO Sarah routes Atlas work to the employees responsible for each department.")
    board_cols = st.columns(4)
    departments_to_show = ["Operations", "Manufacturing", "Finance", "Marketing"]
    for idx, department_name in enumerate(departments_to_show):
        with board_cols[idx]:
            st.markdown(f"**{department_name}**")
            subset = employees_df[employees_df["department"] == department_name] if not employees_df.empty else employees_df
            if subset.empty:
                st.caption("No employees")
            else:
                for _, emp in subset.iterrows():
                    with st.container(border=True):
                        st.write(f"{emp['avatar_emoji']} **{emp['name']}**")
                        st.caption(str(emp['status']).title())
                        st.progress(min(100, float(emp.get('workload') or 0)) / 100, text=f"Workload {round(float(emp.get('workload') or 0), 1)}%")
                        st.write(short_title(emp.get("current_task") or "Ready", 80))

    st.subheader("Employee Assignments")
    if all_tasks_df.empty:
        st.info("No employee assignments yet. Approve a CEO Inbox candidate to create work.")
    else:
        for _, task in all_tasks_df.head(25).iterrows():
            with st.container(border=True):
                t1, t2, t3, t4 = st.columns([2, 2, 1, 1])
                t1.markdown(f"**{task['title']}**")
                t1.caption(task.get("project_name") or "Atlas Project")
                t2.write(task.get("description") or "")
                t3.metric("Owner", task.get("agent_name") or "Agent")
                t4.metric("Status", str(task.get("status") or "pending").replace("_", " ").title())
                a1, a2 = st.columns(2)
                if str(task.get("status") or "").lower() not in {"in_progress", "complete", "completed"}:
                    if a1.button("Start", key=f"start_task_{task['id']}"):
                        with db.get_session() as session:
                            EmployeeWorkflowService(session).start_task(int(task["id"]))
                        st.rerun()
                if str(task.get("status") or "").lower() not in {"complete", "completed"}:
                    if a2.button("Complete", key=f"complete_task_{task['id']}"):
                        with db.get_session() as session:
                            EmployeeWorkflowService(session).complete_task(int(task["id"]))
                        st.rerun()

    st.subheader("Internal Communications")
    if employee_messages_df.empty:
        st.info("No internal messages yet.")
    else:
        for _, msg in employee_messages_df.head(15).iterrows():
            with st.container(border=True):
                m1, m2 = st.columns([3, 1])
                with m1:
                    st.markdown(f"**{msg['sender']} → {msg['recipient']}**")
                    st.caption(f"{msg['subject']} · {msg['status']} · {msg['created_at']}")
                    st.write(msg["body"])
                with m2:
                    if msg["status"] == "unread":
                        if st.button("Mark Read", key=f"read_msg_{msg['id']}"):
                            with db.get_session() as session:
                                EmployeeWorkflowService(session).mark_message_read(int(msg["id"]))
                            st.rerun()

    st.subheader("Ask an Employee")
    if employees_df.empty:
        st.info("No employees loaded yet.")
    else:
        ask_col1, ask_col2 = st.columns([1, 2])
        with ask_col1:
            employee_to_ask = st.selectbox("Employee", employees_df["name"].tolist(), key="ask_employee_name")
        with ask_col2:
            question = st.text_input("Question", placeholder="David, what supplier risks should we watch?", key="ask_employee_question")
        if st.button("Ask Employee", key="ask_employee_button"):
            with db.get_session() as session:
                answer = EmployeeWorkflowService(session).ask_employee(employee_to_ask, question)
            st.text_area("Employee response", answer, height=220)


if active_page == "Employee Office":
    st.header("Employee Office")
    st.caption("Walk into an employee's office: current thought, inbox, memory, tools, skills, messages, and KPIs.")

    if employees_df.empty:
        st.info("No employees loaded yet. Run `python main.py`.")
    else:
        selected_name = st.selectbox("Choose employee", employees_df["name"].tolist(), key="employee_office_select")
        employee = employees_df[employees_df["name"] == selected_name].iloc[0]
        selected_id = int(employee["id"])

        with st.container(border=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"## {employee['avatar_emoji']} {employee['name']}")
                st.caption(f"{employee['title']} · {employee['department']} · Reports to {employee['manager'] or 'CEO'}")
                st.markdown("**Current thought**")
                st.write(employee_current_thought(employee))
            with c2:
                st.metric("Status", employee_status_badge(employee.get("status")))
                st.metric("Performance", f"{round(float(employee['performance_score']), 1)}%")
                st.metric("Workload", f"{round(float(employee['workload']), 1)}%")

        o1, o2 = st.columns([1, 1])
        with o1:
            st.subheader("Inbox")
            inbox_df = queries.employee_messages(engine, selected_id)
            if inbox_df.empty:
                st.info("Inbox is clear.")
            else:
                for _, msg in inbox_df.head(6).iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{msg['subject']}**")
                        st.caption(f"From {msg['sender']} · {msg['status']} · {msg['created_at']}")
                        st.write(msg["body"])

            st.subheader("Skills")
            skills_df = queries.employee_skills(engine, selected_id)
            if skills_df.empty:
                st.caption("No skills recorded.")
            else:
                st.write(" ".join([f"`{row['skill']}`" for _, row in skills_df.iterrows()]))

        with o2:
            st.subheader("Memory")
            memory_df = queries.employee_memories(engine, selected_id)
            if memory_df.empty:
                st.info("No personal memory yet. Run a work cycle to create reflections.")
            else:
                for _, memory in memory_df.head(8).iterrows():
                    with st.container(border=True):
                        st.caption(memory.get("memory_type") or "memory")
                        st.write(memory["content"])

            st.subheader("Tools")
            tools_df = queries.employee_tools(engine, selected_id)
            if tools_df.empty:
                st.caption("No tools recorded.")
            else:
                for _, tool in tools_df.iterrows():
                    st.write(f"- {tool['tool_name']} ({tool['access_level']})")

        st.subheader("Ask this employee")
        question = st.text_input("Question", placeholder=f"{employee['name']}, what should I know right now?", key="office_question")
        if st.button("Ask", key="office_ask_button"):
            with db.get_session() as session:
                answer = EmployeeWorkflowService(session).ask_employee(selected_name, question)
            st.text_area("Response", answer, height=220)


if active_page in {"Employee Runtime", "Operations Center"}:
    st.header("Operations Center")
    st.caption("Watch the company operate: employees think, plan, work, wait, and learn.")

    r1, r2 = st.columns([1, 3])
    with r1:
        max_employees = st.slider("Employees to process", 1, 12, 8)
        if st.button("Run Work Cycle", type="primary"):
            with db.get_session() as session:
                result = EmployeeRuntimeService(session).run_cycle(max_employees=max_employees)
            st.session_state["last_runtime_result"] = result
            st.rerun()
    with r2:
        st.info("This first runtime is deterministic and local. It does not call external AI yet; it gives Atlas employees a visible operating rhythm.")

    result = st.session_state.get("last_runtime_result")
    if result:
        st.subheader("Latest Work Cycle")
        st.caption(f"Timestamp: {result.get('timestamp')}")
        st.metric("Employees Processed", result.get("employees_processed", 0))
        actions = result.get("actions", [])
        if actions:
            for action in actions:
                with st.container(border=True):
                    phase = str(action.get('phase') or 'working').title()
                    st.markdown(f"**{action.get('employee')}** — {phase}: {humanize_employee_action(action.get('action'))}")
                    st.caption(action.get('title') or "Atlas employee")
                    st.write(action.get('thought') or action.get('summary'))
                    st.caption(f"Next: {action.get('next_action') or 'Continue current work'}")

    st.subheader("Current Employee Activity")
    if employees_df.empty:
        st.info("No employees loaded yet.")
    else:
        cols = st.columns(3)
        for idx, (_, employee) in enumerate(employees_df.iterrows()):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {employee['avatar_emoji']} {employee['name']}")
                    st.caption(f"{employee['title']} · {employee_status_badge(employee.get('status'))}")
                    st.write(employee_current_thought(employee))
                    st.progress(min(100, float(employee.get('workload') or 0)) / 100, text=f"Workload {round(float(employee.get('workload') or 0), 1)}%")
                    st.caption(f"Last active: {employee.get('last_active_at') or 'not yet'}")

    st.subheader("Recent Internal Messages")
    if employee_messages_df.empty:
        st.info("No internal messages yet.")
    else:
        for _, msg in employee_messages_df.head(12).iterrows():
            with st.container(border=True):
                st.markdown(f"**{msg['sender']} → {msg['recipient']}**")
                st.caption(f"{msg['subject']} · {msg['status']} · {msg['created_at']}")
                st.write(msg["body"])


if active_page == "Employee Mind":
    st.header("Employee Mind")
    st.caption("Employees now create thoughts, decisions, goals, and reflections during each work cycle.")

    run_col, info_col = st.columns([1, 3])
    with run_col:
        max_employees = st.slider("Employees to process", 1, 12, 8, key="mind_cycle_count")
        if st.button("Run Mind Cycle", type="primary", key="run_mind_cycle"):
            with db.get_session() as session:
                result = EmployeeRuntimeService(session).run_cycle(max_employees=max_employees)
            st.session_state["last_mind_result"] = result
            st.rerun()
    with info_col:
        st.info("This release is deterministic and local: the Mind creates explainable thoughts and decisions without external LLM calls yet.")

    result = st.session_state.get("last_mind_result")
    if result:
        st.subheader("Latest Mind Cycle")
        st.caption(f"Timestamp: {result.get('timestamp')}")
        for action in result.get("actions", []):
            with st.container(border=True):
                st.markdown(f"### {action.get('employee')} — {str(action.get('phase') or 'working').title()}")
                st.write(action.get("thought"))
                c1, c2 = st.columns([2, 1])
                c1.caption(f"Reasoning: {action.get('rationale')}")
                c2.metric("Confidence", f"{round(float(action.get('confidence') or 0) * 100)}%")
                st.caption(f"Next: {action.get('next_action')}")

    st.subheader("Active Employee Goals")
    if employee_goals_df.empty:
        st.info("No employee goals yet. Run `python main.py` or a work cycle to seed the workforce.")
    else:
        for _, goal in employee_goals_df.head(12).iterrows():
            with st.container(border=True):
                st.markdown(f"**{goal['name']}** — {goal['goal_title']}")
                st.caption(f"{goal['title']} · Priority {goal['priority']} · {goal['status']}")
                st.progress(min(100, float(goal.get('progress') or 0)) / 100, text=f"Progress {round(float(goal.get('progress') or 0), 1)}%")
                st.write(goal.get("description") or "")

    st.subheader("Recent Thoughts")
    if employee_thoughts_df.empty:
        st.info("No thoughts recorded yet. Run a mind cycle.")
    else:
        cols = st.columns(2)
        for idx, (_, thought) in enumerate(employee_thoughts_df.head(10).iterrows()):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(f"**{thought['name']}**")
                    st.caption(f"{thought['thought_type']} · confidence {round(float(thought['confidence']) * 100)}%")
                    st.write(thought["content"])

    st.subheader("Decision Records")
    if employee_decisions_df.empty:
        st.info("No decisions recorded yet.")
    else:
        for _, decision in employee_decisions_df.head(8).iterrows():
            with st.container(border=True):
                st.markdown(f"**{decision['name']} — {decision['title']}**")
                st.caption(f"{decision['decision_type']} · confidence {round(float(decision['confidence']) * 100)}% · {decision['created_at']}")
                st.write(decision["reasoning"])
                st.caption(f"Outcome: {decision['outcome']}")

    st.subheader("Reflections and Learning")
    if employee_reflections_df.empty:
        st.info("No reflections yet.")
    else:
        for _, reflection in employee_reflections_df.head(8).iterrows():
            with st.container(border=True):
                st.markdown(f"**{reflection['name']}**")
                st.write(reflection["content"])
                if reflection.get("lesson"):
                    st.caption(f"Lesson: {reflection['lesson']}")


if active_page in {"CEO Workspace", "Executive Office"}:
    st.header("CEO Workspace")
    st.caption("Run Atlas like a product business: projects, agent tasks, readiness, and daily brief.")
    with db.get_session() as session:
        ceo_service = CEOWorkspaceService(session)
        brief = ceo_service.daily_brief()

    with st.container(border=True):
        st.subheader("Daily Brief")
        st.write(brief["headline"])
        b1, b2, b3, b4, b5 = st.columns(5)
        b1.metric("CEO Inbox", brief.get("candidates", 0))
        b2.metric("Active Projects", brief["projects"])
        b3.metric("Open Agent Tasks", brief["open_tasks"])
        b4.metric("Launch Ready", brief["launch_ready"])
        b5.metric("Needs Attention", brief["needs_attention"])

    st.subheader("CEO Inbox")
    st.caption("Atlas automatically creates these candidates from strong opportunities. Review, approve, park, or reject.")
    pending_candidates = candidates_df[candidates_df["status"] == "candidate"] if not candidates_df.empty else candidates_df
    if pending_candidates.empty:
        st.info("No candidate projects waiting for review. Run research with `python main.py` to let Atlas create candidates.")
    else:
        for _, candidate in pending_candidates.iterrows():
            with st.container(border=True):
                st.subheader(candidate["title"])
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Confidence", round(float(candidate["confidence"]), 1))
                c2.metric("Est. Margin", f"{round(float(candidate['estimated_margin']), 1)}%")
                c3.metric("Priority", int(candidate["priority"]))
                c4.metric("Status", str(candidate["status"]).title())
                st.write(candidate.get("summary") or "")
                st.caption(f"Reason: {candidate.get('reason') or 'Meets candidate threshold'}")
                a1, a2, a3 = st.columns(3)
                with a1:
                    if st.button("Approve", key=f"approve_{candidate['id']}", type="primary"):
                        with db.get_session() as session:
                            project = CEOWorkspaceService(session).approve_candidate(int(candidate["id"]))
                        st.success(f"Approved and created project: {project.project_name}")
                        st.rerun()
                with a2:
                    if st.button("Park", key=f"park_{candidate['id']}"):
                        with db.get_session() as session:
                            CEOWorkspaceService(session).park_candidate(int(candidate["id"]))
                        st.info("Candidate parked.")
                        st.rerun()
                with a3:
                    if st.button("Reject", key=f"reject_{candidate['id']}"):
                        with db.get_session() as session:
                            CEOWorkspaceService(session).reject_candidate(int(candidate["id"]))
                        st.warning("Candidate rejected.")
                        st.rerun()

    with st.expander("Reviewed Candidates", expanded=False):
        reviewed = candidates_df[candidates_df["status"] != "candidate"] if not candidates_df.empty else candidates_df
        if reviewed.empty:
            st.caption("No reviewed candidates yet.")
        else:
            st.dataframe(reviewed[["title", "confidence", "estimated_margin", "status", "reviewed_at"]], use_container_width=True, hide_index=True)

    st.subheader("Active Product Projects")
    if projects_df.empty:
        st.info("No active product projects yet. Approve a candidate from the CEO Inbox.")
    else:
        for _, project in projects_df.iterrows():
            render_ceo_project(project)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Agent Task Queue")
        if all_tasks_df.empty:
            st.info("No agent tasks yet.")
        else:
            st.dataframe(all_tasks_df[["project_name", "agent_name", "title", "status", "priority"]], use_container_width=True, hide_index=True)
    with c2:
        st.subheader("Agent Activity Timeline")
        if all_events_df.empty:
            st.info("No agent activity yet.")
        else:
            st.dataframe(all_events_df[["created_at", "agent_name", "event_type", "message"]], use_container_width=True, hide_index=True)

if active_page in {"Business Workspace", "Portfolio Office"}:
    st.header("Business Workspace")
    st.caption("Atlas groups approved products into businesses so the CEO can manage brands, product lines, and departments instead of isolated SKUs.")

    if businesses_df.empty:
        st.info("No businesses yet. Approve a candidate in the CEO Inbox to create the first business workspace.")
        if not business_opps_df.empty:
            st.subheader("Business Opportunities")
            st.dataframe(business_opps_df, use_container_width=True, hide_index=True)
    else:
        left, right = st.columns([1, 2])
        with left:
            st.subheader("Businesses")
            selected_business_name = st.selectbox("Select business", businesses_df["name"].tolist())
            business = businesses_df[businesses_df["name"] == selected_business_name].iloc[0]
            st.metric("Forecast Revenue", as_currency(business["estimated_monthly_revenue"]))
            st.metric("Estimated Margin", f"{round(float(business['estimated_margin'] or 0), 1)}%")
            st.metric("Products", int(business["products"]))
            st.metric("Avg Readiness", f"{round(float(business['avg_readiness'] or 0), 1)}%")
        with right:
            st.subheader(str(business["name"]))
            st.caption(f"Brand: {business['brand_name']} | Market: {business['market']} | Status: {business['status']}")
            st.write(business.get("vision") or "No vision statement yet.")
            st.progress(min(100, int(float(business.get("avg_readiness") or 0))) / 100, text=f"Business launch readiness: {round(float(business.get('avg_readiness') or 0), 1)}%")

        st.subheader("Product Portfolio")
        products_df = queries.products_for_business(engine, int(business["id"]))
        if products_df.empty:
            st.info("No products attached to this business yet.")
        else:
            for _, product in products_df.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    c1.markdown(f"**{product['name']}**")
                    c1.caption(product.get("summary") or product.get("target_customer") or "")
                    c2.metric("Confidence", round(float(product.get("confidence") or 0), 1))
                    c3.metric("Price", f"${float(product.get('suggested_price_min') or 0):.0f}-${float(product.get('suggested_price_max') or 0):.0f}")
                    c4.metric("Readiness", f"{round(float(product.get('readiness_score') or 0), 1)}%")
                    st.write(f"Stage: `{product.get('stage') or 'concept'}` · Manufacturing: `{product.get('manufacturing_status') or 'pending'}` · Finance: `{product.get('finance_status') or 'pending'}` · Marketing: `{product.get('marketing_status') or 'pending'}` · Launch: `{product.get('launch_status') or 'not_started'}`")

        st.subheader("Business Opportunities")
        if business_opps_df.empty:
            st.caption("No business opportunities recorded yet.")
        else:
            st.dataframe(business_opps_df[["title", "market", "confidence", "estimated_monthly_revenue", "estimated_margin", "status", "reason"]], use_container_width=True, hide_index=True)

if active_page in {"Company Builder", "Strategy Room"}:
    st.header("Company Builder")
    st.caption("Approve grouped business opportunities once and let Atlas create the business, products, employee work, and timeline.")

    if business_opps_df.empty:
        st.info("No business opportunities yet. Run `python main.py` to let Atlas group candidate products into businesses.")
    else:
        recommended = business_opps_df.iloc[0]
        with st.container(border=True):
            st.subheader(f"Recommended Business: {recommended['title']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Confidence", f"{round(float(recommended.get('confidence') or 0), 1)}%")
            c2.metric("Forecast Revenue", as_currency(recommended.get("estimated_monthly_revenue") or 0))
            c3.metric("Estimated Margin", f"{round(float(recommended.get('estimated_margin') or 0), 1)}%")
            c4.metric("Market", str(recommended.get("market") or "Unknown"))
            st.write(recommended.get("summary") or recommended.get("reason") or "Atlas grouped related product candidates into this business opportunity.")

        st.subheader("Business Opportunities Waiting for CEO Review")
        for _, opportunity in business_opps_df.iterrows():
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.subheader(opportunity["title"])
                    st.caption(f"Market: {opportunity.get('market') or 'Unknown'} · Status: {opportunity.get('status') or 'candidate'}")
                    st.write(opportunity.get("summary") or "No summary available.")
                    with st.expander("Why Atlas recommends this business"):
                        st.write(opportunity.get("reason") or "Related products cluster into a coherent business opportunity.")
                with right:
                    st.metric("Confidence", f"{round(float(opportunity.get('confidence') or 0), 1)}%")
                    st.metric("Forecast", as_currency(opportunity.get("estimated_monthly_revenue") or 0))
                    st.metric("Margin", f"{round(float(opportunity.get('estimated_margin') or 0), 1)}%")
                st.info("Approval workflow is handled from the CEO Workspace in this release.")

if active_page == "Overview":
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

if active_page == "Opportunity Workspace":
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

if active_page == "AI Product Designer":
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

if active_page == "Agent Command Center":
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

if active_page == "Listings Gallery":
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

if active_page == "Shop Intelligence":
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

if active_page == "Trends":
    st.header("Trend Intelligence")
    if trends.empty:
        st.info("Run research multiple times to build trend history.")
    else:
        metric = st.selectbox("Metric", ["opportunity_score", "avg_price", "avg_views", "avg_favorites", "listing_count"])
        fig = px.line(trends, x="captured_at", y=metric, color="keyword", markers=True, title=f"{metric} Over Time")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(trends, use_container_width=True, hide_index=True)

if active_page == "Research Runs":
    st.header("Research Runs")
    st.dataframe(runs, use_container_width=True, hide_index=True)


if active_page in {"Vendor Workspace", "Vendor Directory"}:
    st.header("Vendor Intelligence")
    st.caption("David's vendor intelligence workspace: supplier profiles, trust scores, quotes, RFQs, and relationship memory.")

    if vendors_df.empty:
        st.info("No vendors loaded yet. Run `python main.py` to seed vendor intelligence.")
    else:
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Vendors", len(vendors_df))
        v2.metric("Avg Trust", round(vendors_df["trust_score"].mean(), 1))
        v3.metric("Avg Lead Time", f"{round(vendors_df['average_lead_time_days'].mean(), 1)} days")
        v4.metric("Avg Margin", f"{round(vendors_df['average_margin'].mean(), 1)}%")

        st.subheader("Recommended Vendors")
        for _, vendor in vendors_df.head(6).iterrows():
            render_vendor_card(vendor)

        st.subheader("Vendor Profile")
        selected_vendor = st.selectbox("Select vendor", vendors_df["name"].tolist(), key="vendor_profile_select")
        selected_row = vendors_df[vendors_df["name"] == selected_vendor].iloc[0]
        selected_vendor_id = int(selected_row["id"])

        profile_left, profile_right = st.columns([2, 1])
        with profile_left:
            render_vendor_card(selected_row)
            st.markdown("**Vendor notes**")
            st.write(selected_row.get("notes") or "No notes recorded.")
        with profile_right:
            st.markdown("**Primary Contact**")
            st.write(selected_row.get("contact_name") or "No contact")
            st.write(selected_row.get("contact_email") or "")
            st.markdown("**Risk**")
            st.write(str(selected_row.get("risk_level") or "medium").title())

        st.subheader("Quotes")
        selected_quotes = queries.vendor_quotes(engine, selected_vendor_id)
        if selected_quotes.empty:
            st.info("No quotes recorded for this vendor.")
        else:
            st.dataframe(selected_quotes, use_container_width=True, hide_index=True)

        st.subheader("Vendor Timeline")
        selected_events = queries.vendor_events(engine, selected_vendor_id)
        if selected_events.empty:
            st.info("No vendor events recorded yet.")
        else:
            for _, event in selected_events.head(10).iterrows():
                with st.container(border=True):
                    st.markdown(f"**{event['event_type'].replace('_', ' ').title()}**")
                    st.caption(f"{event['actor']} · {event['created_at']}")
                    st.write(event["message"])

if active_page == "RFQ Center":
    st.header("RFQ Center")
    st.caption("Prepare supplier quote requests and track quote readiness. External email sending will plug into the Communications Hub later.")

    if vendors_df.empty:
        st.info("No vendors loaded yet.")
    else:
        c1, c2 = st.columns([1, 2])
        with c1:
            vendor_name = st.selectbox("Vendor", vendors_df["name"].tolist(), key="rfq_vendor")
            product_name = st.text_input("Product", value="Premium Magnetic Baseball Lineup Board", key="rfq_product")
            vendor_id = int(vendors_df[vendors_df["name"] == vendor_name].iloc[0]["id"])
            if st.button("Prepare RFQ", key="prepare_rfq"):
                with db.get_session() as session:
                    VendorIntelligenceService(session).create_rfq_event(vendor_id, product_name)
                st.success("RFQ event prepared and added to the vendor timeline.")
                st.rerun()
        with c2:
            st.markdown("### RFQ Draft")
            st.text_area(
                "Draft",
                value=(
                    f"Hello,\n\nWe are evaluating suppliers for {product_name}. "
                    "Please provide unit pricing, MOQ, lead time, sample cost, packaging options, "
                    "and shipping estimates.\n\nThank you,\nDavid\nManufacturing Director, Atlas Enterprise"
                ),
                height=220,
                label_visibility="collapsed",
            )

        st.subheader("All Quotes")
        if vendor_quotes_df.empty:
            st.info("No vendor quotes recorded yet.")
        else:
            st.dataframe(vendor_quotes_df, use_container_width=True, hide_index=True)

if active_page == "Vendor Timeline":
    st.header("Vendor Timeline")
    st.caption("Chronological vendor relationship history across quotes, RFQs, and supplier decisions.")
    if vendor_events_df.empty:
        st.info("No vendor events yet.")
    else:
        for _, event in vendor_events_df.head(50).iterrows():
            with st.container(border=True):
                st.markdown(f"**{event['vendor']} — {event['event_type'].replace('_', ' ').title()}**")
                st.caption(f"{event['actor']} · {event['created_at']}")
                st.write(event["message"])


if active_page == "Finance Workspace":
    st.header("Finance Intelligence")
    st.caption("Michael evaluates whether Atlas can make money before a product launches.")

    if businesses_df.empty:
        st.info("No businesses yet. Approve a business opportunity first.")
    else:
        selected_business_name = st.selectbox("Business", businesses_df["name"].tolist(), key="finance_business")
        business_row = businesses_df[businesses_df["name"] == selected_business_name].iloc[0]
        business_id = int(business_row["id"])

        if st.button("Run Finance Analysis", key="run_finance_analysis"):
            with db.get_session() as session:
                summary = FinanceIntelligenceService(session).generate_for_business(business_id, refresh=True)
            st.success(
                f"Finance analyzed {summary.analyses_created} project(s). "
                f"Average margin: {summary.average_margin:.1f}%. "
                f"Estimated monthly profit: {as_currency(summary.monthly_profit_estimate)}."
            )
            st.rerun()

        selected_finance = queries.finance_analyses(engine, business_id)
        if selected_finance.empty:
            st.warning("No finance analysis yet. Click Run Finance Analysis.")
        else:
            approved = len(selected_finance[selected_finance["approval_status"] == "approved"])
            review = len(selected_finance[selected_finance["approval_status"] == "review"])
            rejected = len(selected_finance[selected_finance["approval_status"] == "rejected"])
            avg_margin = selected_finance["gross_margin"].mean()
            total_profit = selected_finance["monthly_profit_estimate"].sum()
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Avg Gross Margin", f"{avg_margin:.1f}%")
            f2.metric("Monthly Profit Estimate", as_currency(total_profit))
            f3.metric("Finance Approved", approved)
            f4.metric("Needs Review", review + rejected)

            st.subheader("Finance Recommendation")
            top = selected_finance.iloc[0]
            with st.container(border=True):
                st.markdown(f"### {top['project_name']}")
                st.write(top.get("recommendation") or "No recommendation available.")
                cols = st.columns(5)
                cols[0].metric("Price", as_currency(top.get("selling_price")))
                cols[1].metric("Cost", as_currency(top.get("total_variable_cost")))
                cols[2].metric("Profit", as_currency(top.get("gross_profit")))
                cols[3].metric("Margin", f"{float(top.get('gross_margin') or 0):.1f}%")
                cols[4].metric("Status", str(top.get("approval_status") or "review").upper())

            st.subheader("Product Finance Models")
            for _, row in selected_finance.iterrows():
                with st.container(border=True):
                    left, right = st.columns([3, 1])
                    with left:
                        st.markdown(f"### {row['project_name']}")
                        st.caption(row.get("assumptions") or "")
                    with right:
                        st.metric("Finance Status", str(row.get("approval_status") or "review").upper())
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Sell Price", as_currency(row.get("selling_price")))
                    c2.metric("Unit Cost", as_currency(row.get("unit_cost")))
                    c3.metric("Total Cost", as_currency(row.get("total_variable_cost")))
                    c4.metric("Margin", f"{float(row.get('gross_margin') or 0):.1f}%")
                    c5.metric("Break-even", as_int(row.get("break_even_units")))
                    st.progress(min(100, max(0, float(row.get("gross_margin") or 0))) / 100, text="Margin strength")
                    st.write(row.get("recommendation") or "")

if active_page == "Unit Economics":
    st.header("Unit Economics")
    st.caption("Cost stack for every product project.")
    if finance_df.empty:
        st.info("Run Finance Analysis from the Finance Workspace first.")
    else:
        view_cols = [
            "business", "project_name", "selling_price", "unit_cost", "packaging_cost",
            "outbound_shipping_cost", "marketplace_fee", "payment_fee", "ad_cost",
            "total_variable_cost", "gross_profit", "gross_margin", "approval_status",
        ]
        st.dataframe(finance_df[view_cols], use_container_width=True, hide_index=True)
        chart = px.scatter(
            finance_df,
            x="gross_margin",
            y="monthly_profit_estimate",
            color="approval_status",
            size="selling_price",
            hover_name="project_name",
            title="Margin vs Monthly Profit Estimate",
        )
        st.plotly_chart(chart, use_container_width=True)

if active_page == "Profit Scenarios":
    st.header("Profit Scenarios")
    st.caption("Conservative, base, and upside finance outcomes.")
    if finance_scenarios_df.empty:
        st.info("Run Finance Analysis to generate scenarios.")
    else:
        st.dataframe(finance_scenarios_df, use_container_width=True, hide_index=True)
        chart = px.bar(
            finance_scenarios_df,
            x="project_name",
            y="monthly_profit",
            color="name",
            barmode="group",
            title="Monthly Profit by Scenario",
        )
        st.plotly_chart(chart, use_container_width=True)

if active_page == "Finance Timeline":
    st.header("Finance Timeline")
    st.caption("Michael's finance decisions and unit economics events.")
    if finance_events_df.empty:
        st.info("No finance events yet.")
    else:
        for _, event in finance_events_df.head(50).iterrows():
            with st.container(border=True):
                st.markdown(f"**{event['actor']} · {event['event_type'].replace('_', ' ').title()}**")
                st.caption(f"{event.get('business') or ''} · {event.get('project_name') or ''} · {event['created_at']}")
                st.write(event["message"])


if active_page == "Design Studio":
    st.header("Design Studio")
    st.caption("Noah creates real AI product concept renders before David begins sourcing.")

    with db.get_session() as session:
        design_service = DesignManufacturingService(session)
        provider_status = design_service.image_provider_status()

    provider_cols = st.columns(4)
    provider_cols[0].metric("AI Image Provider", provider_status.provider)
    provider_cols[1].metric("Status", "Configured" if provider_status.configured else "Not Configured")
    provider_cols[2].metric("Model", provider_status.model)
    provider_cols[3].metric("Output", f"{provider_status.size} · {provider_status.quality}")

    if not provider_status.configured:
        st.error(
            "AI product rendering is not configured. Add OPENAI_API_KEY to .env and restart "
            "the dashboard. Atlas will no longer pretend a wireframe is a completed Noah design."
        )

    if projects_df.empty:
        st.info("No active product projects yet. Approve a candidate in the CEO Workspace.")
    else:
        project_name = st.selectbox("Product project", projects_df["project_name"].tolist(), key="design_project")
        project_id = int(projects_df[projects_df["project_name"] == project_name].iloc[0]["id"])

        concepts = queries.design_concepts(engine, project_id)
        controls = st.columns([1.4, 1.4, 3])
        with controls[0]:
            if st.button("Generate AI Concepts", type="primary", key="generate_designs", disabled=not provider_status.configured):
                with st.spinner("Noah is generating three product concepts. This may take several minutes..."):
                    with db.get_session() as session:
                        summary = DesignManufacturingService(session).generate_concepts(project_id)
                st.success(f"Noah prepared {summary.concepts_created} concepts for {summary.project_name}.")
                st.rerun()
        with controls[1]:
            if st.button(
                "Regenerate All AI Images",
                key="regenerate_design_images",
                disabled=concepts.empty or not provider_status.configured,
            ):
                with st.spinner("Noah is regenerating concept images. This may take several minutes..."):
                    with db.get_session() as session:
                        count = DesignManufacturingService(session).regenerate_project_images(project_id)
                st.success(f"Noah regenerated {count} concept image(s).")
                st.rerun()

        concepts = queries.design_concepts(engine, project_id)
        if concepts.empty:
            st.info("No concepts yet. Ask Noah to generate the AI design set.")
        else:
            approved_count = len(concepts[concepts["status"] == "approved"])
            st.metric("Approved Design", "Yes" if approved_count else "Waiting for CEO")

            legacy_count = sum(
                1 for value in concepts["mockup_svg"].tolist()
                if str(value or "").lstrip().startswith("<svg")
            )
            if legacy_count:
                st.warning(
                    f"{legacy_count} legacy wireframe concept(s) are still stored from v2.7.1. "
                    "Click 'Regenerate All AI Images' to replace them with real AI renders."
                )

            for _, concept in concepts.sort_values("id").iterrows():
                concept_id = int(concept["id"])
                mockup = str(concept["mockup_svg"] or "")
                image_error = DesignManufacturingService.image_error_message(mockup)
                is_ai_image = DesignManufacturingService.is_ai_image(mockup)
                is_legacy_svg = mockup.lstrip().startswith("<svg")

                with st.container(border=True):
                    left, right = st.columns([3, 2])
                    with left:
                        if is_ai_image:
                            st.markdown("**✨ AI GENERATED PRODUCT CONCEPT**")
                            try:
                                image_bytes = DesignManufacturingService.image_bytes(mockup)
                                st.image(
                                    image_bytes,
                                    caption=f"{concept['concept_name']} · AI render v{int(concept['concept_version'] or 1)}",
                                    use_container_width=True,
                                )
                                st.caption(f"Stored image size: {len(image_bytes) / (1024 * 1024):.2f} MB")
                            except ValueError as exc:
                                st.error(f"Stored image could not be decoded: {exc}")
                        elif image_error:
                            st.error("AI DESIGN GENERATION FAILED")
                            st.markdown(f"**Provider:** {provider_status.provider}")
                            st.markdown(f"**Model:** `{provider_status.model}`")
                            st.code(image_error)
                            if st.button("Retry AI Image", key=f"retry_ai_image_{concept_id}", type="primary", disabled=not provider_status.configured):
                                with st.spinner(f"Noah is regenerating {concept['concept_name']}..."):
                                    with db.get_session() as session:
                                        refreshed = DesignManufacturingService(session).retry_concept_image(concept_id)
                                if DesignManufacturingService.is_ai_image(refreshed.mockup_svg):
                                    st.success("AI image generated and saved.")
                                else:
                                    st.error(DesignManufacturingService.image_error_message(refreshed.mockup_svg) or "Image generation failed.")
                                st.rerun()
                        elif is_legacy_svg:
                            st.warning("LEGACY WIREFRAME — NOT AN APPROVABLE AI DESIGN")
                            st.caption("This concept predates the real AI Design Studio.")
                            if st.button("Replace with AI Render", key=f"replace_legacy_{concept_id}", type="primary", disabled=not provider_status.configured):
                                with st.spinner(f"Noah is replacing {concept['concept_name']}..."):
                                    with db.get_session() as session:
                                        DesignManufacturingService(session).retry_concept_image(concept_id)
                                st.rerun()
                        else:
                            st.error("No product image is stored for this design concept.")
                            if st.button("Generate AI Image", key=f"generate_missing_{concept_id}", type="primary", disabled=not provider_status.configured):
                                with st.spinner(f"Noah is generating {concept['concept_name']}..."):
                                    with db.get_session() as session:
                                        DesignManufacturingService(session).retry_concept_image(concept_id)
                                st.rerun()

                    with right:
                        st.subheader(str(concept["concept_name"]))
                        status_label = str(concept["status"]).upper()
                        image_label = "AI IMAGE READY" if is_ai_image else "IMAGE NOT READY"
                        st.caption(f"{concept['designer_name']} · {status_label} · {image_label}")
                        st.write(concept["design_rationale"])
                        st.markdown("**Materials**")
                        material_items = [
                            m.strip() for m in str(concept["materials"] or "").replace("|", ",").split(",")
                            if m.strip()
                        ]
                        if material_items:
                            st.write(" · ".join(f"`{item}`" for item in material_items))
                        else:
                            st.caption("No materials specified")
                        st.markdown(f"**Dimensions:** {concept['dimensions']}")
                        st.metric("Suggested Price", as_currency(concept["suggested_price"]))
                        st.write(concept["designer_notes"])
                        with st.expander("Noah's AI image-generation prompt"):
                            st.write(concept["image_prompt"])

                        with st.expander("Direct Noah's next revision", expanded=False):
                            revision_direction = st.text_area(
                                "What should be materially different?",
                                placeholder=(
                                    "Example: Make it a foldable hard-shell travel case with magnetic tiles stored "
                                    "inside, no printed words, darker premium materials, and a visible dugout hook."
                                ),
                                key=f"design_direction_{concept_id}",
                                height=110,
                            )
                            if st.button(
                                "Generate Directed Revision",
                                key=f"directed_revision_{concept_id}",
                                type="primary",
                                disabled=not provider_status.configured,
                            ):
                                try:
                                    with st.spinner(f"Noah is rebuilding {concept['concept_name']} from your direction..."):
                                        with db.get_session() as session:
                                            revised = DesignManufacturingService(session).revise_concept_image(
                                                concept_id, revision_direction
                                            )
                                    if DesignManufacturingService.is_ai_image(revised.mockup_svg):
                                        st.success("Directed revision generated and saved.")
                                    else:
                                        st.error(DesignManufacturingService.image_error_message(revised.mockup_svg) or "Image generation failed.")
                                    st.rerun()
                                except ValueError as exc:
                                    st.error(str(exc))

                    if concept["status"] == "review":
                        note = st.text_input("CEO note", key=f"design_note_{concept_id}")
                        a, b, c = st.columns(3)
                        approve_disabled = not is_ai_image
                        if a.button("Approve", key=f"approve_design_{concept_id}", disabled=approve_disabled):
                            try:
                                with db.get_session() as session:
                                    DesignManufacturingService(session).review_concept(concept_id, "approved", note)
                                st.success("Design approved and handed to David.")
                                st.rerun()
                            except ValueError as exc:
                                st.error(str(exc))
                        if b.button("Needs Revision", key=f"revise_design_{concept_id}"):
                            with db.get_session() as session:
                                DesignManufacturingService(session).review_concept(concept_id, "revision", note)
                            st.warning("Revision requested from Noah.")
                            st.rerun()
                        if c.button("Reject", key=f"reject_design_{concept_id}"):
                            with db.get_session() as session:
                                DesignManufacturingService(session).review_concept(concept_id, "rejected", note)
                            st.error("Concept rejected.")
                            st.rerun()


if active_page == "Manufacturing Execution":
    st.header("Manufacturing Execution")
    st.caption("David sources the approved design, recommends a supplier, and hands real cost assumptions to Michael.")
    assignments = queries.sourcing_assignments(engine)
    recommendations = queries.supplier_recommendations(engine)
    if projects_df.empty:
        st.info("No product projects available.")
    else:
        project_name = st.selectbox("Product project", projects_df["project_name"].tolist(), key="mfg_exec_project")
        project_id = int(projects_df[projects_df["project_name"] == project_name].iloc[0]["id"])
        concepts = queries.design_concepts(engine, project_id)
        approved = concepts[concepts["status"] == "approved"] if not concepts.empty else concepts
        if approved.empty:
            st.warning("Manufacturing is waiting on an approved design from Noah.")
        else:
            st.success(f"Approved design package: {approved.iloc[0]['concept_name']}")
            if st.button("David: Execute Supplier Sourcing", type="primary", key="execute_sourcing"):
                try:
                    with db.get_session() as session:
                        rec = DesignManufacturingService(session).execute_sourcing(project_id)
                        supplier_name, confidence = rec.supplier_name, rec.confidence
                    st.success(f"David recommends {supplier_name} with {confidence:.1f}% confidence.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        project_assignments = assignments[assignments["project_id"] == project_id] if not assignments.empty else assignments
        if not project_assignments.empty:
            st.subheader("David's Sourcing Assignment")
            st.dataframe(project_assignments, use_container_width=True, hide_index=True)
        project_recs = recommendations[recommendations["project_id"] == project_id] if not recommendations.empty else recommendations
        if not project_recs.empty:
            st.subheader("Supplier Recommendation")
            for _, rec in project_recs.iterrows():
                with st.container(border=True):
                    st.subheader(str(rec["supplier_name"]))
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Confidence", f"{float(rec['confidence']):.1f}%")
                    c2.metric("Landed Cost", as_currency(rec["landed_cost"]))
                    c3.metric("Lead Time", f"{int(rec['lead_time_days'])} days")
                    c4.metric("MOQ", int(rec["moq"]))
                    st.write(rec["reason"])
                    st.caption(f"Status: {str(rec['status']).upper()}")
                    if rec["status"] == "recommended" and st.button("Approve Supplier + Send to Finance", key=f"approve_supplier_{int(rec['id'])}"):
                        with db.get_session() as session:
                            DesignManufacturingService(session).approve_supplier_and_handoff_finance(int(rec["id"]))
                        st.success("Supplier approved. Michael recalculated finance using the manufacturing handoff."); st.rerun()

if active_page == "Design Timeline":
    st.header("Design & Manufacturing Timeline")
    st.caption("Follow the employee handoff from Noah → David → Mia → Michael.")
    events = queries.agent_events(engine)
    if events.empty:
        st.info("No design/manufacturing events yet.")
    else:
        filtered = events[events["event_type"].isin(["design_concepts_created", "design_handoff", "supplier_recommended", "manufacturing_approved"])]
        if filtered.empty:
            st.info("Generate a design concept to begin the timeline.")
        else:
            for _, event in filtered.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{event['agent_name']} — {str(event['event_type']).replace('_', ' ').title()}**")
                    st.caption(str(event["created_at"]))
                    st.write(event["message"])

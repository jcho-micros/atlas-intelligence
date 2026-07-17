from __future__ import annotations

from datetime import datetime

from app.database.models import (
    Department,
    Employee,
    EmployeeGoal,
    EmployeeKPI,
    EmployeeMemory,
    EmployeeMessage,
    EmployeeThought,
    EmployeeSkill,
    EmployeeTool,
)


class EmployeeService:
    """Creates and reads the first Atlas Enterprise AI workforce."""

    DEFAULT_EMPLOYEES = [
        {
            "name": "John Cho",
            "title": "Chief Executive Officer",
            "department": "Executive",
            "manager": None,
            "emoji": "👤",
            "status": "leading",
            "current_task": "Review CEO decisions and approve business opportunities",
            "mission": "Set vision, approve major decisions, and lead Atlas Enterprise.",
            "personality": "decisive, practical, product-focused",
            "goals": "Approve the highest-value businesses|Keep the company focused|Protect cash and time",
            "skills": ["executive decision making", "product strategy", "capital allocation"],
            "tools": ["CEO Workspace", "Business Intelligence", "Decision Log"],
            "performance": 100,
            "workload": 42,
        },
        {
            "name": "Sarah Williams",
            "title": "Chief Operating Officer",
            "department": "Operations",
            "manager": "John Cho",
            "emoji": "🧭",
            "status": "working",
            "current_task": "Coordinate departments for approved businesses",
            "mission": "Turn CEO-approved opportunities into coordinated execution plans.",
            "personality": "organized, calm, process-driven, direct",
            "goals": "Unblock departments|Balance workloads|Escalate CEO decisions early",
            "skills": ["workflow orchestration", "department coordination", "risk escalation", "launch planning"],
            "tools": ["Planner", "Workflow Engine", "Event Bus", "Company Memory"],
            "performance": 98,
            "workload": 76,
        },
        {
            "name": "Ava Chen",
            "title": "Research Director",
            "department": "Research",
            "manager": "Sarah Williams",
            "emoji": "🔎",
            "status": "working",
            "current_task": "Monitor Etsy opportunities and competitor movement",
            "mission": "Find profitable markets before competitors notice them.",
            "personality": "curious, analytical, skeptical",
            "goals": "Discover opportunities|Explain confidence|Track market changes",
            "skills": ["market research", "competitor analysis", "trend detection", "opportunity scoring"],
            "tools": ["Etsy Connector", "Research Engine", "Opportunity Engine"],
            "performance": 94,
            "workload": 64,
        },
        {
            "name": "Noah Brooks",
            "title": "Product Designer",
            "department": "Product",
            "manager": "Sarah Williams",
            "emoji": "🎨",
            "status": "available",
            "current_task": "Generate product concepts from approved opportunities",
            "mission": "Transform market signals into product concepts customers want.",
            "personality": "creative, customer-focused, practical",
            "goals": "Create differentiated products|Improve bundles|Prepare listing drafts",
            "skills": ["product design", "etsy listing draft", "image prompts", "product positioning"],
            "tools": ["AI Product Designer", "Prompt Templates", "Brand Memory"],
            "performance": 92,
            "workload": 51,
        },
        {
            "name": "David Miller",
            "title": "Manufacturing Director",
            "department": "Manufacturing",
            "manager": "Sarah Williams",
            "emoji": "🏭",
            "status": "working",
            "current_task": "Evaluate supplier paths for baseball coaching products",
            "mission": "Find reliable suppliers and reduce production risk.",
            "personality": "practical, cost-conscious, direct",
            "goals": "Find suppliers|Compare quotes|Reduce defects|Improve lead time",
            "skills": ["supplier search", "RFQ", "vendor evaluation", "MOQ analysis", "production planning"],
            "tools": ["Supplier Directory", "Email", "Spreadsheet", "Vendor Memory"],
            "performance": 96,
            "workload": 83,
        },
        {
            "name": "Michael Grant",
            "title": "Chief Financial Officer",
            "department": "Finance",
            "manager": "Sarah Williams",
            "emoji": "💰",
            "status": "waiting",
            "current_task": "Waiting for supplier costs before final unit economics",
            "mission": "Protect margin, cash flow, and pricing discipline.",
            "personality": "conservative, numbers-first, risk-aware",
            "goals": "Calculate margins|Approve pricing|Track cash risk|Model ROI",
            "skills": ["unit economics", "margin analysis", "pricing strategy", "break-even analysis"],
            "tools": ["Finance Engine", "Spreadsheet", "Fee Model", "Accounting Memory"],
            "performance": 97,
            "workload": 58,
        },
        {
            "name": "Emma Rivera",
            "title": "Chief Marketing Officer",
            "department": "Marketing",
            "manager": "Sarah Williams",
            "emoji": "📣",
            "status": "working",
            "current_task": "Prepare SEO and positioning for approved product lines",
            "mission": "Turn good products into strong brands and demand.",
            "personality": "creative, brand-focused, customer-obsessed",
            "goals": "Improve SEO|Create campaigns|Strengthen brand voice|Increase conversion",
            "skills": ["etsy SEO", "brand positioning", "launch copy", "campaign planning"],
            "tools": ["SEO Engine", "Listing Generator", "Pinterest", "Brand Memory"],
            "performance": 93,
            "workload": 69,
        },
        {
            "name": "Olivia Parker",
            "title": "Customer Success Lead",
            "department": "Customer Success",
            "manager": "Sarah Williams",
            "emoji": "💬",
            "status": "available",
            "current_task": "Draft support policies for personalization-heavy products",
            "mission": "Reduce support burden and improve customer trust.",
            "personality": "empathetic, clear, patient",
            "goals": "Write FAQs|Prepare support macros|Detect common issues|Protect reviews",
            "skills": ["FAQ generation", "support templates", "policy drafting", "customer sentiment"],
            "tools": ["Support Docs", "Communications Hub", "Review Memory"],
            "performance": 91,
            "workload": 37,
        },
        {
            "name": "Mia Stone",
            "title": "Executive Assistant",
            "department": "Executive",
            "manager": "John Cho",
            "emoji": "📅",
            "status": "available",
            "current_task": "Prepare CEO briefing and route approvals",
            "mission": "Keep the CEO informed and reduce decision friction.",
            "personality": "concise, organized, proactive",
            "goals": "Summarize decisions|Manage follow-ups|Maintain daily brief",
            "skills": ["daily briefing", "follow-up tracking", "message routing", "calendar coordination"],
            "tools": ["Calendar", "Inbox", "Daily Brief", "Communications Hub"],
            "performance": 95,
            "workload": 44,
        },
    ]

    def __init__(self, session):
        self.session = session

    def ensure_default_workforce(self) -> None:
        departments = self._ensure_departments()

        employees_by_name: dict[str, Employee] = {}
        for spec in self.DEFAULT_EMPLOYEES:
            employee = self.session.query(Employee).filter_by(name=spec["name"]).first()
            if employee is None:
                employee = Employee(
                    name=spec["name"],
                    title=spec["title"],
                    department_id=departments[spec["department"]].id,
                    avatar_emoji=spec["emoji"],
                    status=spec["status"],
                    current_task=spec["current_task"],
                    mission=spec["mission"],
                    personality=spec["personality"],
                    goals=spec["goals"],
                    performance_score=spec["performance"],
                    workload=spec["workload"],
                )
                self.session.add(employee)
                self.session.flush()
            else:
                employee.department_id = departments[spec["department"]].id
                employee.title = spec["title"]
                employee.status = spec["status"]
                employee.current_task = spec["current_task"]
                employee.last_active_at = datetime.utcnow()

            employees_by_name[spec["name"]] = employee

        for spec in self.DEFAULT_EMPLOYEES:
            employee = employees_by_name[spec["name"]]
            manager_name = spec.get("manager")
            if manager_name:
                employee.manager_id = employees_by_name[manager_name].id

            self._sync_values(EmployeeSkill, employee.id, "skill", spec["skills"])
            self._sync_values(EmployeeTool, employee.id, "tool_name", spec["tools"])
            self._ensure_memory(employee, spec)
            self._ensure_goals(employee, spec)
            self._ensure_thought(employee, spec)
            self._ensure_kpis(employee, spec)

        self._ensure_messages(employees_by_name)
        self.session.commit()

    def headquarters_summary(self) -> dict:
        employees = self.session.query(Employee).all()
        working = [e for e in employees if e.status in {"working", "leading"}]
        avg_performance = sum(e.performance_score or 0 for e in employees) / len(employees) if employees else 0
        avg_workload = sum(e.workload or 0 for e in employees) / len(employees) if employees else 0
        messages_waiting = self.session.query(EmployeeMessage).filter_by(status="unread").count()
        return {
            "employees": len(employees),
            "working": len(working),
            "avg_performance": round(avg_performance, 1),
            "avg_workload": round(avg_workload, 1),
            "messages_waiting": messages_waiting,
            "company_health": round(min(100, (avg_performance * 0.7) + ((100 - avg_workload) * 0.3)), 1),
        }

    def _ensure_departments(self) -> dict[str, Department]:
        names = [
            "Executive",
            "Operations",
            "Research",
            "Product",
            "Manufacturing",
            "Finance",
            "Marketing",
            "Customer Success",
        ]
        departments: dict[str, Department] = {}
        for name in names:
            department = self.session.query(Department).filter_by(name=name).first()
            if department is None:
                department = Department(name=name, description=f"Atlas {name} department")
                self.session.add(department)
                self.session.flush()
            departments[name] = department
        return departments

    def _sync_values(self, model, employee_id: int, field_name: str, values: list[str]) -> None:
        existing = self.session.query(model).filter_by(employee_id=employee_id).all()
        existing_values = {getattr(row, field_name) for row in existing}
        for value in values:
            if value not in existing_values:
                self.session.add(model(employee_id=employee_id, **{field_name: value}))

    def _ensure_memory(self, employee: Employee, spec: dict) -> None:
        exists = self.session.query(EmployeeMemory).filter_by(employee_id=employee.id, memory_type="identity").first()
        if exists is None:
            self.session.add(
                EmployeeMemory(
                    employee_id=employee.id,
                    memory_type="identity",
                    content=f"{employee.name} is the {employee.title}. Mission: {spec['mission']}",
                    importance=8,
                )
            )


    def _ensure_goals(self, employee: Employee, spec: dict) -> None:
        if self.session.query(EmployeeGoal).filter_by(employee_id=employee.id).count() > 0:
            return
        raw_goals = [goal.strip() for goal in str(spec.get("goals") or "").split("|") if goal.strip()]
        for idx, goal in enumerate(raw_goals[:4]):
            self.session.add(
                EmployeeGoal(
                    employee_id=employee.id,
                    goal_type="employee",
                    title=goal,
                    description=f"Core responsibility for {employee.title}: {goal}",
                    status="active",
                    priority=max(5, 9 - idx),
                    progress=15.0 if idx == 0 else 0.0,
                )
            )

    def _ensure_thought(self, employee: Employee, spec: dict) -> None:
        if self.session.query(EmployeeThought).filter_by(employee_id=employee.id).count() > 0:
            return
        self.session.add(
            EmployeeThought(
                employee_id=employee.id,
                thought_type="identity",
                content=f"I am {employee.name}, {employee.title}. My current focus is: {employee.current_task}",
                confidence=0.9,
            )
        )

    def _ensure_kpis(self, employee: Employee, spec: dict) -> None:
        if self.session.query(EmployeeKPI).filter_by(employee_id=employee.id).count() > 0:
            return
        self.session.add(EmployeeKPI(employee_id=employee.id, metric_name="performance_score", metric_value=spec["performance"], target_value=95))
        self.session.add(EmployeeKPI(employee_id=employee.id, metric_name="workload", metric_value=spec["workload"], target_value=75))

    def _ensure_messages(self, employees: dict[str, Employee]) -> None:
        if self.session.query(EmployeeMessage).count() > 0:
            return
        messages = [
            ("Sarah Williams", "David Miller", "Supplier Research", "Need supplier paths for the Youth Baseball Coaching product line."),
            ("David Miller", "Michael Grant", "Cost Input Needed", "Supplier assumptions are ready. Finance can begin preliminary unit economics."),
            ("Emma Rivera", "Sarah Williams", "Launch Positioning", "Marketing recommends a premium coaching essentials brand position."),
            ("Mia Stone", "John Cho", "CEO Brief Ready", "The employee directory and company health summary are ready for review."),
        ]
        for sender, recipient, subject, body in messages:
            self.session.add(
                EmployeeMessage(
                    sender_id=employees[sender].id,
                    recipient_id=employees[recipient].id,
                    subject=subject,
                    body=body,
                    status="unread",
                )
            )

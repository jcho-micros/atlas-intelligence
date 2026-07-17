from __future__ import annotations

from datetime import datetime

from app.database.models import AgentTask, Employee, EmployeeMemory, EmployeeMessage, ProductProject
from app.employees.employee_service import EmployeeService


class EmployeeWorkflowService:
    """Routes Atlas work to AI employees and creates visible employee workflows.

    This is intentionally deterministic for now. It does not call an LLM.
    The goal is to make employees behave like a workforce: they receive work,
    message each other, update status, and provide role-based answers.
    """

    AGENT_TO_EMPLOYEE = {
        "CEO Agent": "John Cho",
        "Research Agent": "Ava Chen",
        "Product Designer Agent": "Noah Brooks",
        "Manufacturing Agent": "David Miller",
        "Logistics Agent": "David Miller",
        "Finance Agent": "Michael Grant",
        "Marketing Agent": "Emma Rivera",
        "Customer Success Agent": "Olivia Parker",
        "Accounting Agent": "Michael Grant",
        "Operations Agent": "Sarah Williams",
        "COO Agent": "Sarah Williams",
    }

    def __init__(self, session):
        self.session = session

    def ensure_workflows(self) -> dict:
        """Synchronize agent tasks into employee inboxes and messages."""
        EmployeeService(self.session).ensure_default_workforce()

        routed = 0
        for task in self.session.query(AgentTask).order_by(AgentTask.priority.desc(), AgentTask.created_at.desc()).all():
            employee = self._employee_for_task(task)
            if employee is None:
                continue
            routed += self._route_task_to_employee(task, employee)

        self._update_employee_statuses()
        self._ensure_operating_messages()
        self.session.commit()

        return {
            "tasks_routed": routed,
            "open_tasks": self.session.query(AgentTask).filter(AgentTask.status.notin_(["complete", "completed"])).count(),
            "unread_messages": self.session.query(EmployeeMessage).filter_by(status="unread").count(),
        }

    def mark_message_read(self, message_id: int) -> None:
        message = self.session.query(EmployeeMessage).filter_by(id=message_id).first()
        if message:
            message.status = "read"
            message.read_at = datetime.utcnow()
            self.session.commit()

    def start_task(self, task_id: int) -> None:
        task = self.session.query(AgentTask).filter_by(id=task_id).first()
        if task:
            task.status = "in_progress"
            task.started_at = task.started_at or datetime.utcnow()
            employee = self._employee_for_task(task)
            if employee:
                employee.status = "working"
                employee.current_task = task.title
                employee.last_active_at = datetime.utcnow()
            self.session.commit()

    def complete_task(self, task_id: int) -> None:
        task = self.session.query(AgentTask).filter_by(id=task_id).first()
        if task:
            task.status = "complete"
            task.completed_at = datetime.utcnow()
            employee = self._employee_for_task(task)
            if employee:
                employee.status = "available"
                employee.current_task = "Ready for the next assignment."
                employee.last_active_at = datetime.utcnow()
                self._remember(employee, "work", f"Completed task: {task.title}", importance=6)
            self.session.commit()

    def ask_employee(self, employee_name: str, question: str) -> str:
        employee = self.session.query(Employee).filter_by(name=employee_name).first()
        if employee is None:
            return "I could not find that employee."

        question_lower = (question or "").lower()
        open_tasks = self._tasks_for_employee(employee, open_only=True)
        recent_messages = (
            self.session.query(EmployeeMessage)
            .filter((EmployeeMessage.sender_id == employee.id) | (EmployeeMessage.recipient_id == employee.id))
            .order_by(EmployeeMessage.created_at.desc())
            .limit(3)
            .all()
        )
        memories = (
            self.session.query(EmployeeMemory)
            .filter_by(employee_id=employee.id)
            .order_by(EmployeeMemory.importance.desc(), EmployeeMemory.created_at.desc())
            .limit(3)
            .all()
        )

        if "supplier" in question_lower or "manufactur" in question_lower:
            focus = "I would prioritize supplier reliability, MOQ, landed cost, and lead time before approving production."
        elif "margin" in question_lower or "profit" in question_lower or "price" in question_lower:
            focus = "I would wait for landed cost, then protect margin with a target price that leaves room for Etsy fees, shipping, packaging, and ads."
        elif "market" in question_lower or "seo" in question_lower or "listing" in question_lower:
            focus = "I would position this around youth baseball coaches, personalization, and premium team-ready presentation."
        elif "status" in question_lower or "working" in question_lower:
            focus = employee.current_task or "I am ready for the next assignment."
        else:
            focus = f"My current focus is: {employee.current_task or 'reviewing my inbox and waiting for assignments'}."

        tasks_text = "; ".join([task.title for task in open_tasks[:3]]) or "no open tasks"
        memory_text = "; ".join([memory.content for memory in memories[:2]]) or "no major memory yet"
        message_text = "; ".join([message.subject for message in recent_messages[:2]]) or "no recent messages"

        return (
            f"{employee.name} — {employee.title}\n\n"
            f"Answer: {focus}\n\n"
            f"Open work: {tasks_text}.\n"
            f"Recent messages: {message_text}.\n"
            f"Relevant memory: {memory_text}."
        )

    def _employee_for_task(self, task: AgentTask) -> Employee | None:
        employee_name = self.AGENT_TO_EMPLOYEE.get(task.agent_name)
        if employee_name is None:
            employee_name = self._fallback_employee_name(task.agent_name)
        return self.session.query(Employee).filter_by(name=employee_name).first()

    def _fallback_employee_name(self, agent_name: str) -> str:
        lower = (agent_name or "").lower()
        if "manufact" in lower or "logistics" in lower:
            return "David Miller"
        if "finance" in lower or "account" in lower:
            return "Michael Grant"
        if "marketing" in lower:
            return "Emma Rivera"
        if "research" in lower:
            return "Ava Chen"
        if "product" in lower:
            return "Noah Brooks"
        if "customer" in lower or "support" in lower:
            return "Olivia Parker"
        if "ceo" in lower:
            return "John Cho"
        return "Sarah Williams"

    def _route_task_to_employee(self, task: AgentTask, employee: Employee) -> int:
        subject = f"Assignment: {task.title}"
        existing = (
            self.session.query(EmployeeMessage)
            .filter_by(recipient_id=employee.id, subject=subject)
            .first()
        )
        if existing:
            return 0

        sarah = self.session.query(Employee).filter_by(name="Sarah Williams").first()
        project = self.session.query(ProductProject).filter_by(id=task.project_id).first()
        project_name = project.project_name if project else "Atlas project"
        body = (
            f"Please handle this {task.task_type} assignment for {project_name}. "
            f"Priority {task.priority}. Details: {task.description or task.title}"
        )
        self.session.add(
            EmployeeMessage(
                sender_id=sarah.id if sarah else None,
                recipient_id=employee.id,
                subject=subject,
                body=body,
                status="unread",
            )
        )
        self._remember(employee, "assignment", f"Assigned to {task.title} for {project_name}", importance=7)
        return 1

    def _update_employee_statuses(self) -> None:
        for employee in self.session.query(Employee).all():
            open_tasks = self._tasks_for_employee(employee, open_only=True)
            unread = self.session.query(EmployeeMessage).filter_by(recipient_id=employee.id, status="unread").count()
            if open_tasks:
                employee.status = "working"
                employee.current_task = open_tasks[0].title
                employee.workload = min(100, 50 + (len(open_tasks) * 12) + (unread * 3))
            elif unread:
                employee.status = "waiting"
                employee.current_task = "Review inbox messages."
                employee.workload = min(100, 35 + (unread * 5))
            elif employee.name == "John Cho":
                employee.status = "leading"
                employee.current_task = "Review CEO decisions and approve business opportunities"
            else:
                employee.status = "available"
                employee.current_task = "Ready for the next assignment."
                employee.workload = max(20, employee.workload * 0.85)
            employee.last_active_at = datetime.utcnow()

    def _tasks_for_employee(self, employee: Employee, open_only: bool = False) -> list[AgentTask]:
        agent_names = [agent for agent, emp_name in self.AGENT_TO_EMPLOYEE.items() if emp_name == employee.name]
        query = self.session.query(AgentTask)
        if agent_names:
            query = query.filter(AgentTask.agent_name.in_(agent_names))
        else:
            query = query.filter(AgentTask.agent_name == employee.title)
        if open_only:
            query = query.filter(AgentTask.status.notin_(["complete", "completed"]))
        return query.order_by(AgentTask.priority.desc(), AgentTask.created_at.desc()).all()

    def _ensure_operating_messages(self) -> None:
        employees = {employee.name: employee for employee in self.session.query(Employee).all()}
        threads = [
            ("Sarah Williams", "Ava Chen", "Research Priorities", "Please keep surfacing opportunities that can become full product lines, not just single SKUs."),
            ("Sarah Williams", "David Miller", "Manufacturing Workload", "Please route supplier risks to Michael before we recommend launch."),
            ("David Miller", "Michael Grant", "Landed Cost Needed", "I will send preliminary supplier assumptions so Finance can model margins."),
            ("Michael Grant", "Emma Rivera", "Pricing Guardrails", "Marketing can use premium positioning, but we need margin protection before launch."),
            ("Mia Stone", "John Cho", "Executive Summary", "Employee workflows are active. Sarah is routing approved project work to department owners."),
        ]
        for sender_name, recipient_name, subject, body in threads:
            sender = employees.get(sender_name)
            recipient = employees.get(recipient_name)
            if sender is None or recipient is None:
                continue
            exists = self.session.query(EmployeeMessage).filter_by(sender_id=sender.id, recipient_id=recipient.id, subject=subject).first()
            if not exists:
                self.session.add(EmployeeMessage(sender_id=sender.id, recipient_id=recipient.id, subject=subject, body=body, status="unread"))

    def _remember(self, employee: Employee, memory_type: str, content: str, importance: int = 5) -> None:
        exists = self.session.query(EmployeeMemory).filter_by(employee_id=employee.id, memory_type=memory_type, content=content).first()
        if exists is None:
            self.session.add(EmployeeMemory(employee_id=employee.id, memory_type=memory_type, content=content, importance=importance))

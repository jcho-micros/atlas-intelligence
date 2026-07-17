from __future__ import annotations

from datetime import datetime

from app.database.models import (
    AgentTask,
    Employee,
    EmployeeDecision,
    EmployeeGoal,
    EmployeeMemory,
    EmployeeMessage,
    EmployeeReflection,
    EmployeeThought,
)
from app.employees.employee_service import EmployeeService
from app.employees.mind import EmployeeMind, MindDecision
from app.employees.workflow_service import EmployeeWorkflowService


class EmployeeRuntimeService:
    """Runs one work cycle for Atlas employees.

    v2.3.1 introduces the Employee Mind pattern: every cycle creates a thought,
    an explainable decision, and a reflection/memory artifact.
    """

    def __init__(self, session):
        self.session = session
        self.workflow = EmployeeWorkflowService(session)

    def run_cycle(self, max_employees: int = 8) -> dict:
        EmployeeService(self.session).ensure_default_workforce()
        self.workflow.ensure_workflows()

        actions: list[dict] = []
        employees = (
            self.session.query(Employee)
            .order_by(Employee.workload.desc(), Employee.last_active_at.asc())
            .limit(max_employees)
            .all()
        )

        for employee in employees:
            tasks = self._open_tasks_for(employee)
            messages = self._recent_messages_for(employee)
            memories = self._recent_memories_for(employee)
            goals = self._active_goals_for(employee)

            decision = EmployeeMind(employee).think(tasks, messages, memories, goals)
            self._apply_decision(employee, decision, tasks, messages)
            actions.append(
                {
                    "employee": employee.name,
                    "title": employee.title,
                    "phase": decision.phase,
                    "action": decision.action,
                    "thought": decision.thought,
                    "summary": decision.summary,
                    "rationale": decision.rationale,
                    "next_action": decision.next_action,
                    "confidence": decision.confidence,
                }
            )

        self.session.commit()
        return {
            "employees_processed": len(actions),
            "actions": actions,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _open_tasks_for(self, employee: Employee) -> list[AgentTask]:
        agent_names = [agent for agent, emp_name in self.workflow.AGENT_TO_EMPLOYEE.items() if emp_name == employee.name]
        query = self.session.query(AgentTask)
        if agent_names:
            query = query.filter(AgentTask.agent_name.in_(agent_names))
        else:
            query = query.filter(AgentTask.agent_name == employee.title)
        return (
            query.filter(AgentTask.status.notin_(["complete", "completed"]))
            .order_by(AgentTask.priority.desc(), AgentTask.created_at.asc())
            .all()
        )

    def _recent_messages_for(self, employee: Employee) -> list[EmployeeMessage]:
        return (
            self.session.query(EmployeeMessage)
            .filter_by(recipient_id=employee.id)
            .order_by(EmployeeMessage.created_at.desc())
            .limit(5)
            .all()
        )

    def _recent_memories_for(self, employee: Employee) -> list[EmployeeMemory]:
        return (
            self.session.query(EmployeeMemory)
            .filter_by(employee_id=employee.id)
            .order_by(EmployeeMemory.importance.desc(), EmployeeMemory.created_at.desc())
            .limit(5)
            .all()
        )

    def _active_goals_for(self, employee: Employee) -> list[EmployeeGoal]:
        return (
            self.session.query(EmployeeGoal)
            .filter_by(employee_id=employee.id, status="active")
            .order_by(EmployeeGoal.priority.desc(), EmployeeGoal.created_at.asc())
            .limit(5)
            .all()
        )

    def _apply_decision(
        self,
        employee: Employee,
        decision: MindDecision,
        tasks: list[AgentTask],
        messages: list[EmployeeMessage],
    ) -> None:
        employee.last_active_at = datetime.utcnow()
        employee.status = decision.phase
        employee.current_task = decision.summary

        self._record_thought(employee, decision)
        self._record_decision(employee, decision)

        if decision.action == "advance_task" and tasks:
            task = tasks[0]
            if task.status == "pending":
                task.status = "in_progress"
                task.started_at = task.started_at or datetime.utcnow()
            else:
                task.status = "complete"
                task.completed_at = datetime.utcnow()
                self._record_reflection(employee, f"Completed {task.title}", decision.next_action, importance=7)
            self._remember(employee, "runtime", f"{decision.summary}. Next: {decision.next_action}", importance=7)
            self._message_sarah(employee, f"Runtime update from {employee.name}", decision.summary)
            return

        if decision.action == "review_message":
            unread = [message for message in messages if message.status == "unread"]
            if unread:
                unread[0].status = "read"
                unread[0].read_at = datetime.utcnow()
            self._remember(employee, "inbox", decision.summary, importance=5)
            return

        if decision.action in {"reflect", "review_goal"}:
            self._record_reflection(employee, decision.summary, decision.rationale, importance=5)
            self._remember(employee, "reflection", decision.thought, importance=5)
            return

    def _record_thought(self, employee: Employee, decision: MindDecision) -> None:
        self.session.add(
            EmployeeThought(
                employee_id=employee.id,
                thought_type=decision.phase,
                content=decision.thought,
                confidence=decision.confidence,
            )
        )

    def _record_decision(self, employee: Employee, decision: MindDecision) -> None:
        self.session.add(
            EmployeeDecision(
                employee_id=employee.id,
                decision_type=decision.action,
                title=decision.summary,
                reasoning=decision.rationale,
                outcome=decision.next_action,
                confidence=decision.confidence,
            )
        )

    def _record_reflection(self, employee: Employee, content: str, lesson: str, importance: int = 5) -> None:
        self.session.add(
            EmployeeReflection(
                employee_id=employee.id,
                content=content,
                lesson=lesson,
                importance=importance,
            )
        )

    def _remember(self, employee: Employee, memory_type: str, content: str, importance: int = 5) -> None:
        existing = (
            self.session.query(EmployeeMemory)
            .filter_by(employee_id=employee.id, content=content)
            .first()
        )
        if existing:
            existing.last_used_at = datetime.utcnow()
            return
        self.session.add(
            EmployeeMemory(
                employee_id=employee.id,
                memory_type=memory_type,
                content=content,
                importance=importance,
            )
        )

    def _message_sarah(self, employee: Employee, subject: str, body: str) -> None:
        sarah = self.session.query(Employee).filter_by(name="Sarah Williams").first()
        if sarah is None or employee.id == sarah.id:
            return
        self.session.add(
            EmployeeMessage(
                sender_id=employee.id,
                recipient_id=sarah.id,
                subject=subject,
                body=body,
                status="unread",
            )
        )

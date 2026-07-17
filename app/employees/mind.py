from dataclasses import dataclass

from app.database.models import AgentTask, Employee, EmployeeGoal, EmployeeMemory, EmployeeMessage


@dataclass
class MindDecision:
    employee_name: str
    phase: str
    action: str
    thought: str
    summary: str
    rationale: str
    next_action: str
    confidence: float = 0.8


class EmployeeMind:
    """Local deterministic reasoning layer for Atlas employees.

    v2.3.1 deliberately keeps this local and explainable. Later releases can
    swap the reasoning policy for an LLM provider without changing the employee
    identity, inbox, memory, or workspace models.
    """

    def __init__(self, employee: Employee):
        self.employee = employee
        self.department = employee.department.name if employee.department else "General"

    def think(
        self,
        tasks: list[AgentTask],
        messages: list[EmployeeMessage],
        memories: list[EmployeeMemory],
        goals: list[EmployeeGoal],
    ) -> MindDecision:
        priority_goal = goals[0] if goals else None
        open_messages = [message for message in messages if message.status == "unread"]

        if tasks:
            task = tasks[0]
            return MindDecision(
                employee_name=self.employee.name,
                phase="working",
                action="advance_task",
                thought=self._role_thought(task.title, priority_goal),
                summary=f"Advanced assigned work: {task.title}",
                rationale=self._task_rationale(task, priority_goal),
                next_action=self._next_action_for_task(task),
                confidence=0.88,
            )

        if open_messages:
            message = open_messages[0]
            return MindDecision(
                employee_name=self.employee.name,
                phase="planning",
                action="review_message",
                thought=f"I need to understand {message.sender.name if message.sender else 'Atlas'}'s request before committing work.",
                summary=f"Reviewed message: {message.subject}",
                rationale="Unread messages can contain blockers, approvals, or inputs from another employee.",
                next_action="Reply or convert the message into a task if it requires follow-up.",
                confidence=0.78,
            )

        if priority_goal:
            return MindDecision(
                employee_name=self.employee.name,
                phase="thinking",
                action="review_goal",
                thought=self._goal_thought(priority_goal),
                summary=f"Reviewed active goal: {priority_goal.title}",
                rationale="No urgent inbox item exists, so the employee reviewed goals and prepared next work.",
                next_action="Wait for COO assignment or create a supporting task when autonomy is enabled.",
                confidence=0.72,
            )

        if memories:
            return MindDecision(
                employee_name=self.employee.name,
                phase="learning",
                action="reflect",
                thought="I am reviewing prior lessons so future work starts with better context.",
                summary="Reflected on recent memory and stayed ready for new work.",
                rationale="Reflection keeps employee memory active even when no task is assigned.",
                next_action="Stand by for new company priorities.",
                confidence=0.65,
            )

        return MindDecision(
            employee_name=self.employee.name,
            phase="waiting",
            action="standby",
            thought="I do not have enough current work to act, so I am waiting for Sarah or the CEO to assign priority.",
            summary="Standing by for assignment.",
            rationale="No open tasks, messages, goals, or memories were available for this cycle.",
            next_action="Receive a goal or task from the COO.",
            confidence=0.55,
        )

    def _role_thought(self, task_title: str, goal: EmployeeGoal | None) -> str:
        title = self.employee.title.lower()
        goal_text = f" while supporting {goal.title}" if goal else ""
        if "operating" in title or "coo" in title:
            return f"I am coordinating dependencies and making sure the right employee owns {task_title}{goal_text}."
        if "manufacturing" in title:
            return f"I am checking supplier, MOQ, lead time, and quality risk before recommending a manufacturing path."
        if "financial" in title or "finance" in self.department.lower():
            return f"I am protecting margin and cash exposure before approving {task_title}."
        if "marketing" in title:
            return f"I am turning the product strategy into a clear offer customers will understand."
        if "research" in title:
            return f"I am validating whether market signals are strong enough to justify more execution work."
        if "assistant" in title:
            return f"I am reducing CEO decision friction by summarizing the most important next action."
        return f"I am advancing {task_title} with my department context."

    def _goal_thought(self, goal: EmployeeGoal) -> str:
        if self.department == "Operations":
            return f"I am checking which departments must move first to achieve: {goal.title}."
        if self.department == "Manufacturing":
            return f"I am thinking about supplier risk and production readiness for: {goal.title}."
        if self.department == "Finance":
            return f"I am thinking about margin, pricing, and cash requirements for: {goal.title}."
        if self.department == "Marketing":
            return f"I am thinking about the buyer message and launch positioning for: {goal.title}."
        return f"I am reviewing how my role contributes to: {goal.title}."

    def _task_rationale(self, task: AgentTask, goal: EmployeeGoal | None) -> str:
        parts = ["The task is open and has the highest available priority for this employee."]
        if goal:
            parts.append(f"It supports the active goal: {goal.title}.")
        if task.priority >= 8:
            parts.append("Priority is high, so it should move before lower-value work.")
        return " ".join(parts)

    def _next_action_for_task(self, task: AgentTask) -> str:
        if "supplier" in task.title.lower() or "manufacturing" in task.agent_name.lower():
            return "Compare supplier options and send preliminary cost inputs to Finance."
        if "finance" in task.agent_name.lower() or "margin" in task.title.lower():
            return "Update unit economics and report margin risk to Sarah."
        if "marketing" in task.agent_name.lower():
            return "Draft positioning, tags, and launch copy for CEO review."
        return "Report progress to Sarah and update memory with the decision context."

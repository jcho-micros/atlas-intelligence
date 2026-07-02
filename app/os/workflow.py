from dataclasses import dataclass, field

from app.os.enums import AgentName, ProjectStatus, TaskStatus


@dataclass
class ProductProject:
    name: str
    opportunity_keyword: str
    status: ProjectStatus = ProjectStatus.CANDIDATE
    score: float = 0.0
    recommendation: str = "REVIEW"


@dataclass
class AgentTask:
    agent: AgentName
    title: str
    project_name: str
    status: TaskStatus = TaskStatus.TODO
    notes: str = ""


@dataclass
class WorkflowEngine:
    tasks: list[AgentTask] = field(default_factory=list)

    def approve_project(self, project: ProductProject) -> ProductProject:
        project.status = ProjectStatus.APPROVED
        self.tasks.extend(
            [
                AgentTask(AgentName.PRODUCT_DESIGNER, "Generate product brief", project.name),
                AgentTask(AgentName.FINANCE, "Estimate unit economics", project.name),
                AgentTask(AgentName.MANUFACTURING, "Find supplier options", project.name),
                AgentTask(AgentName.MARKETING, "Draft launch assets", project.name),
            ]
        )
        return project

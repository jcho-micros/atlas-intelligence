from enum import StrEnum


class ProjectStatus(StrEnum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    PRODUCT_DESIGN = "product_design"
    MANUFACTURING = "manufacturing"
    FINANCE_REVIEW = "finance_review"
    MARKETING = "marketing"
    LAUNCH_READY = "launch_ready"
    LAUNCHED = "launched"
    MONITORING = "monitoring"
    PAUSED = "paused"
    REJECTED = "rejected"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


class AgentName(StrEnum):
    CEO = "ceo"
    RESEARCH = "research"
    PRODUCT_DESIGNER = "product_designer"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    MARKETING = "marketing"
    CUSTOMER_SUCCESS = "customer_success"
    ACCOUNTING = "accounting"
    LAUNCH = "launch"

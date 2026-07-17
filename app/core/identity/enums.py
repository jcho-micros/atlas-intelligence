from enum import Enum


class IdentityType(str, Enum):
    HUMAN = "human"
    AI_EMPLOYEE = "ai_employee"
    SERVICE_ACCOUNT = "service_account"


class IdentityStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class Department(str, Enum):
    EXECUTIVE = "executive"
    ENGINEERING = "engineering"
    FINANCE = "finance"
    OPERATIONS = "operations"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    RESEARCH = "research"

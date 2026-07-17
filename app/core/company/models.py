from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class Company:
    id: int
    name: str
    legal_name: str | None = None
    status: str = "active"
    timezone: str = "America/New_York"
    currency: str = "USD"
    industry: str | None = None
    contact_email: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Department:
    id: int
    company_id: int
    name: str
    code: str
    status: str = "active"
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Team:
    id: int
    company_id: int
    department_id: int
    name: str
    code: str
    status: str = "active"
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
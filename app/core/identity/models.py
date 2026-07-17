from dataclasses import dataclass
from datetime import datetime

from app.core.identity.enums import Department, IdentityStatus, IdentityType


@dataclass(frozen=True, slots=True)
class Identity:
    """Persistence-independent representation of an Atlas identity."""

    id: int
    organization_id: int
    display_name: str
    identity_type: IdentityType
    status: IdentityStatus
    email: str | None = None
    system_name: str | None = None
    department: Department | None = None
    manager_id: int | None = None
    employee_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def can_act(self) -> bool:
        return self.status is IdentityStatus.ACTIVE

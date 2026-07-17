from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.core.identity.enums import Department, IdentityStatus, IdentityType
from app.core.identity.exceptions import (
    DuplicateIdentity,
    IdentityDisabled,
    IdentityNotFound,
    InvalidManager,
)
from app.core.identity.models import Identity
from app.database.models import UserIdentity


class IdentityService:
    """Lifecycle service for human, AI, and service identities."""

    def __init__(self, session):
        self.session = session

    def create_identity(
        self,
        *,
        organization_id: int,
        display_name: str,
        identity_type: IdentityType,
        email: str | None = None,
        system_name: str | None = None,
        department: Department | None = None,
        manager_id: int | None = None,
        employee_id: int | None = None,
    ) -> Identity:
        display_name = display_name.strip()
        normalized_email = self._normalize_email(email)
        normalized_system_name = self._normalize_system_name(system_name)

        if not display_name:
            raise ValueError("display_name is required")
        if identity_type is IdentityType.HUMAN and not normalized_email:
            raise ValueError("Human identities require an email")
        if identity_type is not IdentityType.HUMAN and not (normalized_email or normalized_system_name):
            raise ValueError("AI and service identities require an email or system_name")

        self._ensure_unique(organization_id, normalized_email, normalized_system_name)
        if manager_id is not None:
            self._validate_manager(organization_id, manager_id)

        record = UserIdentity(
            organization_id=organization_id,
            employee_id=employee_id,
            email=normalized_email,
            system_name=normalized_system_name,
            display_name=display_name,
            identity_type=identity_type.value,
            status=IdentityStatus.ACTIVE.value,
            department=department.value if department else None,
            manager_id=manager_id,
        )
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateIdentity("Identity already exists in this organization") from exc
        return self._to_domain(record)

    def get_identity(self, identity_id: int) -> Identity:
        return self._to_domain(self._get_record(identity_id))

    def list_identities(
        self,
        *,
        organization_id: int,
        status: IdentityStatus | None = None,
        identity_type: IdentityType | None = None,
        department: Department | None = None,
    ) -> list[Identity]:
        query = self.session.query(UserIdentity).filter_by(organization_id=organization_id)
        if status:
            query = query.filter_by(status=status.value)
        if identity_type:
            query = query.filter_by(identity_type=identity_type.value)
        if department:
            query = query.filter_by(department=department.value)
        return [self._to_domain(row) for row in query.order_by(UserIdentity.display_name).all()]

    def update_identity(
        self,
        identity_id: int,
        *,
        display_name: str | None = None,
        email: str | None = None,
        system_name: str | None = None,
        department: Department | None = None,
        manager_id: int | None = None,
    ) -> Identity:
        record = self._get_record(identity_id)
        normalized_email = self._normalize_email(email) if email is not None else record.email
        normalized_system_name = (
            self._normalize_system_name(system_name) if system_name is not None else record.system_name
        )
        self._ensure_unique(record.organization_id, normalized_email, normalized_system_name, exclude_id=record.id)

        if display_name is not None:
            if not display_name.strip():
                raise ValueError("display_name cannot be empty")
            record.display_name = display_name.strip()
        if email is not None:
            record.email = normalized_email
        if system_name is not None:
            record.system_name = normalized_system_name
        if department is not None:
            record.department = department.value
        if manager_id is not None:
            if manager_id == identity_id:
                raise InvalidManager("An identity cannot manage itself")
            self._validate_manager(record.organization_id, manager_id)
            record.manager_id = manager_id
        record.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return self._to_domain(record)

    def activate_identity(self, identity_id: int) -> Identity:
        return self._set_status(identity_id, IdentityStatus.ACTIVE)

    def suspend_identity(self, identity_id: int) -> Identity:
        return self._set_status(identity_id, IdentityStatus.SUSPENDED)

    def disable_identity(self, identity_id: int) -> Identity:
        return self._set_status(identity_id, IdentityStatus.DISABLED)

    def require_active(self, identity_id: int) -> Identity:
        identity = self.get_identity(identity_id)
        if not identity.can_act:
            raise IdentityDisabled(f"Identity {identity_id} is {identity.status.value}")
        return identity

    def assign_department(self, identity_id: int, department: Department) -> Identity:
        return self.update_identity(identity_id, department=department)

    def assign_manager(self, identity_id: int, manager_id: int) -> Identity:
        return self.update_identity(identity_id, manager_id=manager_id)

    def _set_status(self, identity_id: int, status: IdentityStatus) -> Identity:
        record = self._get_record(identity_id)
        record.status = status.value
        record.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return self._to_domain(record)

    def _get_record(self, identity_id: int) -> UserIdentity:
        record = self.session.query(UserIdentity).filter_by(id=identity_id).first()
        if record is None:
            raise IdentityNotFound(f"Identity {identity_id} was not found")
        return record

    def _validate_manager(self, organization_id: int, manager_id: int) -> None:
        manager = self.session.query(UserIdentity).filter_by(id=manager_id).first()
        if manager is None or manager.organization_id != organization_id:
            raise InvalidManager("Manager must belong to the same organization")
        if manager.status != IdentityStatus.ACTIVE.value:
            raise InvalidManager("Manager must be active")

    def _ensure_unique(
        self,
        organization_id: int,
        email: str | None,
        system_name: str | None,
        *,
        exclude_id: int | None = None,
    ) -> None:
        checks = []
        if email:
            checks.append(UserIdentity.email == email)
        if system_name:
            checks.append(UserIdentity.system_name == system_name)
        if not checks:
            return
        query = self.session.query(UserIdentity).filter(
            UserIdentity.organization_id == organization_id,
            or_(*checks),
        )
        if exclude_id is not None:
            query = query.filter(UserIdentity.id != exclude_id)
        if query.first() is not None:
            raise DuplicateIdentity("Email or system_name already exists in this organization")

    @staticmethod
    def _normalize_email(value: str | None) -> str | None:
        normalized = value.strip().lower() if value else None
        return normalized or None

    @staticmethod
    def _normalize_system_name(value: str | None) -> str | None:
        normalized = value.strip().lower().replace(" ", "-") if value else None
        return normalized or None

    @staticmethod
    def _to_domain(record: UserIdentity) -> Identity:
        return Identity(
            id=record.id,
            organization_id=record.organization_id,
            display_name=record.display_name,
            identity_type=IdentityType(record.identity_type),
            status=IdentityStatus(record.status),
            email=record.email,
            system_name=record.system_name,
            department=Department(record.department) if record.department else None,
            manager_id=record.manager_id,
            employee_id=record.employee_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

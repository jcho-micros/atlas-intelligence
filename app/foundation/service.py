from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.database.models import (
    AccessRole,
    AuditEvent,
    Notification,
    Organization,
    Permission,
    RolePermission,
    UserIdentity,
    UserRole,
)


class PermissionDenied(RuntimeError):
    """Raised when an identity attempts an unauthorized action."""


class FoundationService:
    """Production-facing foundation services for Atlas Enterprise."""

    DEFAULT_PERMISSIONS = {
        "company.read": "View company configuration and workforce data",
        "company.manage": "Change company configuration",
        "employees.read": "View employees and departments",
        "employees.manage": "Create and update employees",
        "workflows.execute": "Start and operate workflows",
        "approvals.decide": "Approve or reject gated decisions",
        "finance.read": "View financial analysis",
        "finance.manage": "Change financial assumptions and approvals",
        "audit.read": "View the company audit trail",
        "notifications.manage": "Manage notifications",
        "access.manage": "Manage identities, roles, and permissions",
    }

    DEFAULT_ROLES = {
        "Owner": set(DEFAULT_PERMISSIONS),
        "Executive": {
            "company.read", "employees.read", "employees.manage", "workflows.execute",
            "approvals.decide", "finance.read", "finance.manage", "audit.read",
            "notifications.manage",
        },
        "Manager": {
            "company.read", "employees.read", "workflows.execute", "approvals.decide",
            "finance.read", "notifications.manage",
        },
        "Employee": {"company.read", "employees.read", "workflows.execute", "finance.read"},
        "Viewer": {"company.read", "employees.read", "finance.read"},
    }

    def __init__(self, session):
        self.session = session

    def bootstrap(
        self,
        organization_name: str = "Atlas Enterprise",
        slug: str = "atlas-enterprise",
        owner_email: str = "john@atlas.local",
        owner_name: str = "John Cho",
    ) -> dict[str, Any]:
        organization = self.session.query(Organization).filter_by(slug=slug).first()
        if organization is None:
            organization = Organization(name=organization_name, slug=slug)
            self.session.add(organization)
            self.session.flush()

        permissions: dict[str, Permission] = {}
        for code, description in self.DEFAULT_PERMISSIONS.items():
            permission = self.session.query(Permission).filter_by(code=code).first()
            if permission is None:
                permission = Permission(code=code, description=description)
                self.session.add(permission)
                self.session.flush()
            permissions[code] = permission

        roles: dict[str, AccessRole] = {}
        for role_name, permission_codes in self.DEFAULT_ROLES.items():
            role = self.session.query(AccessRole).filter_by(
                organization_id=organization.id, name=role_name
            ).first()
            if role is None:
                role = AccessRole(
                    organization_id=organization.id,
                    name=role_name,
                    description=f"Atlas {role_name} role",
                    is_system=True,
                )
                self.session.add(role)
                self.session.flush()
            roles[role_name] = role
            existing_ids = {
                row[0]
                for row in self.session.query(RolePermission.permission_id)
                .filter(RolePermission.role_id == role.id)
                .all()
            }
            for code in permission_codes:
                permission_id = permissions[code].id
                if permission_id not in existing_ids:
                    self.session.add(RolePermission(role_id=role.id, permission_id=permission_id))
                    existing_ids.add(permission_id)
            self.session.flush()

        owner = self.session.query(UserIdentity).filter_by(
            organization_id=organization.id, email=owner_email.lower()
        ).first()
        if owner is None:
            owner = UserIdentity(
                organization_id=organization.id,
                email=owner_email.lower(),
                display_name=owner_name,
                identity_type="human",
                status="active",
            )
            self.session.add(owner)
            self.session.flush()

        if not self.session.query(UserRole).filter_by(identity_id=owner.id, role_id=roles["Owner"].id).first():
            self.session.add(UserRole(identity_id=owner.id, role_id=roles["Owner"].id))

        self.session.flush()
        self.record_audit(organization.id, "foundation.bootstrap", "organization", str(organization.id), owner)
        self.session.commit()
        return {"organization": organization, "owner": owner, "roles": roles}

    def permissions_for(self, identity_id: int) -> set[str]:
        rows = (
            self.session.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(AccessRole, AccessRole.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == AccessRole.id)
            .filter(UserRole.identity_id == identity_id)
            .all()
        )
        return {row[0] for row in rows}

    def can(self, identity_id: int, permission_code: str) -> bool:
        identity = self.session.query(UserIdentity).filter_by(id=identity_id, status="active").first()
        return bool(identity and permission_code in self.permissions_for(identity_id))

    def require(self, identity_id: int, permission_code: str) -> None:
        if not self.can(identity_id, permission_code):
            identity = self.session.query(UserIdentity).filter_by(id=identity_id).first()
            if identity:
                self.record_audit(
                    identity.organization_id,
                    "access.denied",
                    "permission",
                    permission_code,
                    identity,
                    outcome="denied",
                )
                self.session.commit()
            raise PermissionDenied(f"Permission required: {permission_code}")

    def notify(
        self,
        organization_id: int,
        title: str,
        body: str = "",
        recipient_id: int | None = None,
        severity: str = "info",
        notification_type: str = "info",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> Notification:
        notification = Notification(
            organization_id=organization_id,
            recipient_id=recipient_id,
            title=title,
            body=body,
            severity=severity,
            notification_type=notification_type,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        self.session.add(notification)
        self.session.flush()
        return notification

    def mark_notification_read(self, notification_id: int, identity_id: int) -> bool:
        notification = self.session.query(Notification).filter_by(id=notification_id).first()
        if notification is None or notification.recipient_id not in {None, identity_id}:
            return False
        notification.status = "read"
        notification.read_at = datetime.utcnow()
        self.record_audit(
            notification.organization_id,
            "notification.read",
            "notification",
            str(notification.id),
            self.session.query(UserIdentity).filter_by(id=identity_id).first(),
        )
        self.session.commit()
        return True

    def record_audit(
        self,
        organization_id: int,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        actor: UserIdentity | None = None,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            organization_id=organization_id,
            actor_identity_id=actor.id if actor else None,
            actor_name=actor.display_name if actor else "system",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            details_json=json.dumps(details or {}, sort_keys=True, default=str),
        )
        self.session.add(event)
        self.session.flush()
        return event

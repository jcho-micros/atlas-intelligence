# Atlas Role-Based Access Control

Atlas RBAC is implemented by `FoundationService` and uses the existing
`AccessRole`, `Permission`, `RolePermission`, and `UserRole` tables.

## Default roles

- Owner: all permissions
- Executive: company operations, employee management, approvals, finance, audit, and notifications
- Manager: workflow execution, approvals, finance visibility, and notifications
- Employee: company and employee visibility, workflow execution, and finance visibility
- Viewer: read-only company, employee, and finance visibility

## Automatic workforce mapping

- John Cho -> Owner
- Titles beginning with `Chief` -> Executive
- Titles containing `Director`, `Lead`, or `Manager` -> Manager
- Other workforce identities -> Employee

Workforce synchronization is idempotent and preserves custom, non-system roles.

## Management rules

- Role changes can optionally require an actor with `access.manage`.
- Assignments and revocations are written to the audit log.
- An organization cannot remove its last active Owner.
- Disabled or suspended identities cannot pass permission checks.

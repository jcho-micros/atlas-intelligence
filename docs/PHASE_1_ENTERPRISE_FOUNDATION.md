# Phase 1 — Enterprise Foundation

This increment establishes the controls Atlas needs to operate like a real company rather than a collection of disconnected agents.

## Delivered

- Organization configuration with timezone and JSON settings
- Human and AI identities
- Role-based access control (RBAC)
- Reusable permission checks (`can` and `require`)
- In-app notification records with read lifecycle
- Append-only audit events for security and operational actions
- Idempotent bootstrap for the default Atlas company and owner

## Default roles

- Owner — full system authority
- Executive — company operations, approvals, finance, and audit visibility
- Manager — workflow and approval authority
- Employee — standard operational access
- Viewer — read-only access

## Usage

```python
from app.foundation import FoundationService

foundation = FoundationService(session)
context = foundation.bootstrap()
owner = context["owner"]

foundation.require(owner.id, "company.manage")
foundation.notify(
    context["organization"].id,
    "Decision required",
    "Review the proposed launch budget.",
    recipient_id=owner.id,
    notification_type="approval",
    severity="warning",
)
session.commit()
```

## Next integration step

Route dashboard actions and workflow execution through `FoundationService.require(...)`, then expose notifications and audit history in the CEO workspace.

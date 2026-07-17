# Identity Service

The Identity Service owns the lifecycle of actors that can operate inside Atlas.
It builds on the existing `user_identities` table used by the enterprise foundation.

## Supported identity types

- `human`
- `ai_employee`
- `service_account`

## Supported states

- `active`
- `suspended`
- `disabled`

Only active identities may act. Human identities require an email. AI employees and
service accounts require either an email or a stable `system_name`.

## Package layout

- `app/core/identity/enums.py` — stable domain values
- `app/core/identity/models.py` — persistence-independent domain object
- `app/core/identity/service.py` — lifecycle and validation rules
- `app/core/identity/exceptions.py` — domain-specific failures

## Database migration

Apply the migration to an existing database with:

```bash
python -m alembic upgrade head
```

New test databases created through `DatabaseManager.initialize()` receive the current
schema automatically.

## Employee integration

`EmployeeService.ensure_default_workforce()` now synchronizes the workforce with the canonical identity registry.

- John Cho is linked to the human owner identity (`john@atlas.local`).
- Every other default workforce member receives an `ai_employee` identity.
- Identity `employee_id` links are one-to-one and enforced by the database.
- Employee department and manager relationships are mirrored onto the identity.
- Re-running workforce initialization is idempotent and does not create duplicate identities.

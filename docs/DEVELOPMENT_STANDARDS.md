# Development Standards

## Release Process

Each release should include:

- Complete replacement ZIP
- Release notes
- Upgrade guide
- Validation checklist
- Database migration notes
- Suggested Git commit message

## Git Workflow

Recommended branch naming:

```text
feature/<short-feature-name>
fix/<short-fix-name>
release/<version>
```

## Database Changes

Use Alembic for every schema change.

```bash
python -m alembic revision --autogenerate -m "description"
python -m alembic upgrade head
```

Review generated migrations before applying.

## Configuration

Secrets belong in `.env` only.

`.env.example` should contain empty placeholders.

Never commit `.env`.

## Code Organization

Business logic should live in services/core modules, not in Streamlit UI code.

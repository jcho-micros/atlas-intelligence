# Release Notes Template

## Version

Atlas OS vX.Y.Z

## Theme

Short release theme.

## New Features

- Feature 1
- Feature 2

## Changed

- Change 1

## Database

- Migration required: yes/no
- Migration command:

```bash
python -m alembic upgrade head
```

## Validation

```bash
python main.py
python atlas.py dashboard
pytest
```

## Suggested Commit

```bash
git add .
git commit -m "Release Atlas OS vX.Y.Z"
git push
```

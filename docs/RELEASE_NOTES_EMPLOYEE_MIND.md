# Atlas Enterprise v2.3.1 — Employee Mind Framework

## Theme
Employees begin creating explainable thoughts, decisions, goals, and reflections.

## What's New
- Employee Mind reasoning layer
- Employee goals as first-class database objects
- Employee thought records
- Employee decision records
- Employee reflection records
- Workforce → Employee Mind dashboard page
- Runtime actions now include phase, reasoning, confidence, and next action

## Validation
```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

Open the dashboard and go to:

```text
Workforce → Employee Mind
```

Click **Run Mind Cycle** and confirm thoughts, decisions, goals, and reflections appear.

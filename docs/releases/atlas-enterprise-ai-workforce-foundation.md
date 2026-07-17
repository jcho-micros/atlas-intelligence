# Atlas Enterprise — AI Workforce Foundation

## Goal
Atlas now models AI agents as employees inside an AI-native company. The new workforce foundation introduces employees, departments, internal messages, personal memory, skills, tools, and KPIs.

## New Capabilities
- Headquarters tab with company health, employees working, messages, and morning brief.
- People Directory tab with employee profiles, skills, tools, memory, inbox, and org chart.
- Employee Framework under `app/employees/`.
- Default AI workforce seeded automatically on startup.
- Database models for departments, employees, skills, tools, messages, memories, and KPIs.

## Validation
```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

## Suggested Commit
```bash
git add .
git commit -m "Add Atlas Enterprise AI workforce foundation"
git push
```

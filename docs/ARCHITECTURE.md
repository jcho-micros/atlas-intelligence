# Architecture

Atlas is modular and connector-driven.

```text
Dashboard / CLI
      |
Services Layer
      |
Agents
      |
Connectors
      |
SQLite Database
```

## Core Modules

- `app/connectors`: Marketplace and trend data sources.
- `app/agents`: Business logic agents.
- `app/services`: Orchestration and workflows.
- `app/models`: Pydantic/domain models.
- `app/database`: SQLite setup and SQLAlchemy models.
- `app/dashboard`: Streamlit dashboard.
- `app/api`: Future FastAPI layer.

## Design Rules

- Connectors collect data only.
- Agents analyze data only.
- Services coordinate workflows.
- Dashboard reads from services/database.
- AI explains patterns; deterministic code calculates scores.

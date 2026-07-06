# Atlas OS v1.0.0-alpha.2 Release Notes

## Theme
Operating System Core.

## Added
- `app/orchestration/event_bus.py`
- `app/orchestration/workflow_engine.py`
- `app/orchestration/task_queue.py`
- `app/agents/core/base.py`
- `app/agents/core/registry.py`
- `app/services/project_workspace_service.py`
- Core tests for agent registry and workflow engine

## Upgrade
Replace project files, keep `.env`, then run:

```bash
python main.py
python atlas.py dashboard
pytest
```

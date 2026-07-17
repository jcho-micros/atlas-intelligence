# Atlas Enterprise — Employee Workflow Engine

## Purpose

This release turns the AI workforce foundation into an operating company. Employees now receive work, communicate internally, update status, and answer role-based questions.

## Highlights

- Added `EmployeeWorkflowService`.
- Agent tasks are routed to employees based on role ownership.
- COO Sarah creates assignment messages for department owners.
- Employees maintain assignment memory.
- Dashboard adds an **Employee Workflows** tab.
- Employee tasks support Start and Complete actions.
- Internal communications can be marked read.
- The Ask Employee panel provides deterministic, role-aware answers from tasks, messages, and memory.

## Validation

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

## Notes

This version remains deterministic and local-first. No live LLM calls are required for employee responses yet.

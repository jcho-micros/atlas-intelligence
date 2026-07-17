# Atlas Enterprise Employee Runtime

This sprint gives the AI workforce a visible work cycle.

## Added

- `EmployeeMind`: deterministic local reasoning shell for each employee.
- `EmployeeRuntimeService`: runs one work cycle across employees.
- New Workforce page: **Employee Runtime**.
- Runtime actions: read inbox, prioritize tasks, work tasks, report to Sarah, and write employee memory.
- Recent activity and internal messages shown from the runtime page.

## Validation

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

Open **Workforce → Employee Runtime** and click **Run Work Cycle**.

# Atlas Enterprise Employee Experience

This release improves the Atlas Enterprise experience so the app feels more like a company headquarters than a dashboard.

## Added

- Place-based sidebar navigation:
  - Company: Headquarters, Executive Office, Strategy Room, Portfolio Office
  - Workforce: People Directory, Employee Office, Operations Center, Communications Center
  - Intelligence: Research and market intelligence tools
- New Employee Office page with:
  - employee current thought
  - inbox
  - memory
  - tools
  - skills
  - ask-this-employee interaction
- Operations Center improvements:
  - employee work cycle cards instead of raw action tables
  - human-readable employee actions
  - live employee activity cards
  - message feed cards
- Headquarters improvements:
  - employee cards now show current thoughts and next work

## Validation

Run:

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

Then open:

- Workforce → Employee Office
- Workforce → Operations Center
- Company → Headquarters

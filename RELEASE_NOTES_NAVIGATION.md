# Atlas Enterprise Navigation Cleanup + Employee Runtime Prep

## What changed

- Replaced the wide top-tab navigation with a grouped sidebar navigation.
- Added three primary sections:
  - Company: Headquarters, CEO Workspace, Business Workspace, Company Builder
  - Workforce: People Directory, Employee Workflows, Agent Command Center
  - Intelligence: Overview, Opportunity Workspace, AI Product Designer, Listings Gallery, Shop Intelligence, Trends, Research Runs
- Added a Company Builder page entry under Company.
- Preserved the existing Employee Workflow Engine, People Directory, internal communications, and Ask Employee starter chat.

## Validation

Run:

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

## Suggested commit

```bash
git add .
git commit -m "Group Atlas dashboard navigation by company function"
git push
```

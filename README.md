# Atlas Intelligence v1.1.0 — Business Engine

Atlas is evolving from an Etsy research app into an AI Commerce Operating System.

## What is new

- Business Engine: approved product projects now create/attach to a Business.
- Business Workspace tab in the dashboard.
- Brand, Business, Product, BusinessMetric, and BusinessOpportunity models.
- COO Agent events when a business workspace is created.
- Business-level revenue forecast, margin, products, projects, and launch readiness.

## Run

```bash
python main.py
python atlas.py dashboard
pytest
```

Keep your private `.env`. Do not commit it.


## Atlas Enterprise AI Workforce

This release introduces the first AI employee framework: Headquarters, People Directory, employee identity, skills, tools, inbox, memory, and KPIs.

## Atlas Enterprise Employee Workflow Engine

This release makes the AI employees operational instead of static profiles.

### New capabilities

- Employee Workflow Service routes agent tasks to the correct AI employee.
- Sarah, the COO, assigns work through internal messages.
- Employees update status, workload, and current task from live assignments.
- Employee Workflows dashboard tab shows assignments, messages, and employee ask/answer flow.
- Tasks can be started and completed from the dashboard.
- Internal messages can be marked read.
- Employee memory records assignments and completed work.

### Validate

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```

Recommended commit:

```bash
git add .
git commit -m "Add employee workflow engine"
```


## Atlas Enterprise v2.3.1 — Employee Mind Framework

Adds employee goals, thoughts, decisions, reflections, and a deterministic Employee Mind runtime.


## Atlas Enterprise v2.4.0 — Vendor Intelligence

This release adds Vendor Intelligence as a first-class Atlas Enterprise area:

- Vendor Directory
- Vendor Workspace
- RFQ Center
- Vendor Timeline
- vendor trust scoring
- quote tracking
- supplier recommendation foundation

Run:

```bash
rm data/atlas.db
python main.py
python atlas.py dashboard
pytest
```


## AI Design Studio
Set `OPENAI_API_KEY` in `.env` to have Noah generate real product concept images. See `docs/RELEASE_NOTES_AI_DESIGN_STUDIO.md`.


## Current Release

Atlas Enterprise v2.7.5 — Real AI Designer Hardening.

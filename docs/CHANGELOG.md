# Changelog

## v0.8.0

- Added CEO Workspace as the new operating view for Atlas OS.
- Added product project lifecycle model.
- Added agent task and event tracking.
- Added launch readiness score and daily brief.
- Added service layer for creating projects from opportunities.

# Changelog

## v0.7.0 - Agent Command Center

Adds the first version of Atlas OS agent management.

### Added
- Agent Command Center dashboard tab.
- Manufacturing Agent for supplier/vendor planning.
- Logistics Agent for shipping and fulfillment planning.
- Finance Agent for unit economics and margin planning.
- Customer Success Agent for support workflow planning.
- Accounting Agent for SKU/project accounting setup.
- ProductLaunchPlan database model.
- LaunchPlanService to orchestrate business agents.

### Notes
- v0.7 uses deterministic local agents. LLM-backed agents can be plugged in later.
- This release helps manage the questions behind product execution: who makes it, how it ships, how profit is calculated, how support is handled, and how accounting should be tracked.

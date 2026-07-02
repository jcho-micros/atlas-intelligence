# Agent Contracts

Each Atlas agent must define:

- Name
- Department
- Responsibilities
- Input events
- Output events
- Tasks it can perform
- Data it reads
- Data it writes

## CEO Agent

Owns decisions and orchestration.

Inputs:
- opportunity.detected
- project.needs_review
- task.failed
- launch.ready

Outputs:
- project.approved
- project.rejected
- project.parked
- task.assigned

## Research Agent

Owns market discovery and opportunity detection.

Outputs:
- opportunity.detected
- competitor.changed
- trend.changed

## Manufacturing Agent

Owns vendor discovery, quote comparison, MOQ, cost, and production feasibility.

Outputs:
- manufacturing.supplier_found
- manufacturing.quote_received
- manufacturing.blocked

## Finance Agent

Owns unit economics, margin, fees, break-even, and profit forecast.

Outputs:
- finance.margin_approved
- finance.margin_rejected
- finance.needs_review

## Marketing Agent

Owns SEO, launch copy, social content, and campaign assets.

Outputs:
- marketing.assets_ready
- marketing.seo_ready

## Customer Success Agent

Owns FAQs, support macros, refund policy, personalization responses, and customer communication.

Outputs:
- customer_success.playbook_ready

# Atlas OS

## Mission

Atlas OS exists to help John discover, design, validate, launch, and manage product businesses using marketplace data and specialized AI agents.

## Core Principle

Atlas should not only show data. Atlas should prepare decisions.

The CEO user should review, approve, reject, or redirect work. Agents should perform the operational work.

## Primary Flow

```text
Market Research
    ↓
Opportunity Detected
    ↓
Candidate Product Project Created
    ↓
CEO Reviews
    ↓
Approve / Reject / Park
    ↓
Agents Execute Work
    ↓
Launch Ready
    ↓
Performance Tracking
```

## Business Departments

Atlas OS is organized like a company:

- CEO Agent
- Research Agent
- Product Designer Agent
- Manufacturing Agent
- Logistics Agent
- Finance Agent
- Marketing Agent
- Customer Success Agent
- Accounting Agent
- Launch Agent

## Product Project Lifecycle

```text
candidate
approved
product_design
manufacturing
finance_review
marketing
launch_ready
launched
monitoring
paused
rejected
```

## Event-Driven Architecture

Agents communicate through events, not direct calls.

Examples:

- opportunity.detected
- project.created
- project.approved
- task.created
- task.completed
- finance.margin_approved
- manufacturing.supplier_found
- launch.ready

## Agent Memory

Every agent should remember prior decisions, vendors, margin assumptions, customer responses, product outcomes, and performance history.

Memory turns Atlas from a dashboard into an improving operating system.

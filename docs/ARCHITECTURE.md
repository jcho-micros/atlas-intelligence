# Atlas OS Architecture

## System Overview

Atlas OS is organized around a business-first architecture.

```text
Marketplace Data
      ↓
Research Engine
      ↓
Opportunity Engine
      ↓
Business Opportunity / Candidate Project
      ↓
CEO Approval
      ↓
Business / Product Project
      ↓
Workflow Engine
      ↓
Agent Tasks + Agent Events
      ↓
Launch + Performance + Memory
```

## Main Layers

### Presentation

- Streamlit dashboard
- CEO Workspace
- Project Workspace
- Agent views

### Application Services

- Research Engine
- Candidate Project Service
- CEO Workspace Service
- Product Idea Service
- Snapshot Service

### Atlas Core

- Event Bus
- Workflow Engine
- Planner
- Agent Registry
- Scheduler
- Memory
- Knowledge Base

### Domain

- Business Opportunities
- Product Projects
- Agent Tasks
- Agent Events
- Listings
- Shops
- Opportunities

### Infrastructure

- SQLite database
- Alembic migrations
- Etsy connector
- Future connectors: Amazon, Shopify, Printify, Alibaba, QuickBooks, ShipStation

## Rule of Thumb

Business logic should live outside the dashboard. The dashboard should display and trigger workflows, not own workflows.

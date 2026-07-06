# ADR-0002: Business-First Model

## Status

Accepted

## Context

Atlas began by identifying individual product opportunities. As the platform evolved, it became clear that successful commerce strategy should manage product lines and businesses, not isolated SKUs.

## Decision

Atlas will move toward a hierarchy of:

Business Opportunity → Business → Products → Listings

Candidate projects remain useful as the CEO Inbox, but the long-term model is business-first.

## Consequences

Benefits:
- Supports product lines.
- Enables brand/catalog strategy.
- Agents can operate at business and product levels.

Tradeoffs:
- Adds complexity to the data model.
- Requires migration from product-only workflows.

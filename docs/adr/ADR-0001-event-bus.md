# ADR-0001: Use an Event Bus for Agent Communication

## Status

Accepted

## Context

Atlas is evolving from a dashboard into an agent-managed commerce operating system. Direct service-to-service calls will become hard to maintain as more agents are added.

## Decision

Agents should communicate through events. Events are stored permanently and form the business activity timeline.

## Consequences

Benefits:
- Agents are loosely coupled.
- Timeline and audit history become natural outputs.
- New agents can subscribe to existing events.

Tradeoffs:
- Requires disciplined event naming.
- Requires event processing conventions.

from __future__ import annotations

import json
from typing import Any

from app.database.models import AgentEvent, ProductProject


class EventBus:
    """Durable event recorder for Atlas OS.

    v1 alpha keeps the event bus deliberately simple: events are stored in the
    database and can be displayed in the CEO timeline. Later releases can add
    subscribers, async dispatch, retries, and external notifications.
    """

    def __init__(self, session):
        self.session = session

    def emit(
        self,
        project: ProductProject,
        agent_name: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            project_id=project.id,
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            payload_json=json.dumps(payload or {}),
        )
        self.session.add(event)
        self.session.commit()
        return event

    def recent_for_project(self, project_id: int, limit: int = 25) -> list[AgentEvent]:
        return (
            self.session.query(AgentEvent)
            .filter_by(project_id=project_id)
            .order_by(AgentEvent.created_at.desc())
            .limit(limit)
            .all()
        )

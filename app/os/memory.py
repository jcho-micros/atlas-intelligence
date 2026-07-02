from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryRecord:
    agent: str
    topic: str
    content: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

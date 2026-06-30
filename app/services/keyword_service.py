from sqlalchemy.orm import Session
from app.database.models import Keyword


class KeywordService:
    def __init__(self, session: Session):
        self.session = session

    def seed_keywords(self, seed_keywords: list[dict]) -> int:
        added = 0
        for item in seed_keywords:
            keyword_text = item["keyword"].strip().lower()
            existing = self.session.query(Keyword).filter_by(keyword=keyword_text).one_or_none()
            if existing:
                continue
            self.session.add(
                Keyword(
                    keyword=keyword_text,
                    category=item.get("category", "General"),
                    priority=int(item.get("priority", 5)),
                    enabled=True,
                    status="pending",
                )
            )
            added += 1
        self.session.commit()
        return added

    def list_enabled_keywords(self) -> list[Keyword]:
        return (
            self.session.query(Keyword)
            .filter_by(enabled=True)
            .order_by(Keyword.priority.desc(), Keyword.keyword.asc())
            .all()
        )

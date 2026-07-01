from app.database.models import Keyword


def seed_database(session) -> None:
    starter_keywords = [
        "little league coach gift",
        "baseball lineup board",
        "custom baseball dugout sign",
        "baseball senior night poster",
        "baseball team banner",
    ]

    for phrase in starter_keywords:
        exists = session.query(Keyword).filter_by(keyword=phrase).first()

        if exists is None:
            session.add(
                Keyword(
                    keyword=phrase,
                    category="Baseball",
                    priority=10,
                    enabled=True,
                )
            )

    session.commit()
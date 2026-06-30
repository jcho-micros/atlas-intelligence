from app.database.models import Project, Keyword


def seed_database(session) -> None:
    baseball = session.query(Project).filter_by(name="Baseball").first()

    if not baseball:
        baseball = Project(
            name="Baseball",
            description="Baseball-related product opportunities",
            active=True,
        )
        session.add(baseball)
        session.flush()

    starter_keywords = [
        "baseball lineup board",
        "custom baseball dugout sign",
        "little league coach gift",
        "baseball senior night poster",
        "baseball team banner",
    ]

    for phrase in starter_keywords:
        exists = session.query(Keyword).filter_by(keyword=phrase).first()
        if not exists:
            session.add(
                Keyword(
                    project_id=baseball.id,
                    keyword=phrase,
                    category="Baseball",
                    priority=10,
                    enabled=True,
                )
            )

    session.commit()
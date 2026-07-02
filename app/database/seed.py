from app.database.models import Keyword, Project


def seed_database(session) -> None:
    baseball = session.query(Project).filter_by(name="Baseball").first()
    if baseball is None:
        baseball = Project(name="Baseball", description="Baseball product research", active=True)
        session.add(baseball)
        session.flush()

    starter_keywords = [
        "little league coach gift",
        "baseball lineup board",
        "custom baseball dugout sign",
        "baseball senior night poster",
        "baseball team banner",
    ]

    for phrase in starter_keywords:
        exists = session.query(Keyword).filter_by(project_id=baseball.id, keyword=phrase).first()
        if exists is None:
            session.add(Keyword(project_id=baseball.id, keyword=phrase, category="Baseball", priority=10, enabled=True))

    session.commit()

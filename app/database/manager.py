from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base


class DatabaseManager:
    def __init__(self, db_path: str = "data/atlas.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()

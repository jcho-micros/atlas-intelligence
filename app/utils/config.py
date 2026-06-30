from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def load_config(path: str = "config/config.yaml") -> dict:
    config_path = ROOT_DIR / path
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_db_path(config: dict) -> Path:
    env_path = os.getenv("ATLAS_DB_PATH")
    db_path = env_path or config.get("database", {}).get("path", "data/atlas.db")
    return ROOT_DIR / db_path

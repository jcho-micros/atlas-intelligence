from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    load_dotenv()
    return {
        "project": {"name": "Atlas Intelligence", "version": "0.3.0"},
        "database": {"path": os.getenv("ATLAS_DB_PATH", "data/atlas.db")},
        "research": {
            "mode": os.getenv("ATLAS_DATA_MODE", "sample").lower(),
            "limit": int(os.getenv("ATLAS_RESEARCH_LIMIT", "25")),
        },
        "etsy": {
            "api_key": os.getenv("ETSY_API_KEY", ""),
            "shared_secret": os.getenv("ETSY_SHARED_SECRET", ""),
        },
    }


def get_db_path(config: dict[str, Any]) -> str:
    path = Path(config["database"]["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)

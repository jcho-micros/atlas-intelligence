import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ENV = os.getenv("ATLAS_ENV", "development")
    MODE = os.getenv("ATLAS_DATA_MODE", "sample").lower()
    DB_PATH = os.getenv("ATLAS_DB", "data/atlas.db")
    ETSY_API_KEY = os.getenv("ETSY_API_KEY", "")
    ETSY_SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET", "")
    SEARCH_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", "25"))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))
    CANDIDATE_THRESHOLD = float(os.getenv("CANDIDATE_THRESHOLD", "55"))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    IMAGE_MODEL = os.getenv("ATLAS_IMAGE_MODEL", "gpt-image-1")
    IMAGE_QUALITY = os.getenv("ATLAS_IMAGE_QUALITY", "medium")
    IMAGE_SIZE = os.getenv("ATLAS_IMAGE_SIZE", "1536x1024")

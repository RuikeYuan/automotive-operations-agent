import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./automotive.db")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


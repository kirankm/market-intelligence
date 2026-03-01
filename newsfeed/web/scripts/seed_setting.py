"""Manage app settings from command line."""
import sys
import newsfeed.env  # noqa: F401 — load .env once
from newsfeed.storage.database import get_session
from newsfeed.storage.models import AppSetting


def upsert_setting(db, key, value):
    """Insert or update a setting."""
    existing = db.query(AppSetting).filter(AppSetting.key == key).first()
    if existing:
        existing.value = value
        print(f"Updated '{key}' = '{value}'")
    else:
        db.add(AppSetting(key=key, value=value))
        print(f"Created '{key}' = '{value}'")
    db.commit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m newsfeed.web.scripts.seed_setting <key> <value>")
        sys.exit(1)
    db = get_session()
    try:
        upsert_setting(db, sys.argv[1], sys.argv[2])
    finally:
        db.close()

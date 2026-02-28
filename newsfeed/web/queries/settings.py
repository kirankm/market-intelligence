"""App settings queries."""

from newsfeed.storage.models import AppSetting


def get_setting(db, key, default='5'):
    """Fetch a setting value from app_settings."""
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default


def get_all_settings(db):
    """Fetch all app settings."""
    return db.query(AppSetting).order_by(AppSetting.key).all()


def upsert_setting(db, key, value):
    """Insert or update a setting."""
    existing = db.query(AppSetting).filter(AppSetting.key == key).first()
    if existing:
        existing.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()


def delete_setting(db, key):
    """Delete a setting by key."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        db.delete(setting)
        db.commit()
        return True
    return False

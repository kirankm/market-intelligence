"""Database engine and session setup."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

_engine = None
_SessionFactory = None

def get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL not set in environment")
        _engine = create_engine(url)
    return _engine

def get_session():
    global _SessionFactory
    if _SessionFactory is None:
       _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()

def init_db():
    """Create all tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)

"""Data access: a direct database connection, or Supabase's REST API.

get_db() hands routes either a SQLAlchemy session (DATABASE_URL) or the
Supabase REST client (SUPABASE_URL + SUPABASE_KEY); app/storage.py makes
both look the same to the stores.
"""
import threading
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    """Use the psycopg 3 driver for Postgres URLs.

    Supabase hands out postgresql:// (or postgres://) URLs; SQLAlchemy would
    pick psycopg2 for those, which isn't installed.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def create_db_engine(url: str):
    url = normalize_database_url(url)
    connect_args = {}
    if make_url(url).get_backend_name() == "sqlite":
        # FastAPI may use a session from a different thread than it was created in
        connect_args["check_same_thread"] = False
    else:
        # Supabase's transaction pooler (port 6543) doesn't support prepared statements
        connect_args["prepare_threshold"] = None
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = create_db_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


_rest_client = None
_rest_lock = threading.Lock()


def get_rest_client():
    """The process-wide Supabase REST client (it reuses connections)"""
    from app.storage import SupabaseRest

    global _rest_client
    with _rest_lock:
        if _rest_client is None:
            _rest_client = SupabaseRest(settings.supabase_url, settings.supabase_key)
        return _rest_client


@contextmanager
def open_db() -> Iterator:
    """The configured backend, for scripts: a session or the REST client"""
    if settings.use_supabase_rest:
        yield get_rest_client()
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Iterator:
    """FastAPI dependency: the data backend for one request"""
    with open_db() as db:
        yield db

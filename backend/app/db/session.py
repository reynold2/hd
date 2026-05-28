import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


DEFAULT_DATABASE_URL = "sqlite:///./queue_calling.db"


def resolve_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_sqlite_engine(database_url: str = None) -> Engine:
    database_url = database_url or resolve_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine_args = {"connect_args": connect_args}
    if database_url == "sqlite:///:memory:":
        engine_args["poolclass"] = StaticPool
    return create_engine(database_url, **engine_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

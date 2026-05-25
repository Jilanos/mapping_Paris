from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.models import Base
from app.db.schema import ensure_schema_version


def create_engine_for_url(database_url: str) -> Engine:
    connect_args = {}
    engine_kwargs = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    if database_url == "sqlite:///:memory:":
        engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **engine_kwargs)


engine = create_engine_for_url(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_version(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

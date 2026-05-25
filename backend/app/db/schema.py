from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import AppMetadata

BACKEND_SCHEMA_VERSION = "1"
SCHEMA_VERSION_KEY = "backend_schema_version"


class UnsupportedBackendSchemaError(RuntimeError):
    pass


def ensure_schema_version(engine: Engine) -> None:
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with session_factory() as db:
        version = db.get(AppMetadata, SCHEMA_VERSION_KEY)
        if version is None:
            db.add(AppMetadata(key=SCHEMA_VERSION_KEY, value=BACKEND_SCHEMA_VERSION))
            db.commit()
            return
        if version.value != BACKEND_SCHEMA_VERSION:
            raise UnsupportedBackendSchemaError(
                "Unsupported local backend database schema version "
                f"{version.value}. Expected {BACKEND_SCHEMA_VERSION}. "
                "Run backend/scripts/reset-local-db.ps1, then init-local-db.ps1."
            )


def set_schema_version_for_test(db: Session, value: str) -> None:
    metadata = db.get(AppMetadata, SCHEMA_VERSION_KEY)
    if metadata is None:
        metadata = AppMetadata(key=SCHEMA_VERSION_KEY, value=value)
    metadata.value = value
    db.add(metadata)
    db.commit()

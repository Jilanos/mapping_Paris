import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import AppMetadata, Base  # noqa: E402
from app.db.schema import (  # noqa: E402
    BACKEND_SCHEMA_VERSION,
    SCHEMA_VERSION_KEY,
    UnsupportedBackendSchemaError,
    ensure_schema_version,
)


def test_schema_version_initializes_on_fresh_db(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'schema.db'}")
    Base.metadata.create_all(bind=engine)

    ensure_schema_version(engine)

    Session = sessionmaker(bind=engine)
    with Session() as db:
        metadata = db.get(AppMetadata, SCHEMA_VERSION_KEY)
        assert metadata is not None
        assert metadata.value == BACKEND_SCHEMA_VERSION


def test_unsupported_schema_version_gives_reset_guidance(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'schema.db'}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(AppMetadata(key=SCHEMA_VERSION_KEY, value="0"))
        db.commit()

    with pytest.raises(UnsupportedBackendSchemaError) as exc:
        ensure_schema_version(engine)

    assert "reset-local-db.ps1" in str(exc.value)

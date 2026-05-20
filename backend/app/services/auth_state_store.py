from datetime import UTC, datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from app.db.models import AuthState


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class AuthStateStore:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, ttl_seconds: int) -> AuthState:
        now = datetime.now(UTC)
        auth_state = AuthState(
            state=secrets.token_urlsafe(32),
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self._db.add(auth_state)
        self._db.commit()
        self._db.refresh(auth_state)
        return auth_state

    def consume_valid(self, state: str) -> AuthState | None:
        auth_state = self._db.query(AuthState).filter(AuthState.state == state).one_or_none()
        now = datetime.now(UTC)
        if auth_state is None:
            return None
        if auth_state.consumed_at is not None:
            return None
        if _normalize_dt(auth_state.expires_at) <= now:
            return None
        auth_state.consumed_at = now
        self._db.add(auth_state)
        self._db.commit()
        self._db.refresh(auth_state)
        return auth_state

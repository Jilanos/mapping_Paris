from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.crypto import TokenCrypto
from app.db.models import StravaToken
from app.schemas.strava import StravaTokenResponse


class TokenStore:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._crypto = TokenCrypto.from_settings(settings)

    def save(self, token_response: StravaTokenResponse) -> StravaToken:
        existing = self.get_latest()
        token = existing or StravaToken(
            access_token_encrypted="",
            refresh_token_encrypted="",
            expires_at=token_response.expires_at_datetime,
            scope="",
            token_type="Bearer",
        )
        token.athlete_id = token_response.athlete_id
        token.access_token_encrypted = self._crypto.encrypt(token_response.access_token)
        token.refresh_token_encrypted = self._crypto.encrypt(token_response.refresh_token)
        token.expires_at = token_response.expires_at_datetime
        token.scope = token_response.scope
        token.token_type = token_response.token_type
        self._db.add(token)
        self._db.commit()
        self._db.refresh(token)
        return token

    def get_latest(self) -> StravaToken | None:
        return (
            self._db.query(StravaToken)
            .order_by(StravaToken.updated_at.desc(), StravaToken.id.desc())
            .first()
        )

    def get_refresh_token(self) -> str | None:
        token = self.get_latest()
        if token is None:
            return None
        return self._crypto.decrypt(token.refresh_token_encrypted)

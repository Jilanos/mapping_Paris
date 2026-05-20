from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings


class EncryptionConfigError(RuntimeError):
    pass


class TokenCrypto:
    def __init__(self, key: str) -> None:
        if not key.strip():
            raise EncryptionConfigError("TOKEN_ENCRYPTION_KEY is required")
        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except ValueError as exc:
            raise EncryptionConfigError("TOKEN_ENCRYPTION_KEY is not a valid Fernet key") from exc

    @classmethod
    def from_settings(cls, settings: Settings) -> "TokenCrypto":
        return cls(settings.token_encryption_key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_value: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise EncryptionConfigError("Encrypted token cannot be decrypted") from exc

import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.core.crypto import EncryptionConfigError, TokenCrypto  # noqa: E402


def test_token_crypto_roundtrip_with_test_key() -> None:
    crypto = TokenCrypto(Fernet.generate_key().decode("utf-8"))

    encrypted = crypto.encrypt("raw-token")

    assert encrypted != "raw-token"
    assert crypto.decrypt(encrypted) == "raw-token"


def test_token_crypto_requires_key() -> None:
    settings = Settings(_env_file=None, token_encryption_key="")

    with pytest.raises(EncryptionConfigError):
        TokenCrypto.from_settings(settings)

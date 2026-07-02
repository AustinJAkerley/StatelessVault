import base64

import pytest

from app.crypto_service import CryptoService
from app.errors import ApiError


def test_encrypt_decrypt_round_trip() -> None:
    encrypted = CryptoService.encrypt("Attack at dawn.", "correct horse battery staple")

    plaintext = CryptoService.decrypt(
        secret="correct horse battery staple",
        salt=base64.b64decode(encrypted["salt"]),
        nonce=base64.b64decode(encrypted["nonce"]),
        ciphertext=base64.b64decode(encrypted["ciphertext"]),
        tag=base64.b64decode(encrypted["tag"]),
    )

    assert plaintext == "Attack at dawn."


def test_decrypt_invalid_secret_fails() -> None:
    encrypted = CryptoService.encrypt("Attack at dawn.", "correct horse battery staple")

    with pytest.raises(ApiError) as exc:
        CryptoService.decrypt(
            secret="wrong secret",
            salt=base64.b64decode(encrypted["salt"]),
            nonce=base64.b64decode(encrypted["nonce"]),
            ciphertext=base64.b64decode(encrypted["ciphertext"]),
            tag=base64.b64decode(encrypted["tag"]),
        )

    assert exc.value.error == "decryption_failed"

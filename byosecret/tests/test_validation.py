import pytest

from app.errors import ApiError
from app.models import ALGORITHM, MAX_PLAINTEXT_BYTES, parse_decrypt_request, parse_encrypt_request


def test_encrypt_rejects_empty_plaintext() -> None:
    with pytest.raises(ApiError):
        parse_encrypt_request({"plaintext": "", "secret": "secret"})


def test_encrypt_rejects_oversized_plaintext() -> None:
    oversized = "a" * (MAX_PLAINTEXT_BYTES + 1)
    with pytest.raises(ApiError):
        parse_encrypt_request({"plaintext": oversized, "secret": "secret"})


def test_decrypt_rejects_unsupported_algorithm() -> None:
    with pytest.raises(ApiError):
        parse_decrypt_request(
            {
                "version": 1,
                "algorithm": "unknown",
                "salt": "AAAAAAAAAAAAAAAAAAAAAA==",
                "nonce": "AAAAAAAAAAAAAAAA",
                "ciphertext": "AA==",
                "tag": "AAAAAAAAAAAAAAAAAAAAAA==",
                "secret": "s",
            }
        )


def test_decrypt_rejects_malformed_base64() -> None:
    with pytest.raises(ApiError):
        parse_decrypt_request(
            {
                "version": 1,
                "algorithm": ALGORITHM,
                "salt": "%%%",
                "nonce": "AAAAAAAAAAAAAAAA",
                "ciphertext": "AA==",
                "tag": "AAAAAAAAAAAAAAAAAAAAAA==",
                "secret": "s",
            }
        )

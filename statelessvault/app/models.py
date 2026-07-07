"""What a request has to look like before we trust it.

Nothing gets past this gate on its good looks. Every field is checked, sized,
and decoded here, so that the crypto downstream only ever handles honest bytes.
Be strict at the border and you can be relaxed everywhere behind it.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass

from .errors import ApiError

VERSION = 1
ALGORITHM = "Argon2id/AES-256-GCM"
MAX_PLAINTEXT_BYTES = 64 * 1024


@dataclass
class EncryptRequest:
    plaintext: str
    secret: str


@dataclass
class DecryptRequest:
    secret: str
    salt: bytes
    nonce: bytes
    ciphertext: bytes
    tag: bytes


def _require_non_empty_str(payload: dict, field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        raise ApiError("validation_error", f"'{field}' has to be a string.")
    if not value:
        raise ApiError("validation_error", f"'{field}' cannot be empty. Give it something real.")
    return value


def _decode_b64(payload: dict, field: str) -> bytes:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ApiError("validation_error", f"'{field}' has to be a Base64 string, and not an empty one.")
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ApiError("validation_error", f"'{field}' is not valid Base64.") from exc


def _validate_protocol(payload: dict, required: bool) -> None:
    version = payload.get("version")
    algorithm = payload.get("algorithm")

    if required and version is None:
        raise ApiError("validation_error", "'version' is required. Tell me which one you are speaking.")
    if required and algorithm is None:
        raise ApiError("validation_error", "'algorithm' is required. Tell me which one you are speaking.")

    if version is not None and version != VERSION:
        raise ApiError("validation_error", "That version is not one this vault knows.")

    if algorithm is not None and algorithm != ALGORITHM:
        raise ApiError("validation_error", "That algorithm is not one this vault knows.")


def parse_encrypt_request(payload: dict) -> EncryptRequest:
    _validate_protocol(payload, required=False)
    plaintext = _require_non_empty_str(payload, "plaintext")
    secret = _require_non_empty_str(payload, "secret")

    if len(plaintext.encode("utf-8")) > MAX_PLAINTEXT_BYTES:
        raise ApiError("validation_error", "'plaintext' is bigger than the 64 KB this vault will carry.")

    return EncryptRequest(plaintext=plaintext, secret=secret)


def parse_decrypt_request(payload: dict) -> DecryptRequest:
    _validate_protocol(payload, required=True)

    secret = _require_non_empty_str(payload, "secret")
    salt = _decode_b64(payload, "salt")
    nonce = _decode_b64(payload, "nonce")
    ciphertext = _decode_b64(payload, "ciphertext")
    tag = _decode_b64(payload, "tag")

    if len(salt) != 16:
        raise ApiError("validation_error", "'salt' has to decode to 16 bytes.")
    if len(nonce) != 12:
        raise ApiError("validation_error", "'nonce' has to decode to 12 bytes.")
    if len(tag) != 16:
        raise ApiError("validation_error", "'tag' has to decode to 16 bytes.")
    if not ciphertext:
        raise ApiError("validation_error", "'ciphertext' cannot be empty.")

    return DecryptRequest(secret=secret, salt=salt, nonce=nonce, ciphertext=ciphertext, tag=tag)

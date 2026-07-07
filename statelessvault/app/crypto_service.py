"""The part that actually does the work, and then forgets it.

Your secret becomes a key by way of Argon2id, the key locks or unlocks the
bytes with AES-256-GCM, and the moment the work is done the key is wiped from
memory. Nothing is written to disk. Nothing is kept. I did not invent any of
these primitives, and that is on purpose. The wilderness is no place for
homemade crypto.
"""

from __future__ import annotations

import base64
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import ApiError
from .models import ALGORITHM, VERSION

_ARGON2_TIME_COST = 3
_ARGON2_MEMORY_COST = 64 * 1024
_ARGON2_PARALLELISM = 4
_KEY_LEN = 32


class CryptoService:
    @staticmethod
    def _derive_key(secret: str, salt: bytes) -> bytearray:
        key = hash_secret_raw(
            secret=secret.encode("utf-8"),
            salt=salt,
            time_cost=_ARGON2_TIME_COST,
            memory_cost=_ARGON2_MEMORY_COST,
            parallelism=_ARGON2_PARALLELISM,
            hash_len=_KEY_LEN,
            type=Type.ID,
        )
        return bytearray(key)

    @staticmethod
    def encrypt(plaintext: str, secret: str) -> dict[str, str | int]:
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = CryptoService._derive_key(secret, salt)

        try:
            aesgcm = AESGCM(bytes(key))
            combined = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        finally:
            for i in range(len(key)):
                key[i] = 0

        ciphertext, tag = combined[:-16], combined[-16:]

        return {
            "version": VERSION,
            "algorithm": ALGORITHM,
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
        }

    @staticmethod
    def decrypt(*, secret: str, salt: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> str:
        key = CryptoService._derive_key(secret, salt)
        try:
            aesgcm = AESGCM(bytes(key))
            plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)
            return plaintext.decode("utf-8")
        except (InvalidTag, ValueError, UnicodeDecodeError) as exc:
            raise ApiError(
                "decryption_failed",
                "This will not open. Either the secret is wrong or someone has been at the package.",
                status_code=400,
            ) from exc
        finally:
            for i in range(len(key)):
                key[i] = 0

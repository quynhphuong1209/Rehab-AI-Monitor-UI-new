"""Password hashing and migration helpers.

New hashes use Argon2id when available. Legacy PBKDF2-SHA256 and SHA-256 hashes
are verified so successful logins can migrate accounts to the current format.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import platform
import secrets
from dataclasses import dataclass
from typing import Any, Mapping


HASH_VERSION_ARGON2 = "argon2"
HASH_VERSION_PBKDF2 = "pbkdf2_sha256"
HASH_VERSION_SHA256 = "sha256"


try:
    _original_platform_machine = platform.machine
    try:
        platform.machine = lambda: "AMD64"
        from argon2 import PasswordHasher
        from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
    finally:
        platform.machine = _original_platform_machine
except Exception:  # pragma: no cover - exercised only when dependency is absent
    PasswordHasher = None  # type: ignore[assignment]
    InvalidHashError = VerificationError = VerifyMismatchError = Exception  # type: ignore[misc,assignment]


def _build_password_hasher():
    if PasswordHasher is None:
        return None
    original_machine = platform.machine
    try:
        platform.machine = lambda: "AMD64"
        return PasswordHasher(
            time_cost=2,
            memory_cost=65536,
            parallelism=2,
            hash_len=32,
            salt_len=16,
        )
    finally:
        platform.machine = original_machine


_HASHER = _build_password_hasher()


@dataclass(frozen=True)
class PasswordVerification:
    ok: bool
    needs_rehash: bool = False
    legacy_version: str | None = None


def hash_password_pbkdf2(password: str, *, rounds: int | None = None, salt: str | None = None) -> str:
    if password is None:
        raise ValueError("password is required")
    rounds = rounds or int(os.environ.get("REHAB_PBKDF2_ROUNDS", "260000"))
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("utf-8"), rounds)
    return f"{HASH_VERSION_PBKDF2}${rounds}${salt}${digest.hex()}"


def hash_password_v2(password: str) -> str:
    if password is None:
        raise ValueError("password is required")
    if _HASHER is None:
        return hash_password_pbkdf2(password)
    return _HASHER.hash(str(password))


def current_hash_version() -> str:
    return HASH_VERSION_ARGON2 if _HASHER is not None else HASH_VERSION_PBKDF2


def password_record_update(
    password: str,
    *,
    updated_at: str | None = None,
    must_change_password: bool | None = None,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "password": hash_password_v2(password),
        "hash_version": current_hash_version(),
    }
    if updated_at is not None:
        fields["updated_at"] = updated_at
    if must_change_password is not None:
        fields["must_change_password"] = bool(must_change_password)
    return fields


def hash_password_legacy_sha256(password: str) -> str:
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


def is_legacy_sha256_hash(value: str | None) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in value)


def _verify_pbkdf2(password: str, stored_hash: str) -> bool:
    try:
        _, rounds, salt, digest_hex = stored_hash.split("$", 3)
        calc = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            salt.encode("utf-8"),
            int(rounds),
        ).hex()
        return hmac.compare_digest(calc, digest_hex)
    except Exception:
        return False


def verify_password_hash(password: str, stored_hash: str | None, hash_version: str | None = None) -> PasswordVerification:
    stored_hash = str(stored_hash or "")
    version = str(hash_version or "").lower()
    if not stored_hash:
        return PasswordVerification(False)

    if version == HASH_VERSION_ARGON2 or stored_hash.startswith("$argon2"):
        if _HASHER is None:
            return PasswordVerification(False)
        try:
            ok = _HASHER.verify(stored_hash, str(password))
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return PasswordVerification(False)
        return PasswordVerification(ok, needs_rehash=ok and _HASHER.check_needs_rehash(stored_hash))

    if version in {"", HASH_VERSION_PBKDF2} and stored_hash.startswith(f"{HASH_VERSION_PBKDF2}$"):
        ok = _verify_pbkdf2(password, stored_hash)
        return PasswordVerification(ok, needs_rehash=ok and current_hash_version() != HASH_VERSION_PBKDF2, legacy_version=HASH_VERSION_PBKDF2)

    if version in {"", HASH_VERSION_SHA256} and is_legacy_sha256_hash(stored_hash):
        ok = hmac.compare_digest(hash_password_legacy_sha256(password), stored_hash)
        return PasswordVerification(ok, needs_rehash=ok, legacy_version=HASH_VERSION_SHA256)

    looks_hashed = (
        stored_hash.startswith("$argon2")
        or stored_hash.startswith(f"{HASH_VERSION_PBKDF2}$")
        or is_legacy_sha256_hash(stored_hash)
    )
    if not looks_hashed and hmac.compare_digest(str(password), stored_hash):
        return PasswordVerification(True, needs_rehash=True, legacy_version="plaintext")

    return PasswordVerification(False)


def verify_password_record(password: str, user_record: Mapping[str, Any] | None) -> PasswordVerification:
    if not user_record:
        return PasswordVerification(False)
    return verify_password_hash(
        password,
        str(user_record.get("password") or ""),
        str(user_record.get("hash_version") or ""),
    )


def needs_password_rehash(user_record: Mapping[str, Any] | None) -> bool:
    if not user_record:
        return False
    stored_hash = str(user_record.get("password") or "")
    version = str(user_record.get("hash_version") or "").lower()
    if not stored_hash:
        return False

    if current_hash_version() == HASH_VERSION_PBKDF2:
        return not stored_hash.startswith(f"{HASH_VERSION_PBKDF2}$")

    if version != HASH_VERSION_ARGON2 or not stored_hash.startswith("$argon2"):
        return True
    if _HASHER is None:
        return False
    try:
        return _HASHER.check_needs_rehash(stored_hash)
    except (VerificationError, InvalidHashError):
        return True

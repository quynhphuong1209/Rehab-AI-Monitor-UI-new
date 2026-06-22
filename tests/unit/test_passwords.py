from auth.passwords import (
    HASH_VERSION_ARGON2,
    HASH_VERSION_PBKDF2,
    HASH_VERSION_SHA256,
    current_hash_version,
    hash_password_legacy_sha256,
    hash_password_pbkdf2,
    hash_password_v2,
    needs_password_rehash,
    password_record_update,
    verify_password_hash,
    verify_password_record,
)


def test_current_hash_verifies_and_wrong_password_fails():
    hashed = hash_password_v2("correct horse")
    record = {"password": hashed, "hash_version": current_hash_version()}

    assert verify_password_record("correct horse", record).ok
    assert not verify_password_record("wrong", record).ok


def test_legacy_sha256_verifies_and_requests_rehash():
    record = {
        "password": hash_password_legacy_sha256("old-password"),
        "hash_version": HASH_VERSION_SHA256,
    }

    result = verify_password_record("old-password", record)

    assert result.ok
    assert result.needs_rehash
    assert needs_password_rehash(record)


def test_legacy_pbkdf2_verifies():
    hashed = hash_password_pbkdf2("old-password", rounds=1000, salt="abc123")
    result = verify_password_hash("old-password", hashed, HASH_VERSION_PBKDF2)

    assert result.ok
    assert result.legacy_version in {HASH_VERSION_PBKDF2, None}


def test_password_record_update_sets_current_metadata():
    fields = password_record_update("new-password", updated_at="2026-06-19T10:00:00", must_change_password=False)

    assert fields["hash_version"] in {HASH_VERSION_ARGON2, HASH_VERSION_PBKDF2}
    assert fields["updated_at"] == "2026-06-19T10:00:00"
    assert fields["must_change_password"] is False
    assert verify_password_record("new-password", fields).ok


def test_plaintext_legacy_password_verifies_and_requests_rehash():
    record = {"password": "temporary-secret"}

    result = verify_password_record("temporary-secret", record)

    assert result.ok
    assert result.needs_rehash
    assert result.legacy_version == "plaintext"
    assert not verify_password_record("wrong", record).ok

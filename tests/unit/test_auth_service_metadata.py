from datetime import datetime, timezone

from backend.auth_service import register_user, reset_password
from auth.passwords import current_hash_version, verify_password_hash


def _now():
    return datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)


def _normalize(value):
    return " ".join(str(value or "").strip().split())


def _lookup(users, username):
    wanted = _normalize(username).casefold()
    for key in users:
        if _normalize(key).casefold() == wanted:
            return key
    return None


def test_register_user_sets_current_hash_metadata():
    users = {}

    ok, _message = register_user(
        "patient01",
        "p01@example.test",
        "secret123",
        "secret123",
        "Benh nhan",
        "Patient 01",
        load_users=lambda: users,
        save_users=lambda updated: users.update(updated),
        lookup_user=_lookup,
        normalize_text=_normalize,
        hash_password=lambda password: f"fake-hash:{password}",
        now_fn=_now,
    )

    assert ok
    assert users["patient01"]["hash_version"] == current_hash_version()
    assert users["patient01"]["must_change_password"] is False


def test_reset_password_preserves_account_and_updates_hash_metadata():
    users = {
        "patient01": {
            "password": "old",
            "email": "p01@example.test",
            "full_name": "Patient 01",
            "role": "Benh nhan",
        }
    }

    ok, _message = reset_password(
        "patient01",
        "p01@example.test",
        "secret123",
        "secret123",
        load_users=lambda: users,
        save_users=lambda updated: users.update(updated),
        lookup_user=_lookup,
        normalize_text=_normalize,
        hash_password=lambda password: f"fake-hash:{password}",
        now_fn=_now,
    )

    assert ok
    assert set(users) == {"patient01"}
    assert users["patient01"]["password"] == "fake-hash:secret123"
    assert users["patient01"]["hash_version"] == current_hash_version()
    assert users["patient01"]["must_change_password"] is False

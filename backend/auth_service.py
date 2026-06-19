"""Authentication service functions.

The Streamlit controller owns UI/session state; this module owns the business
rules for login, registration and password reset.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from auth.passwords import current_hash_version


JsonDict = dict[str, Any]
LoadUsers = Callable[[], dict[str, JsonDict]]
SaveUsers = Callable[[dict[str, JsonDict]], None]
NormalizeText = Callable[[Any], str]
LookupUser = Callable[[dict[str, JsonDict], str], str | None]
VerifyPassword = Callable[[str, str, JsonDict], bool]
UpgradePassword = Callable[[dict[str, JsonDict], str, str], None]
HashPassword = Callable[[str], str]
NowFn = Callable[[], Any]


def authenticate_user(
    username: str,
    password: str,
    *,
    load_users: LoadUsers,
    lookup_user: LookupUser,
    verify_password: VerifyPassword,
    upgrade_password: UpgradePassword,
) -> tuple[bool, str | None, JsonDict | None, str]:
    """Validate username/password and upgrade the stored hash when needed."""

    users = load_users()
    user_key = lookup_user(users, username)
    if user_key and verify_password(user_key, password, users[user_key]):
        upgrade_password(users, user_key, password)
        return True, user_key, users[user_key], ""
    return False, None, None, "Tài khoản hoặc mật khẩu không đúng."


def reset_password(
    username: str,
    email: str,
    password: str,
    password2: str,
    *,
    load_users: LoadUsers,
    save_users: SaveUsers,
    lookup_user: LookupUser,
    normalize_text: NormalizeText,
    hash_password: HashPassword,
    now_fn: NowFn,
) -> tuple[bool, str]:
    """Reset password after matching username and email."""

    username = normalize_text(username)
    email = normalize_text(email)
    if not username or not email or len(password or "") < 6:
        return False, "Vui lòng nhập tài khoản, email và mật khẩu mới tối thiểu 6 ký tự."
    if password != password2:
        return False, "Mật khẩu xác nhận không khớp."

    users = load_users()
    user_key = lookup_user(users, username)
    stored_email = normalize_text((users.get(user_key) or {}).get("email")) if user_key else ""
    if not user_key or stored_email.casefold() != email.casefold():
        return False, "Thông tin tài khoản hoặc email không chính xác."

    users[user_key]["password"] = hash_password(password)
    users[user_key]["hash_version"] = current_hash_version()
    users[user_key]["updated_at"] = now_fn().isoformat()
    users[user_key]["must_change_password"] = False
    save_users(users)
    return True, "Đặt lại mật khẩu thành công. Bạn có thể đăng nhập ngay."


def register_user(
    username: str,
    email: str,
    password: str,
    password2: str,
    role: str,
    full_name: str,
    *,
    load_users: LoadUsers,
    save_users: SaveUsers,
    lookup_user: LookupUser,
    normalize_text: NormalizeText,
    hash_password: HashPassword,
    now_fn: NowFn,
) -> tuple[bool, str]:
    """Create a new user account after basic validation."""

    username = normalize_text(username)
    email = normalize_text(email)
    full_name = normalize_text(full_name) or username
    if not username or not email or len(password or "") < 6:
        return False, "Vui lòng điền đủ thông tin và mật khẩu tối thiểu 6 ký tự."
    if password != password2:
        return False, "Mật khẩu xác nhận không khớp."

    users = load_users()
    if lookup_user(users, username):
        return False, "Tên đăng nhập này đã tồn tại."

    users[username] = {
        "password": hash_password(password),
        "hash_version": current_hash_version(),
        "email": email,
        "full_name": full_name,
        "role": role or "Bệnh nhân",
        "created_at": now_fn().isoformat(),
        "must_change_password": False,
    }
    save_users(users)
    return True, "Đăng ký thành công. Bạn có thể đăng nhập ngay."

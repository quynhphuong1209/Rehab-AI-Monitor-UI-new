"""Authentication view models shared by controllers and Streamlit session code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthenticatedUser:
    """Normalized authenticated user stored in Streamlit session state."""

    username: str
    full_name: str
    email: str | None
    role: str

    @classmethod
    def from_record(cls, username: str, record: dict[str, Any] | None) -> "AuthenticatedUser":
        data = record or {}
        return cls(
            username=username,
            full_name=data.get("full_name") or username,
            email=data.get("email"),
            role=data.get("role") or "Bệnh nhân",
        )

    def to_session_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
        }

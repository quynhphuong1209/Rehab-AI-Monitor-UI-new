"""Admin role dashboard shell.

This module keeps the Admin UI separate from the large app.py flow while still
delegating existing tabs to the legacy renderer. It gives the role its own
HTML/CSS surface, matching the clinical-teal demo design.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import json
from pathlib import Path

import streamlit as st

try:
    from demo_ui import block, card_close, card_open, kv, page_head, stat
except Exception:  # pragma: no cover - fallback for unusual import contexts
    block = card_close = card_open = kv = page_head = stat = None


ROLE = "Quản trị viên"


def _count_roles(users: dict) -> dict[str, int]:
    counts = {
        "total": len(users),
        "patients": 0,
        "clinicians": 0,
        "researchers": 0,
        "admins": 0,
    }
    for record in users.values():
        role = (record or {}).get("role", "")
        if role == "Bệnh nhân":
            counts["patients"] += 1
        elif role == "Bác sĩ / KTV PHCN":
            counts["clinicians"] += 1
        elif role == "Nghiên cứu viên":
            counts["researchers"] += 1
        elif role == "Quản trị viên":
            counts["admins"] += 1
    return counts


def _load_admin_snapshot() -> tuple[dict, list, list]:
    """Read lightweight Admin data directly from the workspace JSON files."""

    def read_json(path: Path, default):
        try:
            if path.exists():
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
        except Exception:
            return default
        return default

    root = Path.cwd()
    users = read_json(root / "database" / "users.json", {})
    videos = read_json(root / "database" / "video_list.json", [])
    evaluations = read_json(root / "database" / "doctor_evaluations.json", [])
    return users or {}, videos or [], evaluations or []


def _admin_overview_html() -> str:
    if not all((block, card_close, card_open, kv, page_head, stat)):
        return ""

    users, videos, evaluations = _load_admin_snapshot()
    counts = _count_roles(users)
    processed = sum(1 for video in videos if (video or {}).get("status") == "Đã phân tích")
    pending = max(0, len(videos) - processed)

    stats_html = (
        '<div class="grid g-3" style="margin-bottom:16px">'
        + stat("i-users", "Tổng tài khoản", str(counts["total"]), "", "", "đang quản lý")
        + stat("i-video", "Video hệ thống", str(len(videos)), "", "", f"{pending} chờ xử lý")
        + stat("i-check", "Bản ghi đánh giá", str(len(evaluations)), "", "", "AI + lâm sàng")
        + "</div>"
    )

    role_card = (
        card_open("Phân bố vai trò", "i-shield")
        + kv("Bệnh nhân", counts["patients"])
        + kv("Bác sĩ / KTV", counts["clinicians"])
        + kv("Nghiên cứu viên", counts["researchers"])
        + kv("Quản trị viên", counts["admins"])
        + card_close()
    )
    system_card = (
        card_open("Trạng thái vận hành", "i-cog")
        + kv("Lưu trữ", "JSON / HF Dataset")
        + kv("Xử lý video", f"{processed} đã phân tích")
        + kv("Hàng chờ", pending, "var(--warn)" if pending else "var(--ok)")
        + kv("Theme", st.session_state.get("theme", "light"))
        + card_close()
    )

    body = (
        page_head(
            "Bảng điều khiển Quản trị",
            "Tách giao diện Admin thành package riêng trong frontend/roles/admin.",
        )
        + stats_html
        + f'<div class="grid g-2">{role_card}{system_card}</div>'
    )
    return block(body)


def render(
    tab_titles: Sequence[str],
    render_tab_content: Callable[[Sequence[str], str], None],
) -> None:
    """Render Admin content through the role package entrypoint."""
    active_tab = st.session_state.get("active_tab_widget") or st.session_state.get("active_tab")
    if active_tab == "🏠 TRANG CHỦ":
        overview_html = _admin_overview_html()
        if overview_html:
            st.markdown(overview_html, unsafe_allow_html=True)
            st.session_state["_admin_package_rendered_home"] = True
    else:
        st.session_state.pop("_admin_package_rendered_home", None)

    return render_tab_content(tab_titles, ROLE)

"""Researcher role frontend shell."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from frontend.roles.common import emit_role_workspace_close, emit_role_workspace_open, metric_grid, page_header

ROLE = "Nghiên cứu viên"


def render(
    tab_titles: Sequence[str],
    render_tab_content: Callable[[Sequence[str], str], None],
) -> None:
    """Render the Researcher workspace through the role package entrypoint."""
    emit_role_workspace_open("researcher")
    page_header(
        "Không gian nghiên cứu",
        "Quản lý dataset, đối chiếu AI và trích xuất dữ liệu khung xương theo luồng lâm sàng.",
        "NCV workspace",
    )
    metric_grid(
        (
            ("Điểm khung xương", "33", "CSV tọa độ / khung hình"),
            ("Vai trò dữ liệu", "NCV", "Phân tích & hiệu chỉnh AI"),
            ("Chuẩn hiển thị", "Rehab", "Demo blue workspace"),
        )
    )
    try:
        return render_tab_content(tab_titles, ROLE)
    finally:
        emit_role_workspace_close()

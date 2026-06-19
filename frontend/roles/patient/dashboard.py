"""Patient role frontend shell."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from frontend.roles.common import emit_role_workspace_close, emit_role_workspace_open, metric_grid, page_header

ROLE = "Bệnh nhân"


def render(
    tab_titles: Sequence[str],
    render_tab_content: Callable[[Sequence[str], str], None],
) -> None:
    """Render Patient tabs through the role package entrypoint."""
    emit_role_workspace_open("patient")
    page_header(
        "Theo dõi tập luyện",
        "Khai báo triệu chứng, gửi video tập và xem phản hồi từ chuyên gia trên cùng một giao diện.",
        "Patient workspace",
    )
    metric_grid(
        (
            ("Khai báo VAS", "0-10", "Theo dõi đau"),
            ("Bài tập", "PHCN", "Upload video tập luyện"),
            ("Phản hồi", "AI + BS", "Kết quả sau đánh giá"),
        )
    )
    try:
        return render_tab_content(tab_titles, ROLE)
    finally:
        emit_role_workspace_close()

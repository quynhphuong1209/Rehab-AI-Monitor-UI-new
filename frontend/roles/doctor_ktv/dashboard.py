"""Combined doctor and technician role frontend shell."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from frontend.roles.common import emit_role_workspace_close, emit_role_workspace_open, metric_grid, page_header

ROLE = "Bác sĩ / KTV PHCN"


def render(
    tab_titles: Sequence[str],
    render_tab_content: Callable[[Sequence[str], str], None],
) -> None:
    """Render Doctor/KTV tabs through the role package entrypoint."""
    emit_role_workspace_open("doctor-ktv")
    page_header(
        "Không gian lâm sàng",
        "Theo dõi bệnh nhân, đánh giá PHCN và đối chiếu kết quả AI trong một mặt bàn dữ liệu gọn.",
        "Doctor / KTV workspace",
    )
    metric_grid(
        (
            ("Luồng công việc", "PHCN", "Đánh giá lâm sàng"),
            ("Đối chiếu AI", "ROM", "Góc khớp & trạng thái"),
            ("Ưu tiên", "VAS", "Theo dõi đau / cảnh báo"),
        )
    )
    try:
        return render_tab_content(tab_titles, ROLE)
    finally:
        emit_role_workspace_close()

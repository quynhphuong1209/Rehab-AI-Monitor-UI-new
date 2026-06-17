"""Admin role frontend wrapper."""

ROLE = "Quản trị viên"

def render(tab_titles, render_tab_content):
    return render_tab_content(tab_titles, ROLE)


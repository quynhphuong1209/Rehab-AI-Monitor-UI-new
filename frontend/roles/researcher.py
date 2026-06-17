"""Researcher role frontend wrapper."""

ROLE = "Nghiên cứu viên"

def render(tab_titles, render_tab_content):
    return render_tab_content(tab_titles, ROLE)


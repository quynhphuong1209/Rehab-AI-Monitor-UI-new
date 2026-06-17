"""Patient role frontend wrapper."""

ROLE = "Bệnh nhân"

def render(tab_titles, render_tab_content):
    return render_tab_content(tab_titles, ROLE)


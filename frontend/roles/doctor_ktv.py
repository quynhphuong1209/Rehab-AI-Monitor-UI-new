"""Combined doctor and technician role frontend wrapper."""

ROLE = "Bác sĩ / KTV PHCN"

def render(tab_titles, render_tab_content):
    return render_tab_content(tab_titles, ROLE)


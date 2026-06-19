# MVC Structure

This app is being decomposed from a large Streamlit monolith into explicit MVC
boundaries.

## Current Boundaries

- Models: `models/`
  - `models/auth.py`: authenticated user session model.
  - `models/navigation.py`: role constants and tab contracts.
- Services: `backend/`
  - `backend/auth_service.py`: login, registration and password reset rules.
  - `backend/symptoms.py`: patient symptom business rules.
- Controllers: `controllers/`
  - `app_controller.py`: top-level app flow.
  - `auth_controller.py`: login/register flow.
  - `ui_event_controller.py`: JS bridge event handling.
  - `admin_controller.py`, `patient_controller.py`, `doctor_ktv_controller.py`,
    `researcher_controller.py`: role entrypoints.
  - `tab_controller.py`: tab-content dispatch boundary.
- Views: `views/` and `frontend/`
  - `views/auth_view.py`: auth bridge view.
  - `views/sidebar_view.py`: shared and role-specific sidebar view.
  - `views/legacy_tabs_view.py`: adapter for tab content not yet extracted from
    `app.py`.
  - `frontend/roles/*/dashboard.py`: role shell views.

## Remaining Legacy Surface

`app.py` still contains the large legacy tab renderer and many helper functions
used by those tabs. New code should prefer adding model/service/controller/view
modules and passing required legacy dependencies through `AppContext` only while
the old functions are being moved.

## Dependency Direction

`app.py` bootstraps dependencies, creates `AppContext`, then calls
`controllers.app_controller.run_app`. New controllers and views should not import
`app.py` directly.

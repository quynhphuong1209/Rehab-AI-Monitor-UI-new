"""Role permission matrix skeleton for Phase 5 extraction."""
from __future__ import annotations

ROLE_ADMIN = "Quản trị viên"
ROLE_DOCTOR = "Bác sĩ / KTV PHCN"
ROLE_RESEARCHER = "Nghiên cứu viên"
ROLE_PATIENT = "Bệnh nhân"


def can_view_patient(actor_role: str, actor_username: str, patient_username: str) -> bool:
    if actor_role == ROLE_ADMIN:
        return True
    if actor_role in {ROLE_DOCTOR, ROLE_RESEARCHER}:
        return True
    return actor_role == ROLE_PATIENT and actor_username == patient_username


def can_mutate_system(actor_role: str) -> bool:
    return actor_role == ROLE_ADMIN

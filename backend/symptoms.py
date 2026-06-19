"""Patient symptom service used by the hybrid React/Streamlit bridge."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


JsonRecord = dict[str, Any]
LoadData = Callable[[str], Any]
SaveData = Callable[[str, Any], None]
NowFn = Callable[[], Any]
NormalizeFn = Callable[[Any], str]


def safe_int(value: Any, default: int = 0, min_value: int | None = None, max_value: int | None = None) -> int:
    """Parse a UI value into an int with optional bounds."""

    try:
        parsed = int(float(str(value).replace(",", ".")))
    except Exception:
        parsed = default
    if min_value is not None:
        parsed = max(min_value, parsed)
    if max_value is not None:
        parsed = min(max_value, parsed)
    return parsed


def load_records(file_path: str, load_data: LoadData) -> list[JsonRecord]:
    """Load symptom records while tolerating legacy/corrupt non-list shapes."""

    data = load_data(file_path)
    return data if isinstance(data, list) else []


def list_patient_symptoms(
    file_path: str,
    load_data: LoadData,
    normalize: NormalizeFn,
    *,
    username: str | None = None,
    limit: int = 8,
) -> list[JsonRecord]:
    """Return latest symptoms for a patient, preserving legacy fields."""

    records = load_records(file_path, load_data)
    if username:
        target = normalize(username).casefold()
        records = [
            item for item in records
            if normalize((item or {}).get("username")).casefold() == target
        ]

    def sort_key(item: JsonRecord) -> str:
        raw = (item or {}).get("created_at") or (item or {}).get("date") or (item or {}).get("time") or ""
        return str(raw)

    return list(reversed(sorted(records, key=sort_key)))[: int(limit or 8)]


def validate_patient_symptom(payload: JsonRecord | None, user_info: JsonRecord | None, normalize: NormalizeFn, now_fn: NowFn) -> tuple[JsonRecord | None, str | None]:
    """Validate and normalize a symptom payload from React."""

    payload = payload if isinstance(payload, dict) else {}
    user_info = user_info or {}
    username = normalize(user_info.get("username") or payload.get("username"))
    full_name = normalize(user_info.get("full_name") or payload.get("full_name") or username)
    symptoms = normalize(payload.get("symptoms") or payload.get("description"))
    pain_location = normalize(payload.get("pain_location") or payload.get("painLocation"))
    exercise = normalize(payload.get("exercise"))
    date_value = normalize(payload.get("date"))
    vas = safe_int(payload.get("vas"), default=-1, min_value=-1, max_value=10)

    if not username:
        return None, "Phiên đăng nhập chưa hợp lệ. Vui lòng đăng nhập lại."
    if vas < 0:
        return None, "Vui lòng chọn mức đau VAS từ 0 đến 10."
    if not symptoms:
        return None, "Vui lòng nhập mô tả triệu chứng."
    if len(symptoms) < 6:
        return None, "Mô tả triệu chứng cần chi tiết hơn một chút."

    now = now_fn()
    record: JsonRecord = {
        "username": username,
        "full_name": full_name,
        "symptoms": symptoms,
        "pain_location": pain_location,
        "exercise": exercise,
        "vas": vas,
        "date": date_value or now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M - %d/%m/%Y"),
        "created_at": now.isoformat(),
        "source": "react_patient_form",
    }
    return record, None


def create_patient_symptom(
    file_path: str,
    load_data: LoadData,
    save_data: SaveData,
    normalize: NormalizeFn,
    now_fn: NowFn,
    payload: JsonRecord | None,
    user_info: JsonRecord | None,
) -> tuple[bool, str, JsonRecord | None]:
    """Append a validated symptom record using the app's JSON persistence."""

    record, error = validate_patient_symptom(payload, user_info, normalize, now_fn)
    if error:
        return False, error, None
    data = load_records(file_path, load_data)
    data.append(record)
    save_data(file_path, data)
    return True, "Đã lưu khai báo triệu chứng và gửi tới bác sĩ/KTV.", record

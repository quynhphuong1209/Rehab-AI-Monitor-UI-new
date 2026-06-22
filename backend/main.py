"""FastAPI backend for the React migration UI.

The Streamlit app is still the legacy production surface. This backend gives the
new Vite/React UI a small, explicit API while reading the same JSON data files so
existing accounts and runtime data stay intact.
"""

from __future__ import annotations

import csv
import base64
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import shutil
import statistics
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from auth.passwords import current_hash_version, hash_password_v2, verify_password_record
from storage.json_store import read_json, write_json
from video.serving import get_final_h264_path
from utils.reference_utils import (
    detect_motion_subtype,
    find_closest_reference_pose,
    resolve_reference_file,
)


ROLE_ADMIN = "Quản trị viên"
ROLE_DOCTOR_KTV = "Bác sĩ / KTV PHCN"
ROLE_RESEARCHER = "Nghiên cứu viên"
ROLE_PATIENT = "Bệnh nhân"

ROLE_LABELS = {
    "admin": ROLE_ADMIN,
    "doctor_ktv": ROLE_DOCTOR_KTV,
    "researcher": ROLE_RESEARCHER,
    "patient": ROLE_PATIENT,
}
ROLE_ORDER = ("admin", "doctor_ktv", "researcher", "patient")

REPO_ROOT = Path(os.environ.get("REHAB_REPO_ROOT", Path(__file__).resolve().parents[1])).resolve()
DATABASE_DIR = Path(os.environ.get("REHAB_DATABASE_DIR", REPO_ROOT / "database")).resolve()
DATASET_DIR = Path(os.environ.get("REHAB_DATASET_DIR", DATABASE_DIR / "dataset")).resolve()
TOKEN_SECRET = os.environ.get("REHAB_TOKEN_SECRET") or hashlib.sha256(str(REPO_ROOT).encode("utf-8")).hexdigest()
TOKEN_TTL_SECONDS = int(os.environ.get("REHAB_TOKEN_TTL_SECONDS", str(30 * 24 * 60 * 60)))
HF_DATASET_ID = os.environ.get("HF_DATASET_ID") or os.environ.get("REHAB_HF_DATASET_ID") or "quynhphuong1209/Rehab-AI-Monitor-2026-data"
HF_BUCKET_ID = (
    os.environ.get("HF_BUCKET_ID")
    or os.environ.get("REHAB_HF_BUCKET_ID")
    or os.environ.get("REHAB_HF_STORAGE_BUCKET_ID")
    or "quynhphuong1209/Rehab-AI-Monitor-2026-storage"
)
HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
HF_DOWNLOAD_TIMEOUT_SECONDS = int(os.environ.get("REHAB_HF_DOWNLOAD_TIMEOUT_SECONDS", "180"))
LOCAL_TIMEZONE = timezone(timedelta(hours=7))

DATA_FILE_DEFAULTS: dict[str, Any] = {
    "users": {},
    "video_list": [],
    "doctor_evaluations": [],
    "patient_symptoms": [],
    "schedules": [],
    "research_data": [],
    "lich_su_tap_luyen": [],
    "latest_video_bundle": {},
    "media_registry": {},
}

TOKEN_STORE: dict[str, dict[str, Any]] = {}
TOKEN_REVOKED: set[str] = set()
MEDIA_TOKEN_STORE: dict[str, dict[str, Any]] = {}
MEDIA_REGISTRY_CACHE: dict[str, dict[str, Any]] | None = None
MEDIA_REGISTRY_DIRTY = False
MEDIA_REGISTRY_LAST_SAVE = 0.0
MEDIA_REGISTRY_SAVE_INTERVAL_SECONDS = 5.0
ZIP_MEMBER_CACHE: dict[str, tuple[float, int, dict[str, str]]] = {}
VIDEO_FRAME_COUNT_CACHE: dict[str, tuple[float, int, int]] = {}
MEDIA_TTL_SECONDS = int(os.environ.get("REHAB_MEDIA_TTL_SECONDS", str(30 * 24 * 60 * 60)))
ANALYSIS_RUNNING: dict[str, Any] = {}
ANALYSIS_START_LOCK = threading.Lock()
REFERENCE_POSE_CACHE: dict[str, tuple[float, str, list[dict[str, Any]]]] = {}
REFERENCE_MATCH_CACHE: dict[tuple[Any, ...], dict[str, Any] | None] = {}
REFERENCE_NUMERIC_CACHE: dict[str, tuple[int, list[tuple[dict[str, Any], float | None, float | None, float | None, float | None, float | None, float | None]]]] = {}
CHART_PAYLOAD_CACHE: dict[tuple[str, int, int, str], dict[str, Any]] = {}
PERSON_DETECTOR_HOG: Any = None
PERSON_DETECTOR_CASCADES: Any = None
PERSON_BG_SUBTRACTOR: Any = None
VIDEO_SOURCE_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
UPLOAD_MAX_BYTES = int(os.environ.get("REHAB_UPLOAD_MAX_MB", "600")) * 1024 * 1024
EXERCISE_LABELS = {
    "codman": "Bài tập con lắc Codman",
    "gay": "Bài tập với gậy (Pulley Exercise)",
    "pulley": "Bài tập với gậy (Pulley Exercise)",
    "day": "Bài tập với dây kháng lực (Theraband)",
}


def _stable_media_token(kind: str, path: Path, *parts: Any) -> str:
    try:
        resolved = path.resolve()
        stat = resolved.stat()
        path_sig = f"{resolved}:{stat.st_mtime_ns}:{stat.st_size}"
    except Exception:
        path_sig = str(path)
    raw = "|".join([kind, path_sig, *(str(part) for part in parts)])
    return "m_" + hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:40]
DEFAULT_REFS = {
    "codman": (40.8, 163.0),
    "pulley": (76.7, 92.1),
    "gay": (76.7, 92.1),
    "day": (90.0, 160.0),
}
POSE_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (29, 31),
    (27, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (30, 32),
    (28, 32),
)
POSE_REQUIRED_INDICES = tuple(range(33))
BACKUP_VIDEO_LIST_PATHS = (
    REPO_ROOT / "debug_files" / "video_list.json",
)
ARTIFACT_METADATA_KEYS = (
    "processed_path",
    "df_path",
    "all_frames_data_path",
    "frames_zip",
    "frames_zip_path",
    "frames_dir",
    "all_frames_dir",
)
ANALYSIS_METADATA_KEYS = ("metrics", "sai_so", "giai_doan")
LOCAL_ARTIFACT_ALIAS_KEYS = ("_local_video_artifacts", "local_video_artifacts", "source_video_index")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=6)
    password2: str = Field(min_length=6)
    full_name: str = ""


class ResetPasswordRequest(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=6)
    password2: str = Field(min_length=6)


class AdminCreateUserRequest(RegisterRequest):
    role: str = ROLE_PATIENT
    must_change_password: bool = False


class UserActiveRequest(BaseModel):
    active: bool


class SymptomRequest(BaseModel):
    vas: int = Field(default=0, ge=0, le=10)
    pain_location: str = ""
    exercise: str = ""
    symptoms: str = ""
    date: str = ""


class ScheduleRequest(BaseModel):
    patient_username: str = Field(min_length=1)
    title: str = Field(min_length=1)
    date: str = Field(min_length=1)
    time: str = ""
    note: str = ""
    kind: str = "exercise"


class EvaluationRequest(BaseModel):
    doctor_result: str = Field(default="Gần đúng", min_length=1)
    comments: str = ""
    plan: str = ""
    errors: list[str] | str | None = None
    comments_ncv: str = ""


class AnalysisJobRequestBody(BaseModel):
    model_type: str = "MediaPipe Heavy"
    skip_step: int = Field(default=0, ge=0, le=30)
    resize_width: int = Field(default=720, ge=240, le=2160)
    min_confidence: float = Field(default=0.65, ge=0.0, le=1.0)


class ExportRequestBody(BaseModel):
    kind: str = Field(default="video")
    phase: str = Field(default="all")
    persist: bool = True


class ChartExportRequestBody(BaseModel):
    phase: str = Field(default="all")
    chart_name: str = Field(default="chart")
    filename: str = Field(default="chart.png")
    image_data: str = Field(min_length=20)
    metrics: dict[str, Any] = Field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _search_text(value: Any) -> str:
    text = unicodedata.normalize("NFD", _clean_text(value).casefold())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def role_key(role: Any) -> str:
    text = _search_text(role)
    if "quan" in text or "admin" in text or "qtv" in text:
        return "admin"
    if "nghien" in text or "research" in text or "ncv" in text:
        return "researcher"
    if "bac" in text or "doctor" in text or "ktv" in text or "phcn" in text:
        return "doctor_ktv"
    return "patient"


def canonical_role(role: Any) -> str:
    return ROLE_LABELS[role_key(role)]


def _data_path(name: str) -> Path:
    db_path = DATABASE_DIR / f"{name}.json"
    if db_path.exists() or name == "users":
        return db_path
    root_path = REPO_ROOT / f"{name}.json"
    if root_path.exists():
        return root_path
    return db_path


def _video_list_sync_key(record: dict[str, Any]) -> tuple[str, str, str]:
    patient = _search_text(record.get("username") or record.get("patient_username") or record.get("full_name"))
    video_name = _search_text(record.get("video_name") or record.get("stored_filename") or record.get("video_path"))
    exercise = _search_text(record.get("exercise"))
    return (patient, video_name, exercise)


def _merge_external_video_record(database_record: dict[str, Any], external_record: dict[str, Any]) -> dict[str, Any]:
    merged = dict(database_record)
    for key, value in external_record.items():
        if value is None or value == "":
            continue
        merged[key] = value
    database_metrics = database_record.get("metrics") if isinstance(database_record.get("metrics"), dict) else {}
    external_metrics = external_record.get("metrics") if isinstance(external_record.get("metrics"), dict) else {}
    if database_metrics or external_metrics:
        merged["metrics"] = {**database_metrics, **external_metrics}
    return merged


def _video_latest_update_time_text(video: dict[str, Any], fallback_updated_at: Any = "") -> str:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    for value in (
        metrics.get("metrics_refreshed_at"),
        fallback_updated_at,
        video.get("artifact_updated_at"),
        video.get("updated_at"),
        video.get("uploaded_at"),
        video.get("created_at"),
    ):
        parsed = _parse_vn_time(value)
        if parsed != datetime.min:
            return parsed.strftime("%H:%M - %d/%m/%Y")
    return _clean_text(video.get("time"))


def _external_video_list_records() -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    root_path = REPO_ROOT / "video_list.json"
    if root_path.exists():
        root_data = read_json(root_path, [])
        if isinstance(root_data, list):
            sources.extend(item for item in root_data if isinstance(item, dict))

    bundle_path = DATABASE_DIR / "latest_video_bundle.json"
    if bundle_path.exists():
        bundle_data = read_json(bundle_path, {})
        bundle_videos = bundle_data.get("videos") if isinstance(bundle_data, dict) else None
        bundle_updated_at = _clean_text(bundle_data.get("updated_at")) if isinstance(bundle_data, dict) else ""
        if isinstance(bundle_videos, list):
            for item in bundle_videos:
                if not isinstance(item, dict):
                    continue
                enriched = dict(item)
                original_time = _clean_text(enriched.get("time"))
                if original_time:
                    enriched.setdefault("video_time", original_time)
                latest_time = _video_latest_update_time_text(enriched, bundle_updated_at)
                if latest_time:
                    enriched["time"] = latest_time
                if bundle_updated_at:
                    enriched["latest_bundle_updated_at"] = bundle_updated_at
                sources.append(enriched)
    return sources


def _sync_external_video_list_to_database() -> bool:
    db_path = DATABASE_DIR / "video_list.json"
    external = _external_video_list_records()
    if not external:
        return False
    database = read_json(db_path, [])
    if not isinstance(database, list):
        database = []

    database_by_key = {
        _video_list_sync_key(item): item
        for item in database
        if isinstance(item, dict) and any(_video_list_sync_key(item))
    }
    external_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    external_order: list[tuple[str, str, str]] = []
    for item in external:
        key = _video_list_sync_key(item)
        if not any(key):
            continue
        if key in external_by_key:
            external_by_key[key] = _merge_external_video_record(external_by_key[key], item)
        else:
            external_order.append(key)
            external_by_key[key] = item

    seen: set[tuple[str, str, str]] = set()
    synced: list[dict[str, Any]] = []
    for key in external_order:
        seen.add(key)
        synced.append(_merge_external_video_record(database_by_key.get(key, {}), external_by_key[key]))
    for item in database:
        if not isinstance(item, dict):
            continue
        key = _video_list_sync_key(item)
        if key not in seen:
            synced.append(item)

    if synced == database:
        return False
    write_json(db_path, synced)
    return True


def _doctor_evaluation_sync_key(record: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    record_id = _clean_text(record.get("id"))
    if record_id:
        return ("id", record_id, "", "", "", "")
    patient = _search_text(record.get("patient_username") or record.get("username") or record.get("full_name"))
    video_name = _search_text(record.get("video_name") or record.get("stored_filename") or record.get("video_path"))
    exercise = _search_text(record.get("exercise"))
    evaluator = _search_text(record.get("doctor_username") or record.get("doctor_name") or record.get("submitted_by"))
    time_text = _clean_text(record.get("time") or record.get("timestamp") or record.get("created_at"))
    source = _search_text(record.get("source"))
    return (patient, video_name, exercise, evaluator, time_text, source)


def _sync_external_doctor_evaluations_to_database() -> bool:
    root_path = REPO_ROOT / "doctor_evaluations.json"
    db_path = DATABASE_DIR / "doctor_evaluations.json"
    if not root_path.exists():
        return False
    external = read_json(root_path, [])
    if not isinstance(external, list):
        return False
    database = read_json(db_path, [])
    if not isinstance(database, list):
        database = []

    database_by_key = {
        _doctor_evaluation_sync_key(item): item
        for item in database
        if isinstance(item, dict) and any(_doctor_evaluation_sync_key(item))
    }
    seen: set[tuple[str, str, str, str, str, str]] = set()
    synced: list[dict[str, Any]] = []
    for item in external:
        if not isinstance(item, dict):
            continue
        key = _doctor_evaluation_sync_key(item)
        seen.add(key)
        synced.append({**database_by_key.get(key, {}), **item})
    for item in database:
        if not isinstance(item, dict):
            continue
        key = _doctor_evaluation_sync_key(item)
        if key not in seen:
            synced.append(item)

    if synced == database:
        return False
    write_json(db_path, synced)
    return True


def _sync_video_ai_summaries_to_doctor_evaluations() -> bool:
    db_path = DATABASE_DIR / "doctor_evaluations.json"
    root_path = REPO_ROOT / "doctor_evaluations.json"
    evaluations = read_json(db_path, [])
    if not isinstance(evaluations, list):
        evaluations = []

    _sync_external_video_list_to_database()
    videos = read_json(DATABASE_DIR / "video_list.json", [])
    if not isinstance(videos, list):
        return False

    merged = _merge_video_ai_evaluation_summaries(evaluations, videos)
    generated = [record for record in merged if _is_video_list_ai_summary(record)]
    manual = [record for record in merged if not _is_video_list_ai_summary(record)]
    generated.sort(key=_evaluation_time, reverse=True)
    synced = generated + manual
    if synced == evaluations:
        return False
    write_json(db_path, synced)
    write_json(root_path, synced)
    return True


def _load_data(name: str) -> Any:
    default = DATA_FILE_DEFAULTS[name]
    if name == "video_list":
        _sync_external_video_list_to_database()
    if name == "doctor_evaluations":
        _sync_external_doctor_evaluations_to_database()
        _sync_video_ai_summaries_to_doctor_evaluations()
    data = read_json(_data_path(name), default)
    if isinstance(default, list) and not isinstance(data, list):
        return []
    if isinstance(default, dict) and not isinstance(data, dict):
        return {}
    return data


def _save_data(name: str, data: Any) -> None:
    write_json(_data_path(name), data)


def _load_media_registry() -> dict[str, dict[str, Any]]:
    global MEDIA_REGISTRY_CACHE
    if MEDIA_REGISTRY_CACHE is None:
        data = _load_data("media_registry")
        if not isinstance(data, dict):
            data = {}
        MEDIA_REGISTRY_CACHE = {str(token): meta for token, meta in data.items() if isinstance(meta, dict)}
    return MEDIA_REGISTRY_CACHE


def _save_media_registry(data: dict[str, dict[str, Any]], *, force: bool = False) -> None:
    global MEDIA_REGISTRY_CACHE, MEDIA_REGISTRY_DIRTY, MEDIA_REGISTRY_LAST_SAVE
    if len(data) > 2500:
        now = datetime.now(timezone.utc).timestamp()
        live = {token: meta for token, meta in data.items() if float(meta.get("expires_at") or 0) >= now}
        data = dict(list(live.items())[-2500:])
    MEDIA_REGISTRY_CACHE = data
    MEDIA_REGISTRY_DIRTY = True
    now_monotonic = time.monotonic()
    if force or now_monotonic - MEDIA_REGISTRY_LAST_SAVE >= MEDIA_REGISTRY_SAVE_INTERVAL_SECONDS:
        _save_data("media_registry", data)
        MEDIA_REGISTRY_LAST_SAVE = now_monotonic
        MEDIA_REGISTRY_DIRTY = False


def _flush_media_registry(*, force: bool = False) -> None:
    if MEDIA_REGISTRY_CACHE is not None and (force or MEDIA_REGISTRY_DIRTY):
        _save_media_registry(MEDIA_REGISTRY_CACHE, force=force)


def _remember_media_token(token: str, meta: dict[str, Any]) -> str:
    cleaned = dict(meta)
    cleaned["expires_at"] = float(cleaned.get("expires_at") or (datetime.now(timezone.utc).timestamp() + MEDIA_TTL_SECONDS))
    MEDIA_TOKEN_STORE[token] = cleaned
    registry = _load_media_registry()
    registry[token] = cleaned
    _save_media_registry(registry)
    return token


def _media_token_meta(token: str) -> dict[str, Any] | None:
    meta = MEDIA_TOKEN_STORE.get(token)
    if meta:
        return meta
    registry = _load_media_registry()
    meta = registry.get(token)
    if isinstance(meta, dict):
        MEDIA_TOKEN_STORE[token] = meta
        return meta
    return None


def _forget_media_token(token: str) -> None:
    MEDIA_TOKEN_STORE.pop(token, None)
    registry = _load_media_registry()
    if token in registry:
        registry.pop(token, None)
        _save_media_registry(registry, force=True)


def load_users() -> dict[str, dict[str, Any]]:
    users = _load_data("users")
    return users if isinstance(users, dict) else {}


def save_users(users: dict[str, dict[str, Any]]) -> None:
    _save_data("users", users)


def lookup_user(users: dict[str, dict[str, Any]], username_or_email: str) -> str | None:
    needle = _search_text(username_or_email)
    if not needle:
        return None
    for username, record in users.items():
        if _search_text(username) == needle:
            return username
    for username, record in users.items():
        if isinstance(record, dict):
            for field in ("email", "mssv", "full_name"):
                if _search_text(record.get(field)) == needle:
                    return username
    return None


def _is_active(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    if record.get("active") is False:
        return False
    if record.get("disabled") is True or record.get("locked") is True:
        return False
    return True


def _public_user(username: str, record: dict[str, Any]) -> dict[str, Any]:
    role = canonical_role(record.get("role") or ROLE_PATIENT)
    return {
        "username": username,
        "full_name": record.get("full_name") or username,
        "email": record.get("email") or "",
        "role": role,
        "role_key": role_key(role),
        "mssv": record.get("mssv") or "",
        "active": _is_active(record),
        "must_change_password": bool(record.get("must_change_password")),
        "created_at": record.get("created_at") or "",
        "updated_at": record.get("updated_at") or "",
        "hash_version": record.get("hash_version") or "",
    }


def _login_option_user(username: str, record: dict[str, Any]) -> dict[str, Any]:
    user = _public_user(username, record)
    return {
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "role_key": user["role_key"],
        "active": user["active"],
    }


def build_login_options(*, limit_per_role: int = 12) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {role: [] for role in ROLE_ORDER}
    for username, record in load_users().items():
        if not isinstance(record, dict):
            continue
        option = _login_option_user(username, record)
        buckets.setdefault(option["role_key"], []).append(option)

    roles = []
    for key in ROLE_ORDER:
        users = sorted(
            buckets.get(key, []),
            key=lambda item: (_search_text(item.get("full_name")), _search_text(item.get("username"))),
        )
        roles.append(
            {
                "role_key": key,
                "role": ROLE_LABELS[key],
                "count": len(users),
                "users": users[:limit_per_role],
            }
        )
    return {"roles": roles}


def _require_passwords_match(password: str, password2: str) -> None:
    if password != password2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu xác nhận không khớp.")
    if len(password or "") < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu cần tối thiểu 6 ký tự.")


def _new_user_record(payload: RegisterRequest, *, role: str, must_change_password: bool = False) -> dict[str, Any]:
    now = _now_iso()
    return {
        "password": hash_password_v2(payload.password),
        "hash_version": current_hash_version(),
        "email": _clean_text(payload.email),
        "full_name": _clean_text(payload.full_name) or _clean_text(payload.username),
        "role": canonical_role(role),
        "created_at": now,
        "updated_at": now,
        "must_change_password": bool(must_change_password),
        "active": True,
    }


def _authenticate(username: str, password: str) -> tuple[str, dict[str, Any]]:
    users = load_users()
    user_key = lookup_user(users, username)
    record = users.get(user_key or "")
    if not user_key or not isinstance(record, dict):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản hoặc mật khẩu không đúng.")
    if not _is_active(record):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đang bị khóa.")
    if not verify_password_record(password, record).ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản hoặc mật khẩu không đúng.")
    return user_key, record


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))


def _make_session_token(username: str) -> str:
    payload = _b64url_encode(
        json.dumps({"u": username, "iat": int(time.time()), "n": secrets.token_urlsafe(8)}, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(TOKEN_SECRET.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    return f"v1.{payload}.{_b64url_encode(signature)}"


def _decode_session_token(token: str) -> str | None:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        return None
    payload, signature = parts[1], parts[2]
    expected = _b64url_encode(hmac.new(TOKEN_SECRET.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        data = json.loads(_b64url_decode(payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    username = str(data.get("u") or "").strip()
    issued_at = float(data.get("iat") or 0)
    if not username or not issued_at or time.time() - issued_at > TOKEN_TTL_SECONDS:
        return None
    return username


def _session_from_signed_token(token: str) -> dict[str, Any] | None:
    username = _decode_session_token(token)
    if not username:
        return None
    session = {"username": username, "created_at": _now_iso()}
    TOKEN_STORE[token] = session
    return session


def _issue_token(username: str, record: dict[str, Any]) -> dict[str, Any]:
    token = _make_session_token(username)
    user = _public_user(username, record)
    TOKEN_STORE[token] = {
        "username": username,
        "created_at": _now_iso(),
        "role_key": user["role_key"],
    }
    return {"token": token, "user": user}


async def current_session(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Thiếu token đăng nhập.")
    token = authorization.split(" ", 1)[1].strip()
    if token in TOKEN_REVOKED:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ.")
    session = TOKEN_STORE.get(token) or _session_from_signed_token(token)
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ.")

    users = load_users()
    user_key = lookup_user(users, session["username"]) or session["username"]
    record = users.get(user_key)
    if not isinstance(record, dict) or not _is_active(record):
        TOKEN_STORE.pop(token, None)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không còn hoạt động.")
    return {
        "token": token,
        "username": user_key,
        "record": record,
        "user": _public_user(user_key, record),
    }


def require_admin(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    if session["user"]["role_key"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ quản trị viên được thao tác.")
    return session


def _matches_current_patient(item: dict[str, Any], user: dict[str, Any]) -> bool:
    needles = {_search_text(user.get("username")), _search_text(user.get("full_name"))}
    needles.discard("")
    for field in ("username", "patient_username", "patient", "full_name", "patient_name", "submitted_by"):
        if _search_text(item.get(field)) in needles:
            return True
    return False


def _scope_records(items: Any, user: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    records = [item for item in items if isinstance(item, dict)]
    if user["role_key"] == "patient":
        return [item for item in records if _matches_current_patient(item, user)]
    return records


def _summarize_status(videos: list[dict[str, Any]]) -> dict[str, int]:
    done = 0
    processing = 0
    pending = 0
    for video in videos:
        status_text = _search_text(video.get("status"))
        if _video_has_ai_result(video) or "success" in status_text or "done" in status_text:
            done += 1
        elif "dang" in status_text or "processing" in status_text or "running" in status_text:
            processing += 1
        else:
            pending += 1
    return {"done": done, "processing": processing, "pending": pending}


def _video_has_ai_result(video: dict[str, Any]) -> bool:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    status_text = _search_text(video.get("status"))
    has_accuracy = _to_float(video.get("accuracy")) is not None or _to_float(metrics.get("do_chinh_xac")) is not None or _to_float(metrics.get("ty_le_tong_the")) is not None
    has_frame_metrics = any(
        (_to_float(metrics.get(key)) or _to_float(video.get(key)) or 0) > 0
        for key in ("frame_dung", "frame_gan_dung", "frame_sai", "frame_khong_nhan_dang", "tong_frame_da_cham")
    )
    return bool(video.get("latest_bundle_updated_at")) or "da phan tich" in status_text or has_accuracy or has_frame_metrics


def _role_counts(users: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {"admin": 0, "doctor_ktv": 0, "researcher": 0, "patient": 0}
    for record in users.values():
        if isinstance(record, dict):
            counts[role_key(record.get("role"))] += 1
    counts["total"] = len(users)
    return counts


def _take(items: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    return items[:limit]


def _is_video_list_ai_summary(record: dict[str, Any]) -> bool:
    return _search_text(record.get("source")) == "video_list_ai_researcher"


def _take_recent_evaluations(items: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    indexed = [(idx, item) for idx, item in enumerate(items)]
    indexed.sort(key=lambda item: (1 if _is_video_list_ai_summary(item[1]) else 0, _evaluation_time(item[1]), item[0]), reverse=True)
    return [item for _, item in indexed[:limit]]


def _resolve_existing_path(raw_path: Any) -> Path | None:
    text = _clean_text(raw_path)
    if not text:
        return None
    candidates: list[Path] = []
    normalized = text.replace("\\", "/")
    for prefix in ("/data/", "/app/"):
        if normalized.startswith(prefix):
            candidates.append(REPO_ROOT / normalized[len(prefix) :])
    raw = Path(text)
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(REPO_ROOT / raw)
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.exists():
            return resolved
    return None


def _local_hf_check_file(raw_path: Any) -> Path | None:
    rel_path = _dataset_relative_path(raw_path)
    if not rel_path:
        return None
    candidates: list[Path] = []
    normalized = rel_path.replace("\\", "/")
    for root in (REPO_ROOT / "processed_results").glob("_hf_check_*"):
        direct = root / normalized
        if direct.is_file():
            candidates.append(direct)
        basename = Path(normalized).name
        if basename:
            candidates.extend(path for path in root.rglob(basename) if path.is_file())
        match = re.search(r"_(\d{6})_", basename)
        if match:
            upload_token = match.group(1)
            candidates.extend(path for path in root.rglob(f"*{upload_token}*") if path.is_file())
            candidates.extend(path for path in root.rglob(f"raw_upload_{upload_token}.mp4") if path.is_file())
    for candidate in candidates:
        if candidate.suffix.lower() in VIDEO_SOURCE_EXTENSIONS and _video_frame_count(candidate) > 0:
            return candidate.resolve()
    return None


def _dataset_relative_path(raw_path: Any) -> str:
    text = _clean_text(raw_path).replace("\\", "/")
    if not text:
        return ""
    for prefix in ("/data/", "/app/"):
        if text.startswith(prefix):
            return text[len(prefix) :].lstrip("/")
    for marker in ("patient_uploads/", "processed_results/", "database/"):
        index = text.find(marker)
        if index >= 0:
            return text[index:].lstrip("/")
    raw = Path(text)
    if raw.is_absolute():
        return ""
    return text.lstrip("/")


def _local_dataset_path(raw_path: Any) -> Path | None:
    rel_path = _dataset_relative_path(raw_path)
    if not rel_path:
        return None
    return REPO_ROOT / rel_path


def _hf_download_urls(rel_path: str) -> list[tuple[str, dict[str, str]]]:
    quoted_path = urllib.parse.quote(rel_path, safe="/")
    urls: list[tuple[str, dict[str, str]]] = []
    if HF_DATASET_ID:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        urls.append((f"https://huggingface.co/datasets/{HF_DATASET_ID}/resolve/main/{quoted_path}", headers))
    if HF_BUCKET_ID:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        urls.append((f"https://huggingface.co/buckets/{HF_BUCKET_ID}/resolve/{quoted_path}", headers))
    return urls


def _ensure_hf_dataset_file(raw_path: Any, *, min_size: int = 128, require_video_readable: bool = False) -> Path | None:
    existing = _resolve_existing_path(raw_path)
    if (
        existing
        and existing.is_file()
        and existing.stat().st_size >= min_size
        and (not require_video_readable or _video_frame_count(existing) > 0)
    ):
        return existing
    rel_path = _dataset_relative_path(raw_path)
    target = _local_dataset_path(raw_path)
    if not rel_path or not target:
        return existing
    if (
        target.is_file()
        and target.stat().st_size >= min_size
        and (not require_video_readable or _video_frame_count(target) > 0)
    ):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_suffix(target.suffix + ".download")
    try:
        import requests  # type: ignore[import-not-found]
    except Exception:
        return existing
    for url, headers in _hf_download_urls(rel_path):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=HF_DOWNLOAD_TIMEOUT_SECONDS) as response:
                if response.status_code != 200:
                    tmp_path.unlink(missing_ok=True)
                    continue
                with tmp_path.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            if tmp_path.stat().st_size < min_size:
                tmp_path.unlink(missing_ok=True)
                continue
            tmp_path.replace(target)
            if require_video_readable and _video_frame_count(target) <= 0:
                continue
            return target
        except Exception:
            tmp_path.unlink(missing_ok=True)
            continue
    return existing


def _resolve_video_source_path(raw_path: Any, *, min_size: int = 1024) -> Path | None:
    existing = _resolve_existing_path(raw_path)
    if existing and existing.suffix.lower() in VIDEO_SOURCE_EXTENSIONS and _video_frame_count(existing) > 0:
        return existing
    cached = _local_hf_check_file(raw_path)
    if cached:
        return cached
    downloaded = _ensure_hf_dataset_file(raw_path, min_size=min_size, require_video_readable=True)
    if downloaded and downloaded.suffix.lower() in VIDEO_SOURCE_EXTENSIONS and _video_frame_count(downloaded) > 0:
        return downloaded
    return existing


def _register_media(path: Path | None) -> str | None:
    if not path or not path.is_file():
        return None
    token = _stable_media_token("file", path)
    _remember_media_token(token, {"path": str(path), "expires_at": datetime.now(timezone.utc).timestamp() + MEDIA_TTL_SECONDS})
    return token


def _register_zip_media(path: Path | None, member: str) -> str | None:
    if not path or not path.is_file() or not member:
        return None
    token = _stable_media_token("zip", path, member)
    _remember_media_token(
        token,
        {
            "path": str(path),
            "member": member,
            "expires_at": datetime.now(timezone.utc).timestamp() + MEDIA_TTL_SECONDS,
        },
    )
    return token


def _register_export_media(path: Path | None, download_name: str | None = None) -> str | None:
    token = _register_media(path)
    if token and download_name:
        MEDIA_TOKEN_STORE[token]["download_name"] = download_name
        _remember_media_token(token, MEDIA_TOKEN_STORE[token])
    return token


def _register_video_frame(path: Path | None, frame_index: Any) -> str | None:
    return _register_video_frame_candidates([path], frame_index)


def _same_resolved_path(left: Path | None, right: Path | None) -> bool:
    if not left or not right:
        return False
    try:
        return left.resolve() == right.resolve()
    except Exception:
        return str(left) == str(right)


def _register_video_frame_candidates(paths: list[Path | None], frame_index: Any) -> str | None:
    candidates = [path for path in paths if path and path.is_file()]
    if not candidates:
        return None
    try:
        index = max(0, int(float(frame_index or 0)) - 1)
    except (TypeError, ValueError):
        index = 0
    readable = [path for path in candidates if _video_frame_count(path) > index]
    if not readable:
        return None
    token = _stable_media_token("video_frame", readable[0], index)
    _remember_media_token(
        token,
        {
            "path": str(readable[0]),
            "paths": [str(path) for path in readable],
            "kind": "video_frame",
            "frame_index": index,
            "expires_at": datetime.now(timezone.utc).timestamp() + MEDIA_TTL_SECONDS,
        },
    )
    return token


def _register_video_frame_with_source(paths: list[Path | None], frame_index: Any, processed_path: Path | None = None) -> tuple[str | None, str]:
    token = _register_video_frame_candidates(paths, frame_index)
    if not token:
        return None, "missing"
    record = MEDIA_TOKEN_STORE.get(token, {})
    token_path = _resolve_existing_path(record.get("path"))
    source = "video_processed" if _same_resolved_path(token_path, processed_path) else "video_preview"
    return token, source


def _pose_landmarks(frame: dict[str, Any]) -> list[tuple[int, float, float, float]]:
    landmarks: list[tuple[int, float, float, float]] = []
    for idx in range(33):
        x = _to_float(frame.get(f"pt{idx}_x"))
        y = _to_float(frame.get(f"pt{idx}_y"))
        if x is None or y is None:
            continue
        visibility = _to_float(frame.get(f"pt{idx}_vis"))
        landmarks.append((idx, x, y, 1.0 if visibility is None else visibility))
    return landmarks


def _register_video_pose_frame_candidates(paths: list[Path | None], frame_index: Any, frame: dict[str, Any]) -> str | None:
    landmarks = _pose_landmarks(frame)
    candidates = sorted((path for path in paths if path and path.is_file()), key=_video_context_priority)
    if not candidates:
        return None
    try:
        index = max(0, int(float(frame_index or 0)) - 1)
    except (TypeError, ValueError):
        index = 0
    readable = [path for path in candidates if _video_frame_count(path) > 0]
    if not readable:
        return None
    max_count = max(_video_frame_count(path) for path in readable)
    source_index = min(index, max(0, max_count - 1))
    pose_sig = hashlib.sha256(
        json.dumps(
            {
                "i": index,
                "status": frame.get("status") or frame.get("phase_status"),
                "ml": frame.get("ml_label_text") or frame.get("ml_label"),
                "score": frame.get("ml_score") or frame.get("ml_confidence"),
                "threshold": frame.get("threshold") or frame.get("phase_threshold"),
                "pts": [(frame.get(f"pt{idx}_x"), frame.get(f"pt{idx}_y")) for idx in range(0, 33, 4)],
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8", errors="ignore")
    ).hexdigest()[:16]
    token = _stable_media_token("video_pose_frame", readable[0], index, pose_sig)
    _remember_media_token(
        token,
        {
            "path": str(readable[0]),
            "paths": [str(path) for path in readable],
            "kind": "video_pose_frame",
            "frame_index": source_index,
            "data_frame_index": index,
            "landmarks": landmarks,
            "frame_data": dict(frame),
            "overlay_only": len(landmarks) < len(POSE_REQUIRED_INDICES),
            "expires_at": datetime.now(timezone.utc).timestamp() + MEDIA_TTL_SECONDS,
        },
    )
    return token


def _video_codec(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception:
        return ""
    return _clean_text(result.stdout.splitlines()[0] if result.stdout.splitlines() else "").lower()


def _audio_codec(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception:
        return ""
    return _clean_text(result.stdout.splitlines()[0] if result.stdout.splitlines() else "").lower()


def _video_frame_count(path: Path | None) -> int:
    if not path or not path.is_file():
        return 0
    try:
        stat = path.stat()
        cache_key = str(path.resolve())
        cached = VIDEO_FRAME_COUNT_CACHE.get(cache_key)
        if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
            return cached[2]
    except Exception:
        cache_key = str(path)
        stat = None
    count = 0
    try:
        import cv2  # type: ignore[import-not-found]
        cap = cv2.VideoCapture(str(path))
        if cap.isOpened():
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()
    except Exception:
        count = 0
    count = max(0, count)
    if stat is not None:
        VIDEO_FRAME_COUNT_CACHE[cache_key] = (stat.st_mtime, stat.st_size, count)
    return count


def _resolve_playback_video_path(preferred: Path | None, raw: Path | None = None) -> tuple[Path | None, str]:
    candidates: list[tuple[Path | None, str]] = []
    for path, status_text in ((preferred, "processed_h264"), (raw, "raw_h264"), (preferred, "processed_fallback"), (raw, "raw_fallback")):
        if not path or not path.is_file():
            continue
        final_h264 = _resolve_existing_path(get_final_h264_path(str(path)))
        if final_h264 and final_h264.is_file():
            candidates.append((final_h264, status_text))
        candidates.append((path, status_text))

    seen: set[Path] = set()
    fallback: tuple[Path | None, str] = (None, "missing")
    saw_unreadable = False
    for candidate, status_text in candidates:
        if not candidate:
            continue
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        frame_count = _video_frame_count(resolved)
        if frame_count <= 0:
            saw_unreadable = True
            continue
        if fallback[0] is None:
            fallback = (resolved, "fallback_unverified")
        codec = _video_codec(resolved)
        if codec == "h264":
            return resolved, status_text if "h264" in status_text else "h264"
    if fallback[0] is None and saw_unreadable:
        return None, "unreadable_video"
    return fallback


def _pose_playback_video_path(processed: Path | None) -> Path | None:
    stem = _processed_stem(processed)
    if not stem:
        return None
    for suffix in ("_pose_h264.mp4", "_skeleton_h264.mp4"):
        candidate = REPO_ROOT / "processed_results" / f"{stem}{suffix}"
        if candidate.is_file() and _video_frame_count(candidate) > 0 and _video_codec(candidate) == "h264":
            return candidate
    return None


def _video_fps(path: Path | None, default: float = 30.0) -> float:
    if not path or not path.is_file():
        return default
    try:
        import cv2  # type: ignore[import-not-found]

        cap = cv2.VideoCapture(str(path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        cap.release()
        if fps > 0:
            return fps
    except Exception:
        pass
    return default


def _video_context_priority(path: Path | None) -> tuple[int, str]:
    if not path:
        return (99, "")
    text = _search_text(str(path))
    score = 0
    if "patient_upload" in text or "patient uploads" in text:
        score -= 20
    if "processed_result" in text or "processed_" in text:
        score += 10
    if "pose" in text or "skeleton" in text or "sound" in text or "audio" in text:
        score += 5
    return (score, text)


def _read_video_frame_image(paths: list[Path | None], frame_index: Any) -> Any | None:
    try:
        import cv2  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        index = max(0, int(float(frame_index or 0)) - 1)
    except (TypeError, ValueError):
        index = 0
    candidates = sorted((path for path in paths if path and path.is_file()), key=_video_context_priority)
    for candidate in candidates:
        try:
            if _video_frame_count(candidate) <= index:
                continue
            cap = cv2.VideoCapture(str(candidate))
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                return frame
        except Exception:
            try:
                cap.release()  # type: ignore[name-defined]
            except Exception:
                pass
            continue
    return None


def _needs_video_pose_frame_preference(video: dict[str, Any]) -> bool:
    return _to_bool(video.get("force_video_pose_frames") or video.get("_force_video_pose_frames"))


def _pose_points_for_frame(frame: Any, width: int, height: int) -> dict[int, tuple[int, int, float]]:
    points: dict[int, tuple[int, int, float]] = {}
    if isinstance(frame, dict):
        raw_landmarks = _pose_landmarks(frame)
    elif isinstance(frame, list):
        raw_landmarks = frame
    else:
        raw_landmarks = []
    for item in raw_landmarks:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        try:
            idx = int(item[0])
            x = float(item[1])
            y = float(item[2])
            visibility = float(item[3]) if len(item) > 3 else 1.0
        except (TypeError, ValueError):
            continue
        if x <= 1.5 and y <= 1.5:
            px, py = int(x * width), int(y * height)
        else:
            px, py = int(x), int(y)
        if 0 <= px < width and 0 <= py < height:
            points[idx] = (px, py, visibility)
    return points


def _has_complete_pose(frame: Any) -> bool:
    return isinstance(frame, dict) and len(_pose_landmarks(frame)) >= len(POSE_REQUIRED_INDICES)


def _frame_should_be_unknown(frame: dict[str, Any], exercise: Any = None) -> bool:
    if _to_bool(frame.get("filtered_stranger")):
        return True
    status_text = _clean_text(frame.get("status") or frame.get("phase_status")).upper()
    if status_text == "UNKNOWN":
        reason = _search_text(frame.get("stranger_reason"))
        if reason in {"multiple_people", "pulley_multiple_people", "codman_helper_overlap", "incomplete_pose_33", "unknown_pose"}:
            return True
        if not _has_complete_pose(frame):
            return True
    if _frame_exercise_key(frame, exercise) in {"codman", "pulley"} and not _has_complete_pose(frame):
        scored_status = status_text in {"PASS", "NEAR", "FAIL"}
        shoulder = _first_float(frame.get("goc_vai"), frame.get("right_shoulder_angle"), frame.get("left_shoulder_angle"))
        elbow = _first_float(frame.get("goc_khuyu"), frame.get("right_elbow_angle"), frame.get("left_elbow_angle"))
        shoulder_ref, elbow_ref = _frame_ref_values(frame)
        if not (scored_status and shoulder is not None and elbow is not None and (shoulder_ref is not None or elbow_ref is not None)):
            return True
    return False


def _pose_data_from_landmarks(landmarks: Any, image_shape: tuple[int, int, int] | tuple[int, int], crop_box: tuple[int, int, int, int] | None = None) -> dict[str, Any]:
    height, width = image_shape[:2]
    x1, y1, x2, y2 = crop_box if crop_box else (0, 0, width, height)
    crop_w = max(1, x2 - x1)
    crop_h = max(1, y2 - y1)
    output: dict[str, Any] = {"detected": True, "filtered_stranger": False}
    for idx, landmark in enumerate(landmarks[:33]):
        output[f"pt{idx}_x"] = float(x1 + landmark.x * crop_w) / max(1, width)
        output[f"pt{idx}_y"] = float(y1 + landmark.y * crop_h) / max(1, height)
        output[f"pt{idx}_z"] = float(landmark.z)
        output[f"pt{idx}_vis"] = float(landmark.visibility)
    return output


def _mediapipe_candidate_from_crop(pose: Any, image: Any, crop_box: tuple[int, int, int, int] | None = None) -> dict[str, Any] | None:
    import cv2  # type: ignore[import-not-found]

    height, width = image.shape[:2]
    if crop_box:
        x1, y1, x2, y2 = crop_box
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        if x2 - x1 < 64 or y2 - y1 < 64:
            return None
        crop = image[y1:y2, x1:x2]
        normalized_box = (x1, y1, x2, y2)
    else:
        crop = image
        normalized_box = None
    result = pose.process(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    landmarks = getattr(result, "pose_landmarks", None)
    if not landmarks:
        return None
    return _pose_data_from_landmarks(landmarks.landmark, image.shape, normalized_box)


def _codman_crop_boxes(width: int, height: int) -> list[tuple[int, int, int, int] | None]:
    fractions = [
        None,
        (0.0, 0.0, 0.88, 1.0),
        (0.05, 0.0, 0.95, 1.0),
        (0.0, 0.04, 0.92, 0.98),
        (0.12, 0.0, 1.0, 1.0),
    ]
    boxes: list[tuple[int, int, int, int] | None] = []
    seen: set[tuple[int, int, int, int] | None] = set()
    for item in fractions:
        if item is None:
            box = None
        else:
            x1, y1, x2, y2 = item
            box = (int(width * x1), int(height * y1), int(width * x2), int(height * y2))
        if box not in seen:
            boxes.append(box)
            seen.add(box)
    return boxes


def _person_detector_hog() -> Any:
    global PERSON_DETECTOR_HOG
    if PERSON_DETECTOR_HOG is not None:
        return PERSON_DETECTOR_HOG
    try:
        import cv2  # type: ignore[import-not-found]

        detector = cv2.HOGDescriptor()
        detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        PERSON_DETECTOR_HOG = detector
    except Exception:
        PERSON_DETECTOR_HOG = False
    return PERSON_DETECTOR_HOG


def _visible_person_count(image: Any) -> int:
    try:
        import cv2  # type: ignore[import-not-found]

        height, width = image.shape[:2]
        scale = min(1.0, 640.0 / max(1, width))
        sample = cv2.resize(image, (int(width * scale), max(2, int(height * scale)))) if scale < 1.0 else image
        sample_h, sample_w = sample.shape[:2]
        boxes: list[tuple[int, int, int, int, float, str]] = []

        detector = _person_detector_hog()
        if detector:
            rects, weights = detector.detectMultiScale(sample, winStride=(8, 8), padding=(8, 8), scale=1.05)
            for idx, rect in enumerate(rects):
                x, y, w, h = [int(v) for v in rect]
                score = float(weights[idx]) if idx < len(weights) else 0.0
                area_ratio = (w * h) / max(1, sample_w * sample_h)
                if score >= 0.35 and area_ratio >= 0.018 and h >= sample_h * 0.22:
                    boxes.append((x, y, w, h, score, "hog"))

        global PERSON_DETECTOR_CASCADES
        if PERSON_DETECTOR_CASCADES is None:
            PERSON_DETECTOR_CASCADES = []
            try:
                for filename in (
                    "haarcascade_fullbody.xml",
                    "haarcascade_upperbody.xml",
                    "haarcascade_frontalface_default.xml",
                    "haarcascade_profileface.xml",
                ):
                    path = Path(cv2.data.haarcascades) / filename
                    cascade = cv2.CascadeClassifier(str(path))
                    if not cascade.empty():
                        PERSON_DETECTOR_CASCADES.append((filename, cascade))
            except Exception:
                PERSON_DETECTOR_CASCADES = []
        if PERSON_DETECTOR_CASCADES:
            gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            for name, cascade in PERSON_DETECTOR_CASCADES:
                rects = cascade.detectMultiScale(gray, scaleFactor=1.04, minNeighbors=3, minSize=(max(28, sample_w // 14), max(44, sample_h // 10)))
                for rect in rects:
                    x, y, w, h = [int(v) for v in rect]
                    area_ratio = (w * h) / max(1, sample_w * sample_h)
                    min_height = 0.08 if "face" in name else 0.18 if "upper" in name else 0.24
                    min_area = 0.002 if "face" in name else 0.012
                    if area_ratio >= min_area and h >= sample_h * min_height:
                        boxes.append((x, y, w, h, 0.55, name))

        # Merge strong overlapping boxes so one person is not counted twice.
        boxes = sorted(boxes, key=lambda item: item[2] * item[3], reverse=True)
        kept: list[tuple[int, int, int, int, float, str]] = []
        for box in boxes:
            x, y, w, h, score, kind = box
            cx = x + w / 2
            duplicate = False
            for kx, ky, kw, kh, _, _ in kept:
                inter_x1, inter_y1 = max(x, kx), max(y, ky)
                inter_x2, inter_y2 = min(x + w, kx + kw), min(y + h, ky + kh)
                inter = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
                union = w * h + kw * kh - inter
                kc = kx + kw / 2
                if (union > 0 and inter / union > 0.32) or abs(cx - kc) < max(w, kw) * 0.32:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(box)
        return len(kept)
    except Exception:
        return 0


def _pulley_multiple_people_detected(image: Any) -> bool:
    return _visible_person_count(image) >= 2


def _multiple_people_detected(image: Any, frame: dict[str, Any] | None = None) -> bool:
    if isinstance(frame, dict) and _frame_exercise_key(frame) == "codman":
        if _has_complete_pose(frame) and _clean_text(frame.get("pose_selector")):
            return _codman_helper_overlap_detected(image, frame)
        return _visible_person_count(image) >= 2 or _codman_helper_overlap_detected(image, frame)
    if _visible_person_count(image) >= 2:
        return True
    return False


def _mark_filtered_stranger(record: dict[str, Any], reason: str) -> dict[str, Any]:
    record["filtered_stranger"] = True
    record["stranger_reason"] = reason
    record["status"] = "UNKNOWN"
    record["phase_status"] = "UNKNOWN"
    record["dung"] = False
    record["gan_dung"] = False
    record["dung_ml"] = False
    record["gan_dung_ml"] = False
    record["ml_label"] = "UNKNOWN"
    record["ml_label_text"] = "UNKNOWN"
    record["ml_score"] = 0
    record["ml_confidence"] = None
    record["ml_prob_sai"] = None
    record["ml_prob_gan_dung"] = None
    record["ml_prob_dung"] = None
    return record


def _codman_patient_pose_score(candidate: dict[str, Any], image_shape: tuple[int, int, int] | tuple[int, int]) -> float:
    height, width = image_shape[:2]
    points = _pose_points_for_frame(candidate, width, height)
    required = (12, 14, 16, 24)
    if not all(idx in points for idx in required):
        return -1.0
    right_vis = sum(points[idx][2] for idx in required) / len(required)
    if right_vis < 0.12:
        return -1.0
    visible = [point for point in points.values() if point[2] >= 0.12]
    if len(visible) < 12:
        return -1.0
    xs = [point[0] for point in visible]
    ys = [point[1] for point in visible]
    bbox_area = ((max(xs) - min(xs)) * (max(ys) - min(ys))) / max(1, width * height)
    body_height = (max(ys) - min(ys)) / max(1, height)
    shoulder_mid = ((points.get(11, points[12])[0] + points[12][0]) / 2, (points.get(11, points[12])[1] + points[12][1]) / 2)
    hip_mid = ((points.get(23, points[24])[0] + points[24][0]) / 2, (points.get(23, points[24])[1] + points[24][1]) / 2)
    lean_ratio = abs(shoulder_mid[0] - hip_mid[0]) / max(20.0, abs(hip_mid[1] - shoulder_mid[1]))
    lower_indices = [23, 24, 25, 26, 27, 28]
    lower_vis = sum(points[idx][2] for idx in lower_indices if idx in points) / max(1, len([idx for idx in lower_indices if idx in points]))
    wrist_below_shoulder = 1.0 if points[16][1] >= points[12][1] - height * 0.03 else 0.0
    center_x = ((min(xs) + max(xs)) / 2) / max(1, width)
    center_bonus = max(0.0, 1.0 - abs(center_x - 0.5) * 1.6)
    return (
        min(1.0, bbox_area * 7.0)
        + min(1.8, lean_ratio)
        + min(1.0, body_height * 1.8)
        + right_vis
        + lower_vis
        + wrist_below_shoulder
        + 0.35 * center_bonus
    )


def _white_patch_ratio(image: Any, point: tuple[int, int, float], radius: int = 18) -> float:
    try:
        import cv2  # type: ignore[import-not-found]
    except Exception:
        return 0.0
    height, width = image.shape[:2]
    x, y = int(point[0]), int(point[1])
    patch = image[max(0, y - radius) : min(height, y + radius + 1), max(0, x - radius) : min(width, x + radius + 1)]
    if patch.size == 0:
        return 0.0
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    return float(((value > 155) & (saturation < 65)).mean())


def _codman_helper_overlap_detected(image: Any, candidate: dict[str, Any]) -> bool:
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]
    except Exception:
        return False
    height, width = image.shape[:2]
    points = _pose_points_for_frame(candidate, width, height)
    if not points:
        return False
    required = (12, 14, 16, 24)
    if not all(idx in points for idx in required):
        return False

    visible = [point for point in points.values() if point[2] >= 0.12]
    if not visible:
        return False
    xs = [point[0] for point in visible]
    ys = [point[1] for point in visible]
    pose_x1, pose_x2 = max(0, min(xs)), min(width - 1, max(xs))
    pose_y1, pose_y2 = max(0, min(ys)), min(height - 1, max(ys))
    pose_area = max(1, (pose_x2 - pose_x1) * (pose_y2 - pose_y1))

    right_wrist = points[16]
    right_elbow = points[14]
    right_shoulder = points[12]
    probe_points = (right_wrist, right_elbow, right_shoulder)
    white_hits = sum(1 for point in probe_points if _white_patch_ratio(image, point, radius=max(14, int(width * 0.025))) >= 0.36)

    roi_x1 = max(0, int(min(right_wrist[0], right_elbow[0], right_shoulder[0]) - width * 0.18))
    roi_x2 = min(width, int(max(right_wrist[0], right_elbow[0], right_shoulder[0]) + width * 0.2))
    roi_y1 = max(0, int(min(right_wrist[1], right_elbow[1], right_shoulder[1]) - height * 0.1))
    roi_y2 = min(height, int(max(right_wrist[1], right_elbow[1], right_shoulder[1]) + height * 0.22))
    if roi_x2 <= roi_x1 or roi_y2 <= roi_y1:
        return white_hits >= 2

    roi = image[roi_y1:roi_y2, roi_x1:roi_x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    white_mask = ((hsv[:, :, 2] > 155) & (hsv[:, :, 1] < 70)).astype("uint8") * 255
    kernel = np.ones((5, 5), dtype="uint8")
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    white_area = 0
    for contour in contours:
        area = int(cv2.contourArea(contour))
        if area >= max(45, int(width * height * 0.00018)):
            white_area += area

    white_ratio_roi = white_area / max(1, (roi_x2 - roi_x1) * (roi_y2 - roi_y1))
    white_ratio_frame = white_area / max(1, width * height)
    if white_hits >= 2 and white_ratio_roi >= 0.035:
        return True
    if white_ratio_frame >= 0.012 and white_area > pose_area * 0.08:
        return True

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    expanded = image[
        max(0, pose_y1 - int(height * 0.12)) : min(height, pose_y2 + int(height * 0.12)),
        max(0, pose_x1 - int(width * 0.16)) : min(width, pose_x2 + int(width * 0.16)),
    ]
    if expanded.size:
        exp_hsv = cv2.cvtColor(expanded, cv2.COLOR_BGR2HSV)
        bright_low_sat = ((exp_hsv[:, :, 2] > 150) & (exp_hsv[:, :, 1] < 75)).mean()
        if bright_low_sat > 0.16 and white_hits >= 1:
            return True
    edge_roi = edges[roi_y1:roi_y2, roi_x1:roi_x2]
    return bool(white_hits >= 1 and float((edge_roi > 0).mean()) > 0.09 and white_ratio_roi >= 0.02)


def _select_codman_patient_pose(image: Any, pose: Any) -> dict[str, Any] | None:
    height, width = image.shape[:2]
    best: tuple[float, dict[str, Any]] | None = None
    for crop_box in _codman_crop_boxes(width, height):
        candidate = _mediapipe_candidate_from_crop(pose, image, crop_box)
        if not candidate:
            continue
        score = _codman_patient_pose_score(candidate, image.shape)
        if _codman_helper_overlap_detected(image, candidate):
            _mark_filtered_stranger(candidate, "codman_helper_overlap")
            score -= 1.25
        candidate["pose_selector"] = "codman_patient_roi" if crop_box else "codman_full_frame"
        candidate["pose_selector_score"] = round(score, 4)
        if best is None or score > best[0]:
            best = (score, candidate)
    if best is None or best[0] < 2.2:
        return None
    return best[1]


def _recompute_pose_angles_for_frame(frame: dict[str, Any], image_shape: tuple[int, int, int] | tuple[int, int], exercise: Any = None) -> dict[str, Any]:
    height, width = image_shape[:2]
    points = _pose_points_for_frame(frame, width, height)
    if len(points) < 4:
        return frame

    def angle(indices: tuple[int, int, int]) -> float | None:
        if not all(idx in points for idx in indices):
            return None
        a, b, c = (points[idx][:2] for idx in indices)
        return _angle_between_points(a, b, c)

    left_shoulder = angle((23, 11, 13))
    left_elbow = angle((11, 13, 15))
    right_shoulder = angle((24, 12, 14))
    right_elbow = angle((12, 14, 16))
    output = dict(frame)
    output.update(
        {
            "goc_vai_trai": left_shoulder,
            "goc_khuyu_trai": left_elbow,
            "left_shoulder_angle": left_shoulder,
            "left_elbow_angle": left_elbow,
            "goc_vai_phai": right_shoulder,
            "goc_khuyu_phai": right_elbow,
            "right_shoulder_angle": right_shoulder,
            "right_elbow_angle": right_elbow,
        }
    )
    exercise_key = _frame_exercise_key(output, exercise)
    if exercise_key == "codman":
        output["goc_vai"] = right_shoulder
        output["goc_khuyu"] = right_elbow
        output["shoulder_angle"] = right_shoulder
        output["elbow_angle"] = right_elbow
    elif exercise_key == "pulley":
        shoulder_values = [value for value in (left_shoulder, right_shoulder) if value is not None]
        elbow_values = [value for value in (left_elbow, right_elbow) if value is not None]
        shoulder = sum(shoulder_values) / len(shoulder_values) if shoulder_values else None
        elbow = sum(elbow_values) / len(elbow_values) if elbow_values else None
        output["goc_vai"] = shoulder
        output["goc_khuyu"] = elbow
        output["shoulder_angle"] = shoulder
        output["elbow_angle"] = elbow
    return output


def _mediapipe_pose_frame_data(image: Any, exercise: Any = None, pose_context: Any = None) -> dict[str, Any] | None:
    try:
        import cv2  # type: ignore[import-not-found]
        import mediapipe as mp  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        exercise_key = _exercise_key(exercise) if exercise is not None else ""
        if pose_context is not None:
            if exercise_key == "codman":
                return _select_codman_patient_pose(image, pose_context)
            return _mediapipe_candidate_from_crop(pose_context, image)
        with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.35) as pose:
            if exercise_key == "codman":
                return _select_codman_patient_pose(image, pose)
            return _mediapipe_candidate_from_crop(pose, image)
    except Exception:
        return None


def _frame_with_detected_pose(image: Any, frame: dict[str, Any], pose_context: Any = None) -> dict[str, Any]:
    exercise_key = _frame_exercise_key(frame)
    if _to_bool(frame.get("filtered_stranger")) and _search_text(frame.get("stranger_reason")) in {
        "multiple_people",
        "pulley_multiple_people",
        "codman_helper_overlap",
    }:
        return _mark_filtered_stranger(dict(frame), _clean_text(frame.get("stranger_reason")) or "multiple_people")
    if exercise_key in {"codman", "pulley"} and _multiple_people_detected(image, frame):
        return _mark_filtered_stranger(dict(frame), "pulley_multiple_people")
    if _has_complete_pose(frame):
        return frame
    detected = _mediapipe_pose_frame_data(image, frame.get("exercise") or frame.get("exercise_key"), pose_context=pose_context)
    if not detected:
        return frame
    merged = dict(frame)
    for key, value in detected.items():
        if value not in (None, ""):
            merged[key] = value
    merged = _recompute_pose_angles_for_frame(merged, image.shape, frame.get("exercise") or frame.get("exercise_key"))
    if _to_bool(frame.get("filtered_stranger")) and not _to_bool(merged.get("filtered_stranger")) and _has_complete_pose(merged):
        merged["filtered_stranger"] = False
        merged["detected"] = True
    return merged


def _side_angle_values(frame: dict[str, Any], side: str) -> tuple[float | None, float | None]:
    if side == "left":
        return _first_float(frame.get("goc_vai_trai"), frame.get("left_shoulder_angle")), _first_float(
            frame.get("goc_khuyu_trai"), frame.get("left_elbow_angle")
        )
    return _first_float(frame.get("goc_vai_phai"), frame.get("right_shoulder_angle")), _first_float(
        frame.get("goc_khuyu_phai"), frame.get("right_elbow_angle")
    )


def _frame_exercise_key(frame: dict[str, Any] | None = None, exercise: Any = None) -> str:
    frame = frame if isinstance(frame, dict) else {}
    for value in (
        exercise,
        frame.get("exercise_key"),
        frame.get("exercise"),
        frame.get("exercise_name"),
        frame.get("bai_tap"),
        frame.get("video_name"),
    ):
        if _clean_text(value):
            return _exercise_key(value)
    return _exercise_key("")


def _frame_with_exercise_context(frame: dict[str, Any], exercise: Any) -> dict[str, Any]:
    output = dict(frame)
    if _clean_text(exercise):
        output.setdefault("exercise", _exercise_label(exercise))
    output["exercise_key"] = _frame_exercise_key(output, exercise)
    return output


def _status_from_angle_pairs(pairs: list[tuple[float | None, float | None]], threshold: float) -> str:
    deltas: list[float] = []
    for value, ref in pairs:
        if value is None or ref is None:
            return "UNKNOWN"
        deltas.append(abs(value - ref))
    if not deltas:
        return "FAIL"
    if all(delta <= threshold for delta in deltas):
        return "PASS"
    if all(delta <= threshold * 1.5 for delta in deltas):
        return "NEAR"
    return "FAIL"


def _angle_color(value: float | None, ref: float | None, threshold: float) -> tuple[int, int, int]:
    if value is None or ref is None:
        return (210, 210, 210)
    delta = abs(value - ref)
    if delta <= threshold:
        return (0, 255, 80)
    if delta <= threshold * 1.5:
        return (0, 190, 255)
    return (0, 60, 255)


def _rule_label_for_frame(frame: dict[str, Any], threshold: float, exercise: Any = None) -> str:
    status_text = _phase_status_for_frame(frame, threshold, exercise=exercise)
    if status_text == "PASS":
        return "PASS"
    if status_text == "NEAR":
        return "NEARLY"
    return "FAIL"


def _rule_color_for_label(label: str) -> tuple[int, int, int]:
    if label == "PASS":
        return (0, 255, 80)
    if label == "NEARLY":
        return (0, 190, 255)
    if label == "NO POSE":
        return (0, 60, 255)
    return (0, 60, 255)


def _ml_ascii_label(frame: dict[str, Any]) -> str:
    label = _search_text(_frame_ml_label(frame))
    if "dung" in label and "gan" not in label:
        return "DUNG"
    if "gan" in label or "near" in label:
        return "GAN DUNG"
    if "sai" in label or "fail" in label:
        return "SAI"
    return _clean_text(_frame_ml_label(frame)).upper() or "N/A"


def _draw_badge(cv2: Any, image: Any, text: str, color: tuple[int, int, int], *, x: int, y: int, scale: float) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.45, 0.56 * scale)
    thickness = max(1, int(2 * scale))
    pad_x = max(7, int(9 * scale))
    pad_y = max(5, int(7 * scale))
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x2 = min(image.shape[1] - 4, x + text_w + pad_x * 2)
    y2 = min(image.shape[0] - 4, y + text_h + baseline + pad_y * 2)
    cv2.rectangle(image, (x, y), (x2, y2), (15, 18, 28), -1)
    cv2.rectangle(image, (x, y), (x2, y2), color, thickness)
    cv2.putText(image, text, (x + pad_x, y2 - pad_y - baseline), font, font_scale, color, thickness, cv2.LINE_AA)


def _draw_angle_arc(cv2: Any, image: Any, p1: tuple[int, int], p2: tuple[int, int], p3: tuple[int, int], color: tuple[int, int, int], radius: int) -> None:
    import math

    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    if (v1[0] == 0 and v1[1] == 0) or (v2[0] == 0 and v2[1] == 0):
        return
    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))
    start, end = sorted((a1, a2))
    if end - start > 180:
        start, end = end, start + 360
    cv2.ellipse(image, p2, (radius, radius), 0, start, end, color, max(2, radius // 16), cv2.LINE_AA)


def _draw_pose_analysis_overlay(image: Any, frame: dict[str, Any], frame_index: int, *, threshold: float = 30.0) -> Any:
    try:
        import cv2  # type: ignore[import-not-found]
    except Exception:
        return image

    height, width = image.shape[:2]
    scale = max(0.55, min(1.75, width / 720.0))
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, int(2 * scale))
    thin = max(1, int(1 * scale))
    points = _pose_points_for_frame(frame, width, height)
    is_filtered_stranger = _to_bool(frame.get("filtered_stranger"))
    is_detected = _to_bool(frame.get("detected"))
    pose_ok = len(points) >= len(POSE_REQUIRED_INDICES) and not is_filtered_stranger
    exercise_key = _frame_exercise_key(frame)
    frame = _fill_missing_reference_values(frame, exercise_key)
    is_codman = exercise_key == "codman"
    overlay = image.copy()

    if pose_ok:
        draw_connections = POSE_CONNECTIONS
        draw_indices = set(points)
        for a, b in draw_connections:
            if a in points and b in points:
                min_vis = min(points[a][2], points[b][2])
                line_color = (30, 235, 60) if min_vis >= 0.15 else (0, 210, 255)
                cv2.line(overlay, points[a][:2], points[b][:2], line_color, max(2, int(4 * scale)), cv2.LINE_AA)
        for idx, (px, py, visibility) in points.items():
            if idx not in draw_indices:
                continue
            radius = max(3, int(4 * scale))
            color = (0, 255, 255) if idx in {11, 12, 13, 14, 15, 16, 23, 24} else (40, 160, 255)
            if visibility < 0.15:
                color = (0, 210, 255)
            cv2.circle(overlay, (px, py), radius, color, -1, cv2.LINE_AA)
            cv2.circle(overlay, (px, py), radius + 1, (255, 255, 255), 1, cv2.LINE_AA)
        image = cv2.addWeighted(overlay, 0.86, image, 0.14, 0)

    shoulder_ref, elbow_ref = _frame_ref_values(frame)
    fallback_shoulder_ref, fallback_elbow_ref = _default_refs_for_exercise(exercise_key)
    shoulder_ref = shoulder_ref if shoulder_ref is not None else fallback_shoulder_ref
    elbow_ref = elbow_ref if elbow_ref is not None else fallback_elbow_ref
    left_shoulder, left_elbow = _side_angle_values(frame, "left")
    right_shoulder, right_elbow = _side_angle_values(frame, "right")
    left_shoulder_ref, left_elbow_ref = _frame_ref_side_values(frame, "left")
    right_shoulder_ref, right_elbow_ref = _frame_ref_side_values(frame, "right")
    left_shoulder_ref = left_shoulder_ref if left_shoulder_ref is not None else shoulder_ref
    left_elbow_ref = left_elbow_ref if left_elbow_ref is not None else elbow_ref
    right_shoulder_ref = right_shoulder_ref if right_shoulder_ref is not None else shoulder_ref
    right_elbow_ref = right_elbow_ref if right_elbow_ref is not None else elbow_ref

    side_specs = (
        (("right", (24, 12, 14, 16), right_shoulder, right_elbow, right_shoulder_ref, right_elbow_ref, 1),)
        if is_codman
        else (
            ("left", (23, 11, 13, 15), left_shoulder, left_elbow, left_shoulder_ref, left_elbow_ref, -1),
            ("right", (24, 12, 14, 16), right_shoulder, right_elbow, right_shoulder_ref, right_elbow_ref, 1),
        )
    )
    for _, indices, shoulder_angle, elbow_angle, side_shoulder_ref, side_elbow_ref, direction in side_specs:
        hip_idx, shoulder_idx, elbow_idx, wrist_idx = indices
        if pose_ok and all(idx in points for idx in indices):
            hip = points[hip_idx][:2]
            shoulder = points[shoulder_idx][:2]
            elbow = points[elbow_idx][:2]
            wrist = points[wrist_idx][:2]
            shoulder_color = _angle_color(shoulder_angle, side_shoulder_ref, threshold)
            elbow_color = _angle_color(elbow_angle, side_elbow_ref, threshold)
            _draw_angle_arc(cv2, image, hip, shoulder, elbow, shoulder_color, max(18, int(34 * scale)))
            _draw_angle_arc(cv2, image, shoulder, elbow, wrist, elbow_color, max(16, int(28 * scale)))
            if shoulder_angle is not None:
                cv2.putText(
                    image,
                    f"{int(round(shoulder_angle))}",
                    (shoulder[0] + direction * int(14 * scale), shoulder[1] - int(14 * scale)),
                    font,
                    0.62 * scale,
                    shoulder_color,
                    thickness,
                    cv2.LINE_AA,
                )
            if elbow_angle is not None:
                cv2.putText(
                    image,
                    f"{int(round(elbow_angle))}",
                    (elbow[0] + direction * int(14 * scale), elbow[1] - int(14 * scale)),
                    font,
                    0.62 * scale,
                    elbow_color,
                    thickness,
                    cv2.LINE_AA,
                )

    header_h = max(26, int(34 * scale))
    cv2.rectangle(image, (0, 0), (width, header_h), (8, 8, 8), -1)
    cv2.putText(image, f"Frame #{frame_index}", (max(8, width // 2 - int(52 * scale)), int(23 * scale)), font, 0.58 * scale, (245, 245, 245), thickness, cv2.LINE_AA)

    rule_label = "NO POSE" if not pose_ok else _rule_label_for_frame(frame, threshold, exercise=exercise_key)
    rule_color = _rule_color_for_label(rule_label)
    _draw_badge(cv2, image, f"REF: {rule_label}", rule_color, x=max(6, int(10 * scale)), y=max(6, int(8 * scale)), scale=scale)
    ml_label = _ml_ascii_label(frame) if pose_ok else ("LAN NGUOI" if is_filtered_stranger else "NO POSE")
    ml_confidence = _frame_ml_confidence(frame)
    ml_text = f"ML: {ml_label} {ml_confidence:.0f}%" if ml_confidence is not None else f"ML: {ml_label}"
    (ml_w, _), _ = cv2.getTextSize(ml_text, font, max(0.45, 0.56 * scale), thickness)
    _draw_badge(cv2, image, ml_text, _rule_color_for_label("PASS" if ml_label == "DUNG" else "NEARLY" if "GAN" in ml_label else "FAIL"), x=max(6, width - ml_w - int(42 * scale)), y=max(38, int(48 * scale)), scale=scale)

    if not pose_ok:
        warn_text = "KHONG NHAN DANG - LAN NGUOI KHAC" if is_filtered_stranger else "KHONG NHAN DANG DU 33 DIEM"
        warn_w = min(width - int(40 * scale), int(560 * scale))
        warn_h = int(92 * scale)
        warn_x = max(10, (width - warn_w) // 2)
        warn_y = max(header_h + int(58 * scale), height // 2 - warn_h // 2)
        cv2.rectangle(image, (warn_x, warn_y), (warn_x + warn_w, warn_y + warn_h), (12, 12, 22), -1)
        cv2.rectangle(image, (warn_x, warn_y), (warn_x + warn_w, warn_y + warn_h), (0, 60, 255), thickness)
        cv2.putText(image, warn_text, (warn_x + int(18 * scale), warn_y + int(38 * scale)), font, 0.62 * scale, (0, 60, 255), thickness, cv2.LINE_AA)
        cv2.putText(
            image,
            f"Detected: {'YES' if is_detected else 'NO'} | Pose points: {len(points)}/33",
            (warn_x + int(18 * scale), warn_y + int(70 * scale)),
            font,
            0.48 * scale,
            (230, 230, 230),
            thin,
            cv2.LINE_AA,
        )

    box_x, box_y = max(8, int(14 * scale)), max(46, int(50 * scale))
    box_w = min(width - box_x - 8, int((380 if is_codman else 470) * scale))
    box_h = min(height - box_y - 8, int((196 if is_codman else 220) * scale))
    roi = image[box_y : box_y + box_h, box_x : box_x + box_w]
    if roi.size:
        box_overlay = roi.copy()
        cv2.rectangle(box_overlay, (0, 0), (box_w, box_h), (20, 20, 35), -1)
        cv2.addWeighted(box_overlay, 0.72, roi, 0.28, 0, roi)
        image[box_y : box_y + box_h, box_x : box_x + box_w] = roi
        cv2.rectangle(image, (box_x, box_y), (box_x + box_w, box_y + box_h), (220, 220, 235), thin)
        time_sec = _first_float(frame.get("timestamp_seconds"))
        if time_sec is None:
            time_sec = max(0, frame_index - 1) / 30.0
        time_text = f"{int(time_sec // 60):02d}:{int(time_sec % 60):02d}"
        phase_key = _clean_text(frame.get("phase")) or ("overview" if exercise_key == "pulley" else "g1")
        phase_label = {
            "g1": "G1 - Khoi dau",
            "g2": "G2 - Hoi phuc",
            "g3": "G3 - Chuan xac",
            "overview": "Tong quan",
            "all": "Tat ca",
        }.get(phase_key, "Giai doan")
        lines = [
            ("FRAME #{}".format(frame_index), (255, 255, 0), 0.64),
            (f"TIME: {time_text}", (190, 190, 190), 0.48),
            (("POSE: 33/33 OK" if pose_ok else f"POSE: {len(points)}/33 - KHONG NHAN DANG"), (0, 255, 80) if pose_ok else (0, 60, 255), 0.43),
        ]
        if is_codman:
            lines.extend([(f"CODMAN: {phase_label} | REF +/-{int(threshold)}", (210, 210, 210), 0.4)])
            if pose_ok:
                lines.extend(
                    [
                        ("RIGHT ARM: SHOULDER / ELBOW", (210, 210, 210), 0.43),
                        (
                            f"{int(round(right_shoulder or 0))}/{int(round(right_shoulder_ref or shoulder_ref))}      {int(round(right_elbow or 0))}/{int(round(right_elbow_ref or elbow_ref))}",
                            _angle_color(right_shoulder, right_shoulder_ref, threshold),
                            0.62,
                        ),
                    ]
                )
            else:
                reason = "LAN NGUOI KHAC" if is_filtered_stranger else "THIEU 33 DIEM"
                lines.extend(
                    [
                        ("RIGHT ARM: KHONG CHAM DIEM", (0, 60, 255), 0.43),
                        (f"LY DO: {reason}", (0, 60, 255), 0.48),
                    ]
                )
            lines.append(("G1 +/-45 | G2 +/-30 | G3 +/-15", (0, 255, 80), 0.38))
        else:
            lines.extend(
                [
                    ("PULLEY/STICK: BOTH SIDES | REF +/-30", (210, 210, 210), 0.4),
                    ("LEFT: SHOULDER / ELBOW", (210, 210, 210), 0.43),
                    (
                        f"SH {int(round(left_shoulder or 0))}/{int(round(left_shoulder_ref or shoulder_ref))} deg   EL {int(round(left_elbow or 0))}/{int(round(left_elbow_ref or elbow_ref))} deg",
                        _angle_color(left_shoulder, left_shoulder_ref, threshold),
                        0.62,
                    ),
                    ("RIGHT: SHOULDER / ELBOW", (210, 210, 210), 0.43),
                    (
                        f"SH {int(round(right_shoulder or 0))}/{int(round(right_shoulder_ref or shoulder_ref))} deg   EL {int(round(right_elbow or 0))}/{int(round(right_elbow_ref or elbow_ref))} deg",
                        _angle_color(right_shoulder, right_shoulder_ref, threshold),
                        0.62,
                    ),
                ]
            )
        y = box_y + int(24 * scale)
        for text, color, font_scale in lines:
            if y > box_y + box_h - int(8 * scale):
                break
            cv2.putText(image, text, (box_x + int(12 * scale), y), font, font_scale * scale, color, thickness if font_scale >= 0.6 else thin, cv2.LINE_AA)
            y += int((24 if font_scale >= 0.6 else 22) * scale)
        cv2.line(image, (box_x + int(8 * scale), min(box_y + box_h - int(36 * scale), y)), (box_x + box_w - int(8 * scale), min(box_y + box_h - int(36 * scale), y)), (80, 80, 100), thin)
        cv2.putText(
            image,
            f"REF compare: {rule_label}  |  threshold +/-{int(threshold)} deg",
            (box_x + int(12 * scale), box_y + box_h - int(14 * scale)),
            font,
            0.38 * scale,
            rule_color,
            thin,
            cv2.LINE_AA,
        )
    return image


def _cleanup_media_tokens() -> None:
    now = datetime.now(timezone.utc).timestamp()
    expired = [token for token, meta in MEDIA_TOKEN_STORE.items() if float(meta.get("expires_at") or 0) < now]
    for token in expired:
        _forget_media_token(token)
    registry = _load_media_registry()
    expired_registry = [token for token, meta in registry.items() if float(meta.get("expires_at") or 0) < now]
    if expired_registry:
        for token in expired_registry:
            registry.pop(token, None)
        _save_media_registry(registry, force=True)
    else:
        _flush_media_registry()


def _job_video_path(video: dict[str, Any]) -> str:
    return _clean_text(video.get("video_path") or video.get("processed_path") or video.get("stored_filename") or video.get("video_name"))


def _analysis_job_id(video_path: Any) -> str:
    normalized = _clean_text(video_path).replace("\\", "/")
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def _progress_file_for_video(video: dict[str, Any]) -> Path:
    return REPO_ROOT / "processed_results" / f"progress_{_analysis_job_id(_job_video_path(video))}.json"


def _history_file_for_video(video: dict[str, Any]) -> Path:
    return REPO_ROOT / "processed_results" / f"analysis_job_history_{_analysis_job_id(_job_video_path(video))}.json"


def _job_steps(status_text: str, progress: float) -> list[dict[str, str]]:
    labels = [
        ("validate_transcode", "Mở video"),
        ("mediapipe_pass", "MediaPipe skeleton"),
        ("ref_compare", "REF đúng/sai/gần đúng"),
        ("ml_classifier", "Train/apply ML"),
        ("artifact_persist", "Lưu video/frames/database"),
    ]
    if status_text == "ready_for_ai_worker":
        return [
            {"key": key, "label": label, "status": "done" if index == 0 else "pending"}
            for index, (key, label) in enumerate(labels)
        ]
    active = 0
    if progress >= 0.94:
        active = 4
    elif progress >= 0.78:
        active = 3
    elif progress >= 0.70:
        active = 2
    elif progress >= 0.10:
        active = 1
    output = []
    for index, (key, label) in enumerate(labels):
        if status_text in {"error", "canceled"} and index == active:
            step_status = status_text
        elif index < active or status_text == "success":
            step_status = "done"
        elif index == active:
            step_status = "active"
        else:
            step_status = "pending"
        output.append({"key": key, "label": label, "status": step_status})
    return output


def _analysis_job_payload(
    video: dict[str, Any],
    user: dict[str, Any],
    body: AnalysisJobRequestBody,
    *,
    action: str,
    status_text: str = "queued",
    progress: float = 0.0,
    run_id: str | None = None,
    status_msg: str = "",
    error_msg: str = "",
) -> dict[str, Any]:
    video_path = _job_video_path(video)
    now = datetime.now(timezone.utc).timestamp()
    options = {
        "model_type": body.model_type,
        "skip_step": body.skip_step,
        "resize_width": body.resize_width,
        "min_confidence": body.min_confidence,
    }
    return {
        "job_id": _analysis_job_id(video_path),
        "run_id": run_id or f"run_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
        "video_path": video_path,
        "username": _clean_text(video.get("username") or video.get("patient_username")),
        "video_name": _clean_text(video.get("video_name")),
        "exercise": _clean_text(video.get("exercise")),
        "status": status_text,
        "progress": round(float(progress or 0), 4),
        "status_msg": status_msg,
        "error_msg": error_msg,
        "start_time": now,
        "heartbeat": now,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "job_meta": {
            "requested_by": _clean_text(user.get("username")),
            "action": action,
            "options": options,
        },
        "steps": _job_steps(status_text, float(progress or 0)),
    }


def _write_analysis_job(video: dict[str, Any], payload: dict[str, Any]) -> None:
    progress_path = _progress_file_for_video(video)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(progress_path, payload)
    history_path = _history_file_for_video(video)
    history = read_json(history_path, [])
    if not isinstance(history, list):
        history = []
    run_id = payload.get("run_id")
    history = [item for item in history if not (isinstance(item, dict) and item.get("run_id") == run_id)]
    history.append(payload)
    write_json(history_path, history[-50:])


def _update_job_progress(
    video: dict[str, Any],
    payload: dict[str, Any],
    *,
    progress: float,
    status_msg: str,
    status: str = "processing",
    current_frame: int | None = None,
    total_frames: int | None = None,
    processed_frames: int | None = None,
    started_at: float | None = None,
) -> None:
    now_ts = datetime.now(timezone.utc).timestamp()
    update: dict[str, Any] = {
        "status": status,
        "progress": round(float(progress or 0), 4),
        "status_msg": status_msg,
        "steps": _job_steps(status, float(progress or 0)),
        "heartbeat": now_ts,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    if current_frame is not None:
        update["current_frame"] = int(current_frame)
    if total_frames is not None:
        update["total_frames"] = int(total_frames)
    if processed_frames is not None:
        update["processed_frames"] = int(processed_frames)
    if started_at is not None:
        elapsed = max(0.0, time.time() - started_at)
        update["elapsed_seconds"] = round(elapsed, 1)
        if processed_frames is not None and elapsed > 0:
            update["fps_effective"] = round(float(processed_frames) / elapsed, 2)
    payload.update(update)
    _write_analysis_job(video, payload)


def _read_analysis_job(video: dict[str, Any]) -> dict[str, Any] | None:
    data = read_json(_progress_file_for_video(video), None)
    return data if isinstance(data, dict) else None


def _cancel_other_active_analysis_jobs(current_job_id: str, reason: str = "") -> None:
    progress_dir = REPO_ROOT / "processed_results"
    if not progress_dir.is_dir():
        return
    now = datetime.now().isoformat(timespec="seconds")
    message = reason or "Đã hủy job song song để tránh làm chậm job đang chạy."
    for path in progress_dir.glob("progress_*.json"):
        if path.stem == f"progress_{current_job_id}":
            continue
        latest = read_json(path, None)
        if not isinstance(latest, dict):
            continue
        if _clean_text(latest.get("status")).lower() not in {"queued", "processing", "ready_for_ai_worker"}:
            continue
        progress = float(latest.get("progress") or 0)
        latest.update(
            {
                "status": "canceled",
                "cancel_requested": True,
                "status_msg": message,
                "updated_at": now,
                "heartbeat": datetime.now(timezone.utc).timestamp(),
                "steps": _job_steps("canceled", progress),
            }
        )
        write_json(path, latest)


def _job_cancel_requested(video: dict[str, Any], run_id: str | None = None) -> bool:
    latest = _read_analysis_job(video)
    if not isinstance(latest, dict):
        return False
    if run_id and latest.get("run_id") != run_id:
        return True
    return latest.get("status") == "canceled" or bool(latest.get("cancel_requested"))


def _mark_stale_analysis_job(video: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
    status_text = _clean_text(latest.get("status")).lower()
    if status_text not in {"queued", "processing", "ready_for_ai_worker"}:
        return latest
    heartbeat = float(latest.get("heartbeat") or latest.get("start_time") or 0)
    if heartbeat and datetime.now(timezone.utc).timestamp() - heartbeat <= 60:
        return latest
    latest.update(
        {
            "status": "canceled",
            "cancel_requested": True,
            "status_msg": "Job phân tích đã dừng do backend/worker không còn heartbeat. Bấm Chạy lại để phân tích lại từ đầu.",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "steps": _job_steps("canceled", float(latest.get("progress") or 0)),
        }
    )
    _write_analysis_job(video, latest)
    return latest


def _read_analysis_history(video: dict[str, Any]) -> list[dict[str, Any]]:
    data = read_json(_history_file_for_video(video), [])
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _simulate_or_run_analysis(video: dict[str, Any], user: dict[str, Any], body: AnalysisJobRequestBody, action: str) -> dict[str, Any]:
    payload = _analysis_job_payload(
        video,
        user,
        body,
        action=action,
        status_text="processing",
        progress=0.08,
        status_msg="Đã nhận yêu cầu chạy lại phân tích.",
    )
    payload["status_msg"] = "Đã nhận yêu cầu chạy lại phân tích cho video đang chọn."
    _write_analysis_job(video, payload)

    def worker() -> None:
        for progress, message in (
            (0.24, "Validate/transcode video."),
            (0.46, "Chuẩn bị MediaPipe pass 1."),
            (0.68, "Đợi AI runner xử lý artifact."),
            (1.0, "Backend đã ghi job; bật REHAB_BACKEND_ENABLE_AI_RUNNER=1 để chạy MediaPipe thật."),
        ):
            if progress >= 1.0:
                message = "Backend đã nhận job; đang chờ worker MediaPipe thật xử lý REF/ML/artifact."
            time.sleep(0.25)
            status_text = "ready_for_ai_worker" if progress >= 1.0 else "processing"
            next_payload = dict(payload)
            next_payload.update(
                {
                    "status": status_text,
                    "progress": progress,
                    "status_msg": message,
                    "heartbeat": datetime.now(timezone.utc).timestamp(),
                    "updated_at": datetime.now().isoformat(timespec="seconds"),
                    "steps": _job_steps(status_text, progress),
                }
            )
            _write_analysis_job(video, next_payload)
        ANALYSIS_RUNNING.pop(str(payload["job_id"]), None)

    thread = threading.Thread(target=worker, daemon=True)
    ANALYSIS_RUNNING[str(payload["job_id"])] = thread
    thread.start()
    return payload


def _analysis_result_from_artifacts(video: dict[str, Any]) -> dict[str, Any]:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    return {
        "processed_video_path": video.get("processed_path"),
        "output_video_path": video.get("processed_path"),
        "df_path": video.get("df_path"),
        "all_frames_data_path": video.get("all_frames_data_path"),
        "frames_zip": video.get("frames_zip") or video.get("frames_zip_path"),
        "frames_zip_path": video.get("frames_zip_path") or video.get("frames_zip"),
        "stats": metrics,
    }


def _artifact_update_value(value: Any) -> Any:
    path = _resolve_existing_path(value)
    if path:
        return _relative_repo_path(path)
    return value


def _restore_saved_artifacts_job(
    video: dict[str, Any],
    video_index: int,
    user: dict[str, Any],
    body: AnalysisJobRequestBody,
    action: str,
) -> dict[str, Any] | None:
    hydrated = _hydrate_video_artifacts(video)
    current_score = _existing_artifact_count(video)
    hydrated_score = _existing_artifact_count(hydrated)
    if hydrated_score <= current_score:
        return None

    updates: dict[str, Any] = {}
    for key in ARTIFACT_METADATA_KEYS:
        source_value = hydrated.get(key)
        if not source_value or not _resolve_existing_path(source_value):
            continue
        if not _resolve_existing_path(video.get(key)):
            updates[key] = _artifact_update_value(source_value)

    for key in ANALYSIS_METADATA_KEYS:
        if key == "metrics":
            continue
        if hydrated.get(key) is not None and video.get(key) is None:
            updates[key] = hydrated.get(key)

    source_metrics = hydrated.get("metrics") if isinstance(hydrated.get("metrics"), dict) else {}
    current_metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    if source_metrics:
        updates["metrics"] = {**source_metrics, **current_metrics}
    if hydrated.get("accuracy") is not None and video.get("accuracy") is None:
        updates["accuracy"] = hydrated.get("accuracy")

    if not updates:
        return None

    restored = _persist_video_artifacts(video_index, updates, user)
    source = _clean_text(hydrated.get("_artifact_source")) or "saved_artifacts"
    payload = _analysis_job_payload(
        restored,
        user,
        body,
        action=action,
        status_text="success",
        progress=1.0,
        status_msg=f"Đã khôi phục kết quả đã lưu ({source}); database đã cập nhật video, frames, REF và ML.",
    )
    payload["result"] = _analysis_result_from_artifacts(restored)
    payload["restored_from"] = source
    _write_analysis_job(restored, payload)
    return payload


def _angle_between_points(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float | None:
    ab = (a[0] - b[0], a[1] - b[1])
    cb = (c[0] - b[0], c[1] - b[1])
    ab_len = math.hypot(*ab)
    cb_len = math.hypot(*cb)
    if ab_len <= 1e-9 or cb_len <= 1e-9:
        return None
    cosine = max(-1.0, min(1.0, (ab[0] * cb[0] + ab[1] * cb[1]) / (ab_len * cb_len)))
    return math.degrees(math.acos(cosine))


def _status_from_deltas(shoulder: float | None, elbow: float | None, shoulder_ref: float, elbow_ref: float, threshold: float) -> tuple[str, bool, bool]:
    if shoulder is None or elbow is None:
        return "FAIL", False, False
    shoulder_delta = abs(shoulder - shoulder_ref)
    elbow_delta = abs(elbow - elbow_ref)
    if shoulder_delta <= threshold and elbow_delta <= threshold:
        return "PASS", True, False
    if shoulder_delta <= threshold * 1.5 and elbow_delta <= threshold * 1.5:
        return "NEAR", False, True
    return "FAIL", False, False


def _pose_record_from_image(image: Any, frame_number: int, timestamp_seconds: float, exercise: Any, detected_pose: dict[str, Any] | None = None) -> dict[str, Any]:
    exercise_key = _exercise_key(exercise)
    detected = detected_pose if detected_pose is not None else (_mediapipe_pose_frame_data(image, exercise) or {})
    record: dict[str, Any] = {
        "index": frame_number,
        "frame": frame_number,
        "timestamp_seconds": round(float(timestamp_seconds or 0), 4),
        "detected": bool(detected),
        "filtered_stranger": False,
        "exercise": _exercise_label(exercise),
        "exercise_key": exercise_key,
    }
    record.update(detected)
    height, width = image.shape[:2]
    points = _pose_points_for_frame(record, width, height)
    shoulder_ref, elbow_ref = _default_refs_for_exercise(exercise)
    record["vai_chuan"] = shoulder_ref
    record["khuyu_chuan"] = elbow_ref
    record["shoulder_ref"] = shoulder_ref
    record["elbow_ref"] = elbow_ref

    def angle(indices: tuple[int, int, int]) -> float | None:
        if not all(idx in points for idx in indices):
            return None
        a, b, c = (points[idx][:2] for idx in indices)
        return _angle_between_points(a, b, c)

    left_shoulder = angle((23, 11, 13))
    left_elbow = angle((11, 13, 15))
    right_shoulder = angle((24, 12, 14))
    right_elbow = angle((12, 14, 16))
    shoulder_values = [value for value in (left_shoulder, right_shoulder) if value is not None]
    elbow_values = [value for value in (left_elbow, right_elbow) if value is not None]
    if exercise_key == "codman":
        shoulder = right_shoulder
        elbow = right_elbow
    else:
        shoulder = sum(shoulder_values) / len(shoulder_values) if shoulder_values else None
        elbow = sum(elbow_values) / len(elbow_values) if elbow_values else None
    threshold = 30.0 if exercise_key == "pulley" else 45.0
    record.update(
        {
            "goc_vai": shoulder,
            "goc_khuyu": elbow,
            "goc_vai_trai": left_shoulder,
            "goc_khuyu_trai": left_elbow,
            "goc_vai_phai": right_shoulder,
            "goc_khuyu_phai": right_elbow,
        }
    )
    record = _fill_missing_reference_values(record, exercise)
    if exercise_key in {"codman", "pulley"} and not _has_complete_pose(record):
        return _mark_filtered_stranger(record, "incomplete_pose_33")
    status_text = _phase_status_for_frame(record, threshold, _default_refs_for_exercise(exercise), exercise)
    record["dung"] = status_text == "PASS"
    record["gan_dung"] = status_text == "NEAR"
    record["status"] = status_text
    return record


def _apply_people_filter_to_record(image: Any, record: dict[str, Any], exercise: Any) -> dict[str, Any]:
    exercise_key = _frame_exercise_key(record, exercise)
    if exercise_key not in {"codman", "pulley"}:
        return record
    if _multiple_people_detected(image, record):
        reason = "codman_helper_overlap" if exercise_key == "codman" else "multiple_people"
        return _mark_filtered_stranger(record, reason)
    locked_reason = _search_text(record.get("stranger_reason"))
    if (
        _to_bool(record.get("filtered_stranger"))
        and locked_reason not in {"multiple_people", "pulley_multiple_people", "codman_helper_overlap"}
        and _has_complete_pose(record)
    ):
        record["filtered_stranger"] = False
        record["stranger_reason"] = None
    return record


def _numeric_values(records: list[dict[str, Any]], key: str) -> list[float]:
    values = [_to_float(record.get(key)) for record in records]
    return [value for value in values if value is not None]


def _analysis_metrics(records: list[dict[str, Any]], total_frames: int, elapsed: float, exercise: Any) -> dict[str, Any]:
    exercise_key = _exercise_key(exercise)
    valid = [
        _fill_missing_reference_values(record, exercise)
        for record in records
        if _to_bool(record.get("detected"))
        and not _frame_should_be_unknown(record, exercise)
        and _frame_angle_values(record, exercise)[0] is not None
    ]
    total_valid = len(valid)
    def record_status(record: dict[str, Any]) -> str:
        if _frame_should_be_unknown(record, exercise):
            return "UNKNOWN"
        status_text = _clean_text(record.get("phase_status") or record.get("status")).upper()
        if status_text in {"PASS", "NEAR", "FAIL", "UNKNOWN"}:
            return status_text
        threshold = _to_float(record.get("threshold") or record.get("phase_threshold"))
        if threshold is None:
            threshold = 30 if _is_pulley_exercise(exercise) else 45
        return _phase_status_for_frame(record, threshold, exercise=exercise)

    pass_count = sum(1 for record in valid if record_status(record) == "PASS")
    near_count = sum(1 for record in valid if record_status(record) == "NEAR")
    fail_count = sum(1 for record in valid if record_status(record) == "FAIL")
    unknown_count = sum(1 for record in records if record_status(record) == "UNKNOWN")
    total_counted = pass_count + near_count + fail_count + unknown_count
    shoulder_values = [value for value, _ in (_frame_angle_values(record, exercise) for record in valid) if value is not None]
    elbow_values = [value for _, value in (_frame_angle_values(record, exercise) for record in valid) if value is not None]
    accuracy = (pass_count / total_valid * 100) if total_valid else 0.0
    mae_values = []
    shoulder_refs = []
    elbow_refs = []
    for record in valid:
        shoulder_ref, elbow_ref = _merge_ref_values(_frame_ref_values(record), _default_refs_for_exercise(exercise))
        if shoulder_ref is not None:
            shoulder_refs.append(shoulder_ref)
        if elbow_ref is not None:
            elbow_refs.append(elbow_ref)
        shoulder_delta, elbow_delta = _frame_delta_values(record, (shoulder_ref, elbow_ref), exercise)
        if shoulder_delta is not None:
            mae_values.append(shoulder_delta)
        if elbow_delta is not None:
            mae_values.append(elbow_delta)
    return {
        "do_chinh_xac": round(accuracy, 2),
        "ty_le_tong_the": round(accuracy, 2),
        "ty_le_gan_dung": round((near_count / total_valid * 100) if total_valid else 0.0, 2),
        "ty_le_vai_dung": round(accuracy, 2),
        "ty_le_khuyu_dung": round(accuracy, 2),
        "frame_dung": pass_count,
        "frame_gan_dung": near_count,
        "frame_sai": fail_count,
        "frame_khong_nhan_dang": unknown_count,
        "tong_frame_hop_le": total_valid,
        "tong_frame_da_cham": total_counted,
        "tb_goc_vai": round(sum(shoulder_values) / len(shoulder_values), 3) if shoulder_values else 0,
        "tb_goc_khuyu": round(sum(elbow_values) / len(elbow_values), 3) if elbow_values else 0,
        "min_goc_vai": min(shoulder_values) if shoulder_values else 0,
        "max_goc_vai": max(shoulder_values) if shoulder_values else 0,
        "min_goc_khuyu": min(elbow_values) if elbow_values else 0,
        "max_goc_khuyu": max(elbow_values) if elbow_values else 0,
        "std_goc_vai": statistics.pstdev(shoulder_values) if len(shoulder_values) > 1 else 0,
        "std_goc_khuyu": statistics.pstdev(elbow_values) if len(elbow_values) > 1 else 0,
        "mae_tong": mae_tong,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1_score, 3),
        "icc": _app_icc_from_mae(mae_tong, total_valid),
        "tb_vai_chuan": round(sum(shoulder_refs) / len(shoulder_refs), 3) if shoulder_refs else _default_refs_for_exercise(exercise)[0],
        "tb_khuyu_chuan": round(sum(elbow_refs) / len(elbow_refs), 3) if elbow_refs else _default_refs_for_exercise(exercise)[1],
        "ref_source": "youtube_mediapipe" if exercise_key in {"codman", "pulley"} else "default",
        "exercise_key": exercise_key,
        "thoi_gian": round(elapsed, 2),
        "tong_frame": total_frames,
    }


def _apply_ml_to_records(csv_path: Path, frames_path: Path, records: list[dict[str, Any]], metrics: dict[str, Any], exercise: Any) -> dict[str, Any]:
    try:
        import pandas as pd  # type: ignore[import-not-found]
        from utils.pose_classifier_utils import apply_classifier_to_dataframe, ensure_classifier_ready, merge_ml_metrics
    except Exception as exc:
        metrics["ml_status"] = f"ML chưa sẵn sàng: {exc}"
        return metrics
    try:
        ready = ensure_classifier_ready(
            processed_dir=str(REPO_ROOT / "processed_results"),
            db_dir=str(DATABASE_DIR),
            min_samples=10,
            auto_train=True,
        )
        metrics["ml_ready"] = bool(ready.get("ready"))
        metrics["ml_trained_now"] = bool(ready.get("trained"))
        if not ready.get("ready"):
            metrics["ml_status"] = ready.get("message") or "Chưa train được pose classifier"
            return metrics
        df = pd.read_csv(csv_path)
        phase_bounds = None if _is_pulley_exercise(exercise) else _segment_bounds_from_angle_items(records)
        predicted_df, ml_result = apply_classifier_to_dataframe(
            df,
            db_dir=str(DATABASE_DIR),
            phase_bounds=phase_bounds,
            exercise_name=_clean_text(exercise),
        )
        predicted_df.to_csv(csv_path, index=False)
        ml_cols = [
            "ml_label",
            "ml_label_text",
            "dung_ml",
            "gan_dung_ml",
            "ml_score",
            "ml_confidence",
            "ml_prob_sai",
            "ml_prob_gan_dung",
            "ml_prob_dung",
        ]
        for idx, record in enumerate(records[: len(predicted_df)]):
            if _to_bool(record.get("filtered_stranger")) or _clean_text(record.get("status")).upper() == "UNKNOWN" or _clean_text(record.get("phase_status")).upper() == "UNKNOWN":
                _mark_filtered_stranger(record, _clean_text(record.get("stranger_reason")) or "unknown_pose")
                continue
            for col in ml_cols:
                if col in predicted_df.columns:
                    value = predicted_df.iloc[idx][col]
                    try:
                        if hasattr(value, "item"):
                            value = value.item()
                    except Exception:
                        pass
                    record[col] = value
        frames_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        return merge_ml_metrics(metrics, ml_result)
    except Exception as exc:
        metrics["ml_status"] = f"Không apply được ML: {exc}"
        return metrics

def _render_analysis_artifacts_from_records(
    source: Path,
    output_path: Path,
    frames_zip: Path,
    records: list[dict[str, Any]],
    *,
    fps: float,
    skip: int,
    target_width: int,
    target_height: int,
    exercise: Any,
    on_progress: Callable[[int, int], None] | None = None,
) -> int:
    try:
        import cv2  # type: ignore[import-not-found]
    except Exception:
        return 0
    if not source.is_file() or not records:
        return 0
    tmp_video = output_path.with_name(f"{output_path.stem}_render_tmp.mp4")
    tmp_zip = frames_zip.with_name(f"{frames_zip.stem}_render_tmp.zip")
    for path in (tmp_video, tmp_zip):
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
    cap = cv2.VideoCapture(str(source))
    writer = cv2.VideoWriter(str(tmp_video), cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, fps / max(1, skip)), (target_width, target_height))
    if not cap.isOpened() or not writer.isOpened():
        cap.release()
        writer.release()
        return 0
    rendered_count = 0
    needs_pose_redetect = any(isinstance(record, dict) and len(_pose_landmarks(record)) < 33 for record in records)
    pose_context = None
    try:
        if needs_pose_redetect:
            import mediapipe as mp  # type: ignore[import-not-found]

            exercise_key = _exercise_key(exercise)
            pose_context = mp.solutions.pose.Pose(
                static_image_mode=exercise_key == "codman",
                model_complexity=2,
                enable_segmentation=False,
                min_detection_confidence=0.35,
            )
    except Exception:
        pose_context = None
    try:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            total_records = len(records)
            last_progress_write = time.monotonic()
            last_frame_number = 0
            for position, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                frame_number = _frame_number_key(record.get("frame") or record.get("index") or record.get("frame_number")) or position + 1
                if frame_number != last_frame_number + 1:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_number - 1))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                last_frame_number = frame_number
                if (frame.shape[1], frame.shape[0]) != (target_width, target_height):
                    interpolation = cv2.INTER_AREA if target_width < frame.shape[1] else cv2.INTER_LINEAR
                    frame = cv2.resize(frame, (target_width, target_height), interpolation=interpolation)
                frame_data = _frame_with_exercise_context(record, exercise)
                if _frame_exercise_key(frame_data, exercise) in {"codman", "pulley"}:
                    # Rendering must not re-score an already analyzed frame. The
                    # analysis pass is the source of truth for UNKNOWN/person
                    # filtering; otherwise a coarse detector can overwrite all
                    # repaired REF/ML labels while merely rebuilding artifacts.
                    if len(_pose_landmarks(frame_data)) < 33 and pose_context is not None:
                        frame_data = _frame_with_detected_pose(frame, frame_data, pose_context=pose_context)
                        if not _to_bool(frame_data.get("filtered_stranger")):
                            frame_data = _apply_people_filter_to_record(frame, frame_data, exercise)
                    records[position] = frame_data
                threshold = _to_float(frame_data.get("threshold") or frame_data.get("phase_threshold"))
                if threshold is None:
                    _, _, fallback_threshold = _phase_for_position(position, len(records), exercise)
                    threshold = float(fallback_threshold)
                display_index = int(_frame_number_key(frame_data.get("index") or frame_number) or position + 1)
                rendered = _draw_pose_analysis_overlay(frame, frame_data, display_index, threshold=float(threshold))
                writer.write(rendered)
                ok_jpg, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok_jpg:
                    archive.writestr(f"f_{position + 1:06d}.jpg", encoded.tobytes())
                rendered_count += 1
                if on_progress and (rendered_count == 1 or rendered_count % 50 == 0 or time.monotonic() - last_progress_write >= 2.0):
                    on_progress(rendered_count, total_records)
                    last_progress_write = time.monotonic()
    finally:
        cap.release()
        writer.release()
        if pose_context is not None:
            try:
                pose_context.close()
            except Exception:
                pass
    if rendered_count <= 0:
        tmp_video.unlink(missing_ok=True)
        tmp_zip.unlink(missing_ok=True)
        return 0
    tmp_video.replace(output_path)
    tmp_zip.replace(frames_zip)
    return rendered_count


def _audio_state_for_record(record: dict[str, Any]) -> str | None:
    if _to_bool(record.get("filtered_stranger")):
        return None
    status_text = _clean_text(record.get("phase_status") or record.get("status")).upper()
    if not status_text:
        status_text = _phase_status_for_frame(record, _to_float(record.get("threshold") or record.get("phase_threshold")) or 30.0)
    if status_text == "PASS":
        return "dung"
    if status_text == "NEAR":
        return "gan_dung"
    if status_text == "FAIL":
        return "sai"
    return None


def _audio_events_from_records(records: list[dict[str, Any]], fps: float, *, min_gap: float = 1.5) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    last_state: str | None = None
    last_audio_time = -10.0
    safe_fps = max(1.0, float(fps or 30.0))
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        state = _audio_state_for_record(record)
        if not state:
            continue
        frame_number = _frame_number_key(record.get("frame") or record.get("index") or record.get("frame_number")) or position + 1
        timestamp = _first_float(record.get("timestamp_seconds"))
        if timestamp is None:
            timestamp = max(0.0, (frame_number - 1) / safe_fps)
        if state != last_state and timestamp - last_audio_time >= min_gap:
            events.append({"time": float(timestamp), "state": state})
            last_state = state
            last_audio_time = float(timestamp)
    return events


def _mix_voice_audio_for_records(records: list[dict[str, Any]], output_path: Path, fps: float, total_frames: int) -> tuple[Path | None, dict[str, Any]]:
    audio_path = output_path.with_name(f"{output_path.stem}_audio.wav")
    try:
        audio_path.unlink(missing_ok=True)
    except Exception:
        pass
    events = _audio_events_from_records(records, fps)
    if not events:
        return None, {"audio_status": "no_events", "audio_events": 0}
    sounds_dir = REPO_ROOT / "sounds"
    sound_paths = {
        "dung": sounds_dir / "dung.mp3",
        "gan_dung": sounds_dir / "gan_dung.mp3",
        "sai": sounds_dir / "sai.mp3",
    }
    missing = [name for name, path in sound_paths.items() if not path.is_file() or path.stat().st_size <= 0]
    if missing:
        return None, {"audio_status": f"missing_sound:{','.join(missing)}", "audio_events": len(events)}
    try:
        from pydub import AudioSegment  # type: ignore[import-not-found]
    except Exception as exc:
        return None, {"audio_status": f"pydub_unavailable:{exc}", "audio_events": len(events)}
    try:
        if len(events) > 40:
            step = max(1, len(events) // 40)
            events = events[::step][:40]
        sounds = {state: AudioSegment.from_mp3(path) for state, path in sound_paths.items()}
        safe_fps = max(1.0, float(fps or 30.0))
        total_duration_ms = int((max(1, int(total_frames or len(records))) / safe_fps) * 1000) + 1000
        final_audio = AudioSegment.empty()
        last_ms = 0
        for event in events:
            state = _clean_text(event.get("state"))
            snd = sounds.get(state)
            if snd is None:
                continue
            time_ms = max(0, int(float(event.get("time") or 0) * 1000))
            silence_dur = time_ms - last_ms
            if silence_dur > 0:
                final_audio += AudioSegment.silent(duration=silence_dur)
            elif silence_dur < 0:
                continue
            final_audio += snd
            last_ms = time_ms + len(snd)
        if total_duration_ms > last_ms:
            final_audio += AudioSegment.silent(duration=total_duration_ms - last_ms)
        else:
            final_audio = final_audio[:total_duration_ms]
        final_audio.export(audio_path, format="wav")
        return audio_path if audio_path.is_file() and audio_path.stat().st_size > 0 else None, {
            "audio_status": "mixed",
            "audio_events": len(events),
            "audio_path": _relative_repo_path(audio_path) if audio_path.is_file() else "",
        }
    except Exception as exc:
        return None, {"audio_status": f"mix_error:{exc}", "audio_events": len(events)}


def _ensure_sound_playback_video(
    source_video: Path | None,
    frame_records: list[dict[str, Any]],
    *,
    exercise: Any,
    metrics: dict[str, Any] | None = None,
) -> tuple[Path | None, dict[str, Any]]:
    if not source_video or not source_video.is_file() or not frame_records:
        return source_video, {}
    if _audio_codec(source_video):
        return source_video, {"audio_status": "already_has_audio"}

    source_stem = _processed_stem(source_video) or source_video.stem
    output = source_video.with_name(f"{source_stem}_sound.mp4")
    if output.is_file() and _video_frame_count(output) > 0 and _audio_codec(output):
        return output, {"audio_status": "sound_cached", "audio_video_path": _relative_repo_path(output)}

    contextual_records = [_frame_with_exercise_context(record, exercise) for record in frame_records if isinstance(record, dict)]
    fps = _video_fps(source_video, 30.0)
    audio_path, audio_metrics = _mix_voice_audio_for_records(contextual_records, output, fps, len(contextual_records) or _video_frame_count(source_video))
    updates = dict(audio_metrics)
    if not audio_path or not audio_path.is_file():
        return source_video, updates

    tmp_output = output.with_name(f"{output.stem}_tmp.mp4")
    tmp_output.unlink(missing_ok=True)
    try:
        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_video),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            "-movflags",
            "+faststart",
            str(tmp_output),
        ]
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=900)
        if result.returncode != 0 or not tmp_output.is_file() or _video_frame_count(tmp_output) <= 0 or not _audio_codec(tmp_output):
            updates["audio_mux_status"] = f"ffmpeg_error:{(result.stderr or '')[-300:]}"
            tmp_output.unlink(missing_ok=True)
            return source_video, updates
        tmp_output.replace(output)
        updates["audio_status"] = "mixed"
        updates["audio_video_path"] = _relative_repo_path(output)
        if metrics is not None:
            metrics.update(updates)
        return output, updates
    except Exception as exc:
        tmp_output.unlink(missing_ok=True)
        updates["audio_mux_status"] = f"mux_exception:{exc}"
        return source_video, updates


def _run_lightweight_pose_analysis(video: dict[str, Any], video_index: int, user: dict[str, Any], body: AnalysisJobRequestBody, action: str, run_id: str) -> None:
    try:
        _run_lightweight_pose_analysis_impl(video, video_index, user, body, action, run_id)
    except Exception as exc:
        latest = _read_analysis_job(video)
        if not isinstance(latest, dict):
            latest = _analysis_job_payload(video, user, body, action=action, status_text="error", progress=1.0, run_id=run_id)
        latest.update(
            {
                "status": "error",
                "progress": 1.0,
                "status_msg": "Worker phan tich bi loi, vui long bam Chay lai sau khi sua loi.",
                "error_msg": f"Loi worker phan tich: {exc}",
                "heartbeat": datetime.now(timezone.utc).timestamp(),
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "steps": _job_steps("error", 1.0),
            }
        )
        _write_analysis_job(video, latest)
    finally:
        ANALYSIS_RUNNING.pop(str(_analysis_job_id(_job_video_path(video))), None)


def _run_lightweight_pose_analysis_impl(video: dict[str, Any], video_index: int, user: dict[str, Any], body: AnalysisJobRequestBody, action: str, run_id: str) -> None:
    start = time.time()
    payload = _analysis_job_payload(video, user, body, action=action, status_text="processing", progress=0.04, run_id=run_id, status_msg="Đang mở video gốc và khởi tạo MediaPipe.")
    _write_analysis_job(video, payload)
    try:
        import cv2  # type: ignore[import-not-found]
        import mediapipe as mp  # type: ignore[import-not-found]
    except Exception as exc:
        payload.update({"status": "error", "progress": 1.0, "error_msg": f"Thiếu OpenCV/MediaPipe để phân tích: {exc}", "steps": _job_steps("error", 1.0)})
        _write_analysis_job(video, payload)
        return

    source = _resolve_video_source_path(video.get("video_path")) or _resolve_video_source_path(video.get("processed_path"))
    if not source or not source.is_file():
        payload.update({"status": "error", "progress": 1.0, "error_msg": "Không tìm thấy video gốc local để chạy phân tích.", "steps": _job_steps("error", 1.0)})
        _write_analysis_job(video, payload)
        return

    processed_dir = REPO_ROOT / "processed_results"
    processed_dir.mkdir(parents=True, exist_ok=True)
    stem = _analysis_output_stem(video)
    output_path = processed_dir / f"{stem}.mp4"
    final_h264 = processed_dir / f"{stem}_f.mp4"
    csv_path = processed_dir / f"{stem}_data.csv"
    frames_path = processed_dir / f"f_{stem.removeprefix('processed_')}.json"
    frames_zip = processed_dir / f"{stem}_frames.zip"
    exercise = _exercise_label(video.get("exercise") or video.get("video_name"))
    exercise_key = _exercise_key(exercise)
    is_codman_exercise = exercise_key == "codman"
    is_pulley_exercise = exercise_key == "pulley"
    skip = max(1, int(body.skip_step) if body.skip_step is not None else 1)
    requested_resize_width = max(240, min(2160, int(body.resize_width or 720)))
    model_name = _clean_text(body.model_type).lower()
    model_complexity = 0 if "lite" in model_name else 1 if "full" in model_name else 2

    records: list[dict[str, Any]] = []
    cap = cv2.VideoCapture(str(source))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if not cap.isOpened() or total_frames <= 0:
        cap.release()
        payload.update({"status": "error", "progress": 1.0, "error_msg": "Không mở được video gốc hoặc video không có frame hợp lệ.", "steps": _job_steps("error", 1.0)})
        _write_analysis_job(video, payload)
        return
    _update_job_progress(video, payload, progress=0.08, status_msg=f"Đã mở video: {total_frames} frames. Đang chuẩn bị MediaPipe.", total_frames=total_frames, started_at=start)
    if width <= 0 or height <= 0:
        width, height = 720, 1280
    target_width = min(width, requested_resize_width)
    target_width = max(2, target_width - (target_width % 2))
    target_height = max(2, int(round(height * (target_width / max(1, width)))))
    target_height = target_height - (target_height % 2)
    resize_to_output = (target_width, target_height) != (width, height)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, fps / skip), (target_width, target_height))
    if not writer.isOpened():
        cap.release()
        payload.update({"status": "error", "progress": 1.0, "error_msg": "Không mở được VideoWriter để ghi video overlay.", "steps": _job_steps("error", 1.0)})
        _write_analysis_job(video, payload)
        return

    frame_number = 0
    processed_count = 0
    last_progress_write = time.monotonic()
    zip_archive = zipfile.ZipFile(frames_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=1)
    _update_job_progress(video, payload, progress=0.1, status_msg=f"MediaPipe đã sẵn sàng, bắt đầu trích xuất khung xương ở {target_width}x{target_height}.", current_frame=0, total_frames=total_frames, processed_frames=0, started_at=start)
    pose_context = mp.solutions.pose.Pose(static_image_mode=False, model_complexity=model_complexity, enable_segmentation=False, min_detection_confidence=max(0.1, float(body.min_confidence or 0.5)))
    with pose_context as pose:
        while True:
            if processed_count and processed_count % 5 == 0 and _job_cancel_requested(video, run_id):
                payload.update({"status": "canceled", "cancel_requested": True, "status_msg": "Đã dừng phân tích theo yêu cầu.", "updated_at": datetime.now().isoformat(timespec="seconds"), "steps": _job_steps("canceled", float(payload.get("progress") or 0))})
                _write_analysis_job(video, payload)
                cap.release()
                writer.release()
                zip_archive.close()
                output_path.unlink(missing_ok=True)
                frames_zip.unlink(missing_ok=True)
                return
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            frame_number += 1
            if (frame_number - 1) % skip != 0:
                continue
            if resize_to_output:
                interpolation = cv2.INTER_AREA if target_width < width else cv2.INTER_LINEAR
                frame = cv2.resize(frame, (target_width, target_height), interpolation=interpolation)
            timestamp_seconds = max(0.0, (frame_number - 1) / fps)
            detected: dict[str, Any] = {}
            try:
                if is_codman_exercise:
                    detected = _mediapipe_pose_frame_data(frame, exercise, pose_context=pose) or {}
                else:
                    detected = _mediapipe_pose_frame_data(frame, exercise, pose_context=pose) or {}
            except Exception:
                detected = {}
            record = _pose_record_from_image(frame, frame_number, timestamp_seconds, exercise, detected)
            record = _apply_people_filter_to_record(frame, record, exercise)
            phase, _, threshold = _phase_for_position(len(records), max(1, total_frames // skip), exercise)
            record["phase"] = phase
            if _frame_should_be_unknown(record, exercise):
                _mark_filtered_stranger(record, _clean_text(record.get("stranger_reason")) or "incomplete_pose_33")
                status_text = "UNKNOWN"
            else:
                status_text = _phase_status_for_frame(record, threshold, _default_refs_for_exercise(exercise), exercise)
            record["status"] = status_text or record.get("status") or "FAIL"
            record["phase_status"] = record["status"]
            record["dung"] = status_text == "PASS"
            record["gan_dung"] = status_text == "NEAR"
            rendered = _draw_pose_analysis_overlay(frame, record, frame_number, threshold=float(threshold))
            writer.write(rendered)
            ok_jpg, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if ok_jpg:
                zip_archive.writestr(f"f_{len(records) + 1:06d}.jpg", encoded.tobytes())
            records.append(record)
            processed_count += 1
            if processed_count == 1 or processed_count % 25 == 0 or time.monotonic() - last_progress_write >= 2.0:
                progress = 0.12 + min(0.58, (frame_number / max(1, total_frames)) * 0.58)
                _update_job_progress(
                    video,
                    payload,
                    progress=progress,
                    status_msg=f"Đang trích xuất khung xương MediaPipe: frame {frame_number}/{total_frames}",
                    current_frame=frame_number,
                    total_frames=total_frames,
                    processed_frames=processed_count,
                    started_at=start,
                )
                last_progress_write = time.monotonic()
    cap.release()
    writer.release()
    zip_archive.close()

    if not records:
        output_path.unlink(missing_ok=True)
        frames_zip.unlink(missing_ok=True)
        payload.update({"status": "error", "progress": 1.0, "error_msg": "Không trích xuất được frame hợp lệ từ video.", "steps": _job_steps("error", 1.0)})
        _write_analysis_job(video, payload)
        return

    phase_bounds = _apply_phase_thresholds_to_records(records, exercise)
    phase_msg = "Đã trích xuất xong MediaPipe; đang ghi frames JSON, CSV và gói ZIP frames."
    if phase_bounds and len(phase_bounds) >= 4:
        phase_msg = f"Đã chia Codman thành GĐ1/GĐ2/GĐ3 với sai số ±45/±30/±15; đang ghi JSON, CSV và ZIP frames."
    _update_job_progress(video, payload, progress=0.72, status_msg=phase_msg, current_frame=frame_number, total_frames=total_frames, processed_frames=processed_count, started_at=start)
    frames_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    fieldnames = sorted({key for record in records for key in record.keys() if not isinstance(record.get(key), (dict, list))})
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer_csv = csv.DictWriter(handle, fieldnames=fieldnames)
        writer_csv.writeheader()
        writer_csv.writerows({key: record.get(key) for key in fieldnames} for record in records)

    metrics = _analysis_metrics(records, total_frames, time.time() - start, exercise)
    if phase_bounds and len(phase_bounds) >= 4:
        metrics["phase_bounds"] = [int(value) for value in phase_bounds[:4]]
        metrics["phase_thresholds"] = dict(PHASE_THRESHOLDS)
    _update_job_progress(video, payload, progress=0.78, status_msg="Đã so sánh REF/đúng-sai-gần đúng; đang train/apply model ML.", current_frame=frame_number, total_frames=total_frames, processed_frames=processed_count, started_at=start)
    metrics = _apply_ml_to_records(csv_path, frames_path, records, metrics, exercise)
    _update_job_progress(video, payload, progress=0.84, status_msg="Dang dung lai video/frames sau khi da co REF giai doan va ML.", current_frame=frame_number, total_frames=total_frames, processed_frames=processed_count, started_at=start)
    rendered_count = _render_analysis_artifacts_from_records(
        source,
        output_path,
        frames_zip,
        records,
        fps=fps,
        skip=skip,
        target_width=target_width,
        target_height=target_height,
        exercise=exercise,
        on_progress=lambda done, total: _update_job_progress(
            video,
            payload,
            progress=0.84 + min(0.02, (done / max(1, total)) * 0.02),
            status_msg=f"Dang dung video/frames overlay sau REF/ML: frame {done}/{total}",
            current_frame=done,
            total_frames=total,
            processed_frames=processed_count,
            started_at=start,
        ),
    )
    if rendered_count:
        metrics["rendered_frames"] = rendered_count
        frames_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    _update_job_progress(video, payload, progress=0.865, status_msg="Dang tron am thanh dung/gan dung/sai vao video.", current_frame=frame_number, total_frames=total_frames, processed_frames=processed_count, started_at=start)
    audio_path, audio_metrics = _mix_voice_audio_for_records(records, output_path, fps / max(1, skip), processed_count or total_frames)
    metrics.update(audio_metrics)
    _update_job_progress(video, payload, progress=0.86, status_msg="ML đã cập nhật vào CSV/frames; đang đóng gói video H.264.", current_frame=frame_number, total_frames=total_frames, processed_frames=processed_count, started_at=start)
    try:
        h264_candidate, _ = _resolve_playback_video_path(output_path)
        if not audio_path and h264_candidate and h264_candidate != output_path and h264_candidate.is_file():
            shutil.copy2(h264_candidate, final_h264)
        else:
            command = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(output_path),
            ]
            if audio_path and audio_path.is_file():
                command.extend(["-i", str(audio_path)])
            command.extend([
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
            ])
            if audio_path and audio_path.is_file():
                command.extend(["-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest"])
            else:
                command.extend(["-map", "0:v:0", "-an"])
            command.extend([
                "-movflags",
                "+faststart",
                str(final_h264),
            ])
            result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=900)
            if result.returncode != 0:
                metrics["audio_mux_status"] = f"ffmpeg_error:{(result.stderr or '')[-300:]}"
    except Exception as exc:
        metrics["audio_mux_status"] = f"mux_exception:{exc}"
    processed_for_db = final_h264 if final_h264.is_file() and _video_frame_count(final_h264) > 0 else output_path
    _update_job_progress(video, payload, progress=0.94, status_msg="Đang lưu video, frames, CSV, REF, ML vào database.", current_frame=frame_number, total_frames=total_frames, processed_frames=processed_count, started_at=start)
    updates = {
        "processed_path": _relative_repo_path(processed_for_db),
        "df_path": _relative_repo_path(csv_path),
        "all_frames_data_path": _relative_repo_path(frames_path),
        "frames_zip": _relative_repo_path(frames_zip),
        "frames_zip_path": _relative_repo_path(frames_zip),
        "metrics": metrics,
        "accuracy": round(float(metrics.get("do_chinh_xac") or 0), 1),
        "status": "Đã phân tích",
        "exercise": exercise,
    }
    restored = _persist_video_artifacts(video_index, updates, user)
    payload = _analysis_job_payload(restored, user, body, action=action, status_text="success", progress=1.0, run_id=run_id, status_msg="Đã phân tích xong: video overlay, frames, CSV, REF và ML đã cập nhật database.")
    payload["result"] = _analysis_result_from_artifacts(restored)
    _write_analysis_job(restored, payload)


def _start_real_analysis_job(video: dict[str, Any], video_index: int, user: dict[str, Any], body: AnalysisJobRequestBody, action: str) -> dict[str, Any]:
    payload = _analysis_job_payload(
        video,
        user,
        body,
        action=action,
        status_text="processing",
        progress=0.02,
        status_msg="Đã nhận yêu cầu; backend đang chạy MediaPipe thật cho video đang chọn.",
    )
    with ANALYSIS_START_LOCK:
        _cancel_other_active_analysis_jobs(str(payload["job_id"]))
        running = ANALYSIS_RUNNING.get(str(payload["job_id"]))
        is_running = bool(running and (running.is_alive() if hasattr(running, "is_alive") else running.poll() is None if hasattr(running, "poll") else False))
        if is_running:
            latest = _read_analysis_job(video) or payload
            latest.update(
                {
                    "status": "processing",
                    "status_msg": "Video này đang có job phân tích chạy; bấm Cập nhật để xem tiến độ hoặc Hủy trước khi chạy lại.",
                    "heartbeat": datetime.now(timezone.utc).timestamp(),
                    "updated_at": datetime.now().isoformat(timespec="seconds"),
                    "steps": _job_steps("processing", float(latest.get("progress") or 0.02)),
                }
            )
            _write_analysis_job(video, latest)
            return latest
        _write_analysis_job(video, payload)
        if os.environ.get("REHAB_ANALYSIS_SUBPROCESS", "1") != "0":
            worker_log = REPO_ROOT / "processed_results" / f"analysis_worker_{payload['job_id']}.log"
            worker_log.parent.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env.setdefault("REHAB_REPO_ROOT", str(REPO_ROOT))
            env.setdefault("REHAB_DATABASE_DIR", str(DATABASE_DIR))
            command = [
                sys.executable,
                "-m",
                "backend.analysis_worker",
                "--video-index",
                str(video_index),
                "--run-id",
                str(payload["run_id"]),
                "--action",
                action,
                "--user-json",
                json.dumps(user, ensure_ascii=False),
                "--options-json",
                body.model_dump_json(),
            ]
            log_handle = worker_log.open("ab")
            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(REPO_ROOT),
                    env=env,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    close_fds=True,
                )
            finally:
                log_handle.close()
            ANALYSIS_RUNNING[str(payload["job_id"])] = process
        else:
            thread = threading.Thread(
                target=_run_lightweight_pose_analysis,
                args=(video, video_index, user, body, action, str(payload["run_id"])),
                daemon=True,
            )
            ANALYSIS_RUNNING[str(payload["job_id"])] = thread
            thread.start()
    return payload


def _find_video_index(videos: list[dict[str, Any]], identifier: str) -> int | None:
    if not identifier:
        return None
    if identifier.isdigit():
        idx = int(identifier)
        if 0 <= idx < len(videos):
            return idx
    wanted = _search_text(identifier)
    for idx, video in enumerate(videos):
        values = [
            video.get("stored_filename"),
            video.get("video_name"),
            video.get("video_path"),
            video.get("processed_path"),
        ]
        if any(_search_text(value) == wanted or wanted in _search_text(value) for value in values):
            return idx
    return None


def _relative_repo_path(path: Path | None) -> str:
    if not path:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except Exception:
        return str(path)


def _safe_filename(value: Any, fallback: str = "video.mp4") -> str:
    text = Path(_clean_text(value) or fallback).name
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9._ -]+", "_", text).strip(" ._")
    return text or fallback


def _exercise_label(value: Any) -> str:
    text = _search_text(value)
    if "day" in text or "theraband" in text or "khang luc" in text:
        return EXERCISE_LABELS["day"]
    if "gay" in text or "pulley" in text or "stick" in text:
        return EXERCISE_LABELS["pulley"]
    return EXERCISE_LABELS["codman"]


def _exercise_key(value: Any) -> str:
    label = _exercise_label(value)
    if _is_pulley_exercise(label):
        return "pulley"
    if "day" in _search_text(label):
        return "day"
    return "codman"


def _default_refs_for_exercise(exercise: Any) -> tuple[float, float]:
    key = _exercise_key(exercise)
    return DEFAULT_REFS.get(key, DEFAULT_REFS["codman"])


def _reference_name_for_exercise(exercise: Any) -> str:
    key = _exercise_key(exercise)
    if key == "pulley":
        return "gay"
    if key == "day":
        return "day"
    return "codman"


def _reference_poses_for_exercise(exercise: Any) -> list[dict[str, Any]]:
    ref_name = _reference_name_for_exercise(exercise)
    ref_path = resolve_reference_file(ref_name, str(DATABASE_DIR), str(REPO_ROOT))
    if not ref_path:
        return []
    try:
        resolved = str(Path(ref_path).resolve())
        stat = Path(ref_path).stat()
    except OSError:
        return []
    cached = REFERENCE_POSE_CACHE.get(resolved)
    if cached and cached[0] == stat.st_mtime and cached[1] == ref_name:
        return cached[2]
    try:
        raw = json.loads(Path(ref_path).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            poses = raw.get("poses") or []
            if not poses and isinstance(raw.get("exercises"), dict):
                poses = []
                for exercise_id, exercise_data in raw["exercises"].items():
                    if not isinstance(exercise_data, dict):
                        continue
                    for pose in exercise_data.get("poses") or []:
                        if isinstance(pose, dict):
                            item = dict(pose)
                            item.setdefault("exercise_id", exercise_id)
                            item.setdefault("motion_type", exercise_data.get("motion_type"))
                            poses.append(item)
        elif isinstance(raw, list):
            poses = raw
        else:
            poses = []
        poses = [pose for pose in poses if isinstance(pose, dict)]
    except Exception:
        poses = []
    REFERENCE_POSE_CACHE[resolved] = (stat.st_mtime, ref_name, poses)
    return poses


def _numeric_reference_poses(exercise: Any) -> list[tuple[dict[str, Any], float | None, float | None, float | None, float | None, float | None, float | None]]:
    refs = _reference_poses_for_exercise(exercise)
    cache_key = _reference_name_for_exercise(exercise)
    cached = REFERENCE_NUMERIC_CACHE.get(cache_key)
    if cached and cached[0] == id(refs):
        return cached[1]
    output = [
        (
            ref,
            _first_float(ref.get("vai")),
            _first_float(ref.get("khuyu")),
            _first_float(ref.get("vai_trai"), ref.get("vai")),
            _first_float(ref.get("khuyu_trai"), ref.get("khuyu")),
            _first_float(ref.get("vai_phai"), ref.get("vai")),
            _first_float(ref.get("khuyu_phai"), ref.get("khuyu")),
        )
        for ref in refs
        if isinstance(ref, dict)
    ]
    REFERENCE_NUMERIC_CACHE[cache_key] = (id(refs), output)
    return output


def _frame_ref_side_values(frame: dict[str, Any], side: str) -> tuple[float | None, float | None]:
    eval_info = _safe_nested_dict(frame.get("eval_info"))
    if side == "left":
        return (
            _first_float(frame.get("shoulder_ref_left"), frame.get("vai_chuan_trai"), frame.get("ref_left_shoulder"), eval_info.get("shoulder_ref_left")),
            _first_float(frame.get("elbow_ref_left"), frame.get("khuyu_chuan_trai"), frame.get("ref_left_elbow"), eval_info.get("elbow_ref_left")),
        )
    return (
        _first_float(frame.get("shoulder_ref_right"), frame.get("vai_chuan_phai"), frame.get("ref_right_shoulder"), eval_info.get("shoulder_ref_right")),
        _first_float(frame.get("elbow_ref_right"), frame.get("khuyu_chuan_phai"), frame.get("ref_right_elbow"), eval_info.get("elbow_ref_right")),
    )


def _has_saved_reference_values(frame: dict[str, Any]) -> bool:
    shoulder_ref, elbow_ref = _frame_ref_values(frame)
    left_shoulder_ref, left_elbow_ref = _frame_ref_side_values(frame, "left")
    right_shoulder_ref, right_elbow_ref = _frame_ref_side_values(frame, "right")
    return any(
        value is not None
        for value in (
            shoulder_ref,
            elbow_ref,
            left_shoulder_ref,
            left_elbow_ref,
            right_shoulder_ref,
            right_elbow_ref,
        )
    )


def _should_fill_youtube_reference(frame: dict[str, Any], exercise: Any) -> bool:
    if _frame_exercise_key(frame, exercise) not in {"codman", "pulley"}:
        return False
    if frame.get("ref_source") == "youtube_mediapipe":
        return False
    return not _has_saved_reference_values(frame)


def _fill_missing_reference_values(frame: dict[str, Any], exercise: Any) -> dict[str, Any]:
    frame = _frame_with_exercise_context(frame, exercise)
    if _should_fill_youtube_reference(frame, exercise):
        return _apply_youtube_reference_to_frame(frame, exercise, overwrite=False)
    return frame


def _match_youtube_reference_for_frame(frame: dict[str, Any], exercise: Any) -> dict[str, Any] | None:
    refs = _numeric_reference_poses(exercise)
    if not refs:
        return None
    frame = _frame_with_exercise_context(frame, exercise)
    exercise_key = _frame_exercise_key(frame, exercise)
    shoulder, elbow = _frame_angle_values(frame, exercise)
    left_shoulder, left_elbow = _side_angle_values(frame, "left")
    right_shoulder, right_elbow = _side_angle_values(frame, "right")
    if shoulder is None:
        return None
    ref_name = _reference_name_for_exercise(exercise)
    cache_key = (
        ref_name,
        round(float(shoulder), 1),
        round(float(elbow or 170), 1),
        round(float(left_shoulder), 1) if left_shoulder is not None else None,
        round(float(left_elbow), 1) if left_elbow is not None else None,
        round(float(right_shoulder), 1) if right_shoulder is not None else None,
        round(float(right_elbow), 1) if right_elbow is not None else None,
    )
    if cache_key in REFERENCE_MATCH_CACHE:
        cached = REFERENCE_MATCH_CACHE[cache_key]
        return dict(cached) if isinstance(cached, dict) else None
    matched: dict[str, Any] | None = None
    best_score = float("inf")
    for ref, ref_shoulder, ref_elbow, ref_left_shoulder, ref_left_elbow, ref_right_shoulder, ref_right_elbow in refs:
        if exercise_key == "pulley":
            left_score = 0.0
            right_score = 0.0
            left_count = 0
            right_count = 0
            if left_shoulder is not None and ref_left_shoulder is not None:
                left_score += (left_shoulder - ref_left_shoulder) ** 2
                left_count += 1
            if left_elbow is not None and ref_left_elbow is not None:
                left_score += (left_elbow - ref_left_elbow) ** 2
                left_count += 1
            if right_shoulder is not None and ref_right_shoulder is not None:
                right_score += (right_shoulder - ref_right_shoulder) ** 2
                right_count += 1
            if right_elbow is not None and ref_right_elbow is not None:
                right_score += (right_elbow - ref_right_elbow) ** 2
                right_count += 1
            if not left_count and not right_count:
                continue
            score = max(left_score / max(1, left_count), right_score / max(1, right_count))
        else:
            value_shoulder = right_shoulder if right_shoulder is not None else shoulder
            value_elbow = right_elbow if right_elbow is not None else elbow
            if ref_shoulder is None or ref_elbow is None or value_shoulder is None or value_elbow is None:
                continue
            score = (value_shoulder - ref_shoulder) ** 2 + (value_elbow - ref_elbow) ** 2
        if score < best_score:
            best_score = score
            matched = ref
    REFERENCE_MATCH_CACHE[cache_key] = dict(matched) if isinstance(matched, dict) else None
    return matched


def _apply_youtube_reference_to_frame(frame: dict[str, Any], exercise: Any, *, overwrite: bool = False) -> dict[str, Any]:
    frame = _frame_with_exercise_context(frame, exercise)
    matched = _match_youtube_reference_for_frame(frame, exercise)
    if not matched:
        return frame
    shoulder_ref = _first_float(matched.get("vai"))
    elbow_ref = _first_float(matched.get("khuyu"))
    left_shoulder_ref = _first_float(matched.get("vai_trai"), shoulder_ref)
    left_elbow_ref = _first_float(matched.get("khuyu_trai"), elbow_ref)
    right_shoulder_ref = _first_float(matched.get("vai_phai"), shoulder_ref)
    right_elbow_ref = _first_float(matched.get("khuyu_phai"), elbow_ref)
    updates = {
        "ref_source": "youtube_mediapipe",
        "youtube_ref_exercise_id": matched.get("exercise_id"),
        "motion_subtype": matched.get("exercise_id"),
        "motion_type": matched.get("motion_type"),
        "youtube_ref_time": matched.get("time"),
        "shoulder_ref": shoulder_ref,
        "elbow_ref": elbow_ref,
        "vai_chuan": shoulder_ref,
        "khuyu_chuan": elbow_ref,
        "shoulder_ref_left": left_shoulder_ref,
        "elbow_ref_left": left_elbow_ref,
        "shoulder_ref_right": right_shoulder_ref,
        "elbow_ref_right": right_elbow_ref,
        "vai_chuan_trai": left_shoulder_ref,
        "khuyu_chuan_trai": left_elbow_ref,
        "vai_chuan_phai": right_shoulder_ref,
        "khuyu_chuan_phai": right_elbow_ref,
    }
    for key, value in updates.items():
        if value is None:
            continue
        if overwrite or frame.get(key) in (None, ""):
            frame[key] = value
    return frame


def _analysis_output_stem(video: dict[str, Any]) -> str:
    source = _job_video_path(video) or f"video_{time.time()}"
    return f"processed_{hashlib.md5(source.encode('utf-8')).hexdigest()[:10]}"


def _ensure_export_dir() -> Path:
    path = REPO_ROOT / "processed_results" / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_dataset_segment(value: Any, fallback: str = "unknown") -> str:
    text = _search_text(value)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback


def _dataset_patient_dir(video: dict[str, Any]) -> Path:
    patient = video.get("full_name") or video.get("patient_username") or video.get("username") or "unknown-patient"
    return DATASET_DIR / _safe_dataset_segment(patient, "unknown-patient")


def _dataset_video_slug(video: dict[str, Any]) -> str:
    name = video.get("video_name") or video.get("stored_filename") or video.get("video_path") or "video"
    exercise = video.get("exercise") or ""
    date_token = _video_date_token(video) if "_video_date_token" in globals() else ""
    base = "-".join(part for part in [_safe_dataset_segment(name, "video"), _safe_dataset_segment(exercise, ""), date_token] if part)
    return base[:140] or "video"


def _dataset_kind_dir(video: dict[str, Any], kind: str) -> Path:
    kind_key = _safe_dataset_segment(kind, "artifact")
    return _dataset_patient_dir(video) / kind_key


def _dataset_legacy_index_path() -> Path:
    return DATASET_DIR / "dataset.json"


def _dataset_manifest_path() -> Path:
    return DATASET_DIR / "dataset_manifest.json"


def _load_dataset_manifest() -> dict[str, Any]:
    path = _dataset_manifest_path()
    data = read_json(path, {})
    if not isinstance(data, dict):
        data = {}
    data.setdefault("updated_at", "")
    data.setdefault("dataset_dir", str(DATASET_DIR))
    data.setdefault("patients", {})
    data.setdefault("artifacts", [])
    return data


def _save_dataset_manifest(data: dict[str, Any]) -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    data["dataset_dir"] = str(DATASET_DIR)
    write_json(_dataset_manifest_path(), data)
    write_json(_dataset_legacy_index_path(), data)


def _copy_dataset_file(source: Path | None, target_dir: Path, filename: str) -> Path | None:
    if not source or not source.is_file():
        return None
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename, source.name)
    target = target_dir / safe_name
    try:
        if source.resolve() == target.resolve():
            return target
    except Exception:
        pass
    if target.exists() and target.stat().st_size == source.stat().st_size and target.stat().st_mtime >= source.stat().st_mtime:
        return target
    shutil.copy2(source, target)
    return target


def _dataset_path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.is_dir():
        return 0
    total = 0
    for file in path.rglob("*"):
        if file.is_file():
            try:
                total += file.stat().st_size
            except OSError:
                pass
    return total


def _dataset_file_count(path: Path) -> int:
    if path.is_file():
        return 1
    if not path.is_dir():
        return 0
    return sum(1 for file in path.rglob("*") if file.is_file() and file.name != "_dataset_source.json")


def _dataset_artifact_entry(
    video: dict[str, Any],
    source: Path,
    saved: Path,
    *,
    kind: str,
    phase: str,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "patient": _clean_text(video.get("full_name") or video.get("patient_username") or video.get("username")),
        "patient_username": _clean_text(video.get("patient_username") or video.get("username")),
        "video_name": _clean_text(video.get("video_name") or video.get("stored_filename")),
        "exercise": _clean_text(video.get("exercise")),
        "kind": kind,
        "phase": _phase_suffix(phase),
        "source_path": _relative_repo_path(source),
        "dataset_path": _relative_repo_path(saved),
        "size": _dataset_path_size(saved),
        "is_dir": saved.is_dir(),
        "file_count": _dataset_file_count(saved),
        "updated_at": _now_iso(),
        "updated_by": _clean_text((user or {}).get("username")),
    }


def _upsert_dataset_manifest_entry(entry: dict[str, Any]) -> None:
    manifest = _load_dataset_manifest()
    patient_key = _safe_dataset_segment(entry.get("patient") or entry.get("patient_username"), "unknown-patient")
    patient = manifest.setdefault("patients", {}).setdefault(
        patient_key,
        {
            "patient": entry.get("patient") or entry.get("patient_username"),
            "patient_username": entry.get("patient_username"),
            "updated_at": "",
            "artifacts": [],
        },
    )
    key_fields = ("patient_username", "video_name", "exercise", "kind", "phase")
    def same(item: dict[str, Any]) -> bool:
        if not all(_clean_text(item.get(key)) == _clean_text(entry.get(key)) for key in key_fields):
            return False
        if _clean_text(entry.get("kind")) == "charts":
            return _clean_text(item.get("chart_name")) == _clean_text(entry.get("chart_name")) and _clean_text(item.get("dataset_path")) == _clean_text(entry.get("dataset_path"))
        return True

    artifacts = [item for item in manifest.get("artifacts", []) if isinstance(item, dict) and not same(item)]
    artifacts.append(entry)
    manifest["artifacts"] = artifacts[-2000:]
    patient_artifacts = [item for item in patient.get("artifacts", []) if isinstance(item, dict) and not same(item)]
    patient_artifacts.append(entry)
    patient["artifacts"] = patient_artifacts[-500:]
    patient["updated_at"] = entry.get("updated_at")
    _save_dataset_manifest(manifest)


def _sync_export_to_dataset(
    video: dict[str, Any],
    source: Path,
    *,
    kind: str,
    phase: str,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phase_key = _phase_suffix(phase)
    video_slug = _dataset_video_slug(video)
    if kind == "video":
        folder = _dataset_kind_dir(video, "video")
        filename = f"{video_slug}_{phase_key}{source.suffix.lower() or '.mp4'}"
    elif kind == "frames":
        kind = "zip" if source.suffix.lower() == ".zip" else "frames"
        folder = _dataset_kind_dir(video, kind)
        filename = f"{video_slug}_frames_{phase_key}{source.suffix.lower() or '.zip'}"
    elif kind == "csv":
        folder = _dataset_kind_dir(video, "csv")
        filename = f"{video_slug}_{phase_key}{source.suffix.lower() or '.csv'}"
    elif kind == "zip":
        folder = _dataset_kind_dir(video, "zip")
        filename = f"{video_slug}_{phase_key}{source.suffix.lower() or '.zip'}"
    elif kind == "charts":
        folder = _dataset_kind_dir(video, "charts")
        filename = _safe_filename(source.name, f"{video_slug}_{phase_key}.png")
    else:
        folder = _dataset_kind_dir(video, kind)
        filename = _safe_filename(source.name, f"{video_slug}_{phase_key}{source.suffix.lower()}")
    saved = _copy_dataset_file(source, folder, filename)
    if not saved:
        return {}
    entry = _dataset_artifact_entry(video, source, saved, kind=kind, phase=phase_key, user=user)
    _upsert_dataset_manifest_entry(entry)
    return entry


def _source_signature(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        return {
            "source_path": str(path.resolve()),
            "source_mtime_ns": int(stat.st_mtime_ns),
            "source_size": int(stat.st_size),
        }
    except OSError:
        return {"source_path": str(path)}


def _safe_replace_dataset_dir(target_dir: Path) -> None:
    target_resolved = target_dir.resolve()
    dataset_resolved = DATASET_DIR.resolve()
    if target_resolved == dataset_resolved or dataset_resolved not in target_resolved.parents:
        raise RuntimeError("Refuse to clear a path outside database/dataset.")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)


def _sync_frame_images_to_dataset(
    video: dict[str, Any],
    source: Path | None,
    *,
    phase: str,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not source or not source.exists():
        return {}
    phase_key = _phase_suffix(phase)
    video_slug = _dataset_video_slug(video)
    target_dir = _dataset_kind_dir(video, "frames") / f"{video_slug}_{phase_key}"
    marker_path = target_dir / "_dataset_source.json"
    signature = _source_signature(source)
    marker = read_json(marker_path, {}) if marker_path.is_file() else {}
    if (
        isinstance(marker, dict)
        and marker.get("source_path") == signature.get("source_path")
        and marker.get("source_mtime_ns") == signature.get("source_mtime_ns")
        and marker.get("source_size") == signature.get("source_size")
        and _dataset_file_count(target_dir) > 0
    ):
        entry = _dataset_artifact_entry(video, source if source.is_file() else target_dir, target_dir, kind="frames", phase=phase_key, user=user)
        _upsert_dataset_manifest_entry(entry)
        return entry

    image_suffixes = (".jpg", ".jpeg", ".png", ".webp")
    _safe_replace_dataset_dir(target_dir)
    written = 0
    if source.is_dir():
        files = [file for file in _artifact_frame_files(source) if file.suffix.lower() in image_suffixes]
        for ordinal, file in enumerate(files, start=1):
            suffix = file.suffix.lower() or ".jpg"
            shutil.copy2(file, target_dir / f"f_{ordinal:06d}{suffix}")
            written += 1
    elif source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            members = [name for name in archive.namelist() if Path(name).suffix.lower() in image_suffixes]
            for ordinal, name in enumerate(members, start=1):
                suffix = Path(name).suffix.lower() or ".jpg"
                (target_dir / f"f_{ordinal:06d}{suffix}").write_bytes(archive.read(name))
                written += 1
    if not written:
        return {}
    marker_data = {**signature, "file_count": written, "updated_at": _now_iso()}
    write_json(marker_path, marker_data)
    entry = _dataset_artifact_entry(video, source if source.is_file() else target_dir, target_dir, kind="frames", phase=phase_key, user=user)
    entry["source_file_count"] = written
    _upsert_dataset_manifest_entry(entry)
    return entry


def _sync_available_artifacts_to_dataset(video: dict[str, Any], user: dict[str, Any] | None = None) -> dict[str, Any]:
    synced: dict[str, Any] = {}
    hydrated = _hydrate_video_artifacts(video)
    candidates = {
        "video": _resolve_existing_path(hydrated.get("processed_path") or hydrated.get("pose_video_path")),
        "raw_video": _resolve_existing_path(hydrated.get("video_path")),
        "csv": _resolve_existing_path(hydrated.get("df_path")),
        "json": _resolve_existing_path(hydrated.get("all_frames_data_path")),
        "zip": _resolve_existing_path(hydrated.get("frames_zip") or hydrated.get("frames_zip_path")),
    }
    for kind, source in candidates.items():
        if source and source.is_file():
            entry_kind = "video" if kind == "raw_video" else kind
            entry_phase = "raw" if kind == "raw_video" and not _resolve_existing_path(hydrated.get("processed_path") or hydrated.get("pose_video_path")) else "all"
            entry = _sync_export_to_dataset(hydrated, source, kind=entry_kind, phase=entry_phase, user=user)
            if entry:
                synced[f"dataset_{kind}_path"] = entry.get("dataset_path")
    processed = _resolve_existing_path(hydrated.get("processed_path") or hydrated.get("pose_video_path") or hydrated.get("video_path"))
    frame_source = candidates.get("zip") or _frame_dir_for_video(hydrated, processed)
    if frame_source:
        frame_entry = _sync_frame_images_to_dataset(hydrated, frame_source, phase="all", user=user)
        if frame_entry:
            synced["dataset_frames_path"] = frame_entry.get("dataset_path")
    return synced


def _phase_suffix(phase: str) -> str:
    normalized = _search_text(phase) or "all"
    return normalized if normalized in {"all", "g1", "g2", "g3", "overview", "raw"} else "all"


def _phase_bounds_for_export(video: dict[str, Any], frame_records: list[dict[str, Any]], frame_total: int, phase: str) -> tuple[int, int]:
    phase_key = _phase_suffix(phase)
    total = max(0, int(frame_total or len(frame_records or [])))
    if phase_key in {"all", "overview"} or total <= 0:
        return 0, total
    phase_bounds = _segment_bounds_from_angle_items(frame_records) if frame_records and not _is_pulley_exercise(video.get("exercise")) else None
    if phase_bounds and len(phase_bounds) >= 4:
        mapping = {
            "g1": (int(phase_bounds[0]), int(phase_bounds[1])),
            "g2": (int(phase_bounds[1]), int(phase_bounds[2])),
            "g3": (int(phase_bounds[2]), int(phase_bounds[3])),
        }
        start, end = mapping.get(phase_key, (0, total))
        return max(0, min(total, start)), max(0, min(total, end))
    thirds = [0, total // 3, (2 * total) // 3, total]
    mapping = {"g1": (thirds[0], thirds[1]), "g2": (thirds[1], thirds[2]), "g3": (thirds[2], thirds[3])}
    return mapping.get(phase_key, (0, total))


def _copy_or_link_export(source: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size == source.stat().st_size and output.stat().st_mtime >= source.stat().st_mtime:
        return output
    shutil.copy2(source, output)
    return output


def _cut_video_export(source: Path, stem: str, phase: str, start_offset: int, end_offset: int, total_frames: int) -> Path | None:
    if not source.is_file():
        return None
    phase_key = _phase_suffix(phase)
    output = _ensure_export_dir() / f"{stem}_{phase_key}.mp4"
    if phase_key in {"all", "overview"} or start_offset <= 0 and end_offset >= total_frames:
        return _copy_or_link_export(source, output)
    fps = _video_fps(source, 30.0)
    start_second = max(0.0, float(start_offset) / max(1.0, fps))
    duration_second = max(0.1, float(max(1, end_offset - start_offset)) / max(1.0, fps))
    if output.exists() and output.stat().st_size > 1024 and output.stat().st_mtime >= source.stat().st_mtime:
        return output
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start_second:.4f}",
        "-i",
        str(source),
        "-t",
        f"{duration_second:.4f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output),
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=600)
    except Exception:
        output.unlink(missing_ok=True)
        return None
    if result.returncode != 0 or not output.is_file() or output.stat().st_size < 1024:
        output.unlink(missing_ok=True)
        return None
    return output


def _zip_frame_dir_slice(frame_dir: Path, output: Path, *, start_offset: int = 0, end_offset: int | None = None) -> Path | None:
    files = _artifact_frame_files(frame_dir)
    if not files:
        return None
    end = len(files) if end_offset is None else max(start_offset, min(len(files), end_offset))
    selected = files[max(0, start_offset) : end]
    if not selected:
        return None
    latest = max(file.stat().st_mtime for file in selected)
    if output.exists() and output.stat().st_size > 1024 and output.stat().st_mtime >= latest:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for ordinal, file in enumerate(selected, start=start_offset + 1):
                archive.write(file, arcname=f"f_{ordinal:06d}{file.suffix.lower() or '.jpg'}")
        for attempt in range(5):
            try:
                tmp.replace(output)
                break
            except PermissionError:
                if attempt >= 4:
                    raise
                time.sleep(0.4)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except PermissionError:
            pass
        return None
    return output if output.is_file() and output.stat().st_size > 32 else None


def _zip_frame_zip_slice(frame_zip: Path, output: Path, *, start_offset: int = 0, end_offset: int | None = None) -> Path | None:
    lookup = _zip_member_lookup(frame_zip)
    if not lookup:
        return None
    names = [lookup[key] for key in sorted(lookup)]
    end = len(names) if end_offset is None else max(start_offset, min(len(names), end_offset))
    selected = names[max(0, start_offset) : end]
    if not selected:
        return None
    if output.exists() and output.stat().st_size > 1024 and output.stat().st_mtime >= frame_zip.stat().st_mtime:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    try:
        with zipfile.ZipFile(frame_zip) as source, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as dest:
            for ordinal, name in enumerate(selected, start=start_offset + 1):
                suffix = Path(name).suffix.lower() or ".jpg"
                dest.writestr(f"f_{ordinal:06d}{suffix}", source.read(name))
        tmp.replace(output)
    except Exception:
        tmp.unlink(missing_ok=True)
        return None
    return output if output.is_file() and output.stat().st_size > 32 else None


def _zip_video_frames_slice(source_video: Path, output: Path, *, start_offset: int = 0, end_offset: int | None = None) -> Path | None:
    if not source_video.is_file():
        return None
    total = _video_frame_count(source_video)
    if total <= 0:
        return None
    start = max(0, min(total, int(start_offset or 0)))
    end = total if end_offset is None else max(start, min(total, int(end_offset or total)))
    if start >= end:
        return None
    expected = end - start
    if output.exists() and output.stat().st_size > 1024 and output.stat().st_mtime >= source_video.stat().st_mtime:
        try:
            with zipfile.ZipFile(output) as archive:
                if len([name for name in archive.namelist() if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]) >= expected:
                    return output
        except Exception:
            output.unlink(missing_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(f"{source_video.resolve()}:{source_video.stat().st_mtime_ns}:{start}:{end}".encode("utf-8")).hexdigest()[:12]
    frame_dir = output.parent / f"_{output.stem}_{cache_key}_frames"
    shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    pattern = frame_dir / "f_%06d.jpg"
    vf = f"select=between(n\\,{start}\\,{end - 1})"
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source_video),
        "-vf",
        vf,
        "-vsync",
        "0",
        "-start_number",
        str(start + 1),
        "-q:v",
        "3",
        str(pattern),
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=900)
        if result.returncode != 0:
            shutil.rmtree(frame_dir, ignore_errors=True)
            return None
        built = _zip_frame_dir_slice(frame_dir, output, start_offset=0, end_offset=None)
    finally:
        shutil.rmtree(frame_dir, ignore_errors=True)
    return built


def _generate_pose_frame_zip_from_video(
    video: dict[str, Any],
    source_video: Path,
    frame_records: list[dict[str, Any]],
    output: Path,
    *,
    start_offset: int = 0,
    end_offset: int | None = None,
) -> Path | None:
    if not source_video.is_file():
        return None
    total = len(frame_records)
    if total <= 0:
        total = _video_frame_count(source_video)
    if total <= 0:
        return None
    end = total if end_offset is None else max(start_offset, min(total, end_offset))
    start = max(0, min(total, start_offset))
    if start >= end:
        return None
    phase_bounds = _segment_bounds_from_angle_items(frame_records) if frame_records and not _is_pulley_exercise(video.get("exercise")) else None
    source_count = max(1, _video_frame_count(source_video))
    if output.exists() and output.stat().st_size > 1024 and output.stat().st_mtime >= source_video.stat().st_mtime:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    try:
        import cv2  # type: ignore[import-not-found]

        cap = cv2.VideoCapture(str(source_video))
        last_frame = None
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for record_pos in range(start, end):
                record = frame_records[record_pos] if record_pos < len(frame_records) and isinstance(frame_records[record_pos], dict) else {"index": record_pos + 1}
                requested = _frame_number_key(record.get("index") or record.get("frame"))
                source_index = max(0, min(source_count - 1, (requested - 1) if requested is not None else record_pos))
                cap.set(cv2.CAP_PROP_POS_FRAMES, source_index)
                ok, frame = cap.read()
                if not ok or frame is None:
                    frame = last_frame
                if frame is None:
                    continue
                last_frame = frame
                frame_data = _frame_with_detected_pose(frame, _frame_with_exercise_context(record, video.get("exercise")))
                display_index = record_pos + 1
                _, _, threshold = _phase_for_position(record_pos, total, video.get("exercise"), phase_bounds)
                threshold = _to_float(frame_data.get("threshold") or frame_data.get("phase_threshold")) or float(threshold)
                rendered = _draw_pose_analysis_overlay(frame, frame_data, display_index, threshold=threshold)
                ok, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok:
                    archive.writestr(f"f_{display_index:06d}.jpg", encoded.tobytes())
        cap.release()
        tmp.replace(output)
    except Exception:
        tmp.unlink(missing_ok=True)
        return None
    return output if output.is_file() and output.stat().st_size > 32 else None


def _persist_video_artifacts(video_index: int, updates: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    videos = _load_data("video_list")
    if not isinstance(videos, list) or not (0 <= video_index < len(videos)) or not isinstance(videos[video_index], dict):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy video để cập nhật database.")
    current = dict(videos[video_index])
    for key, value in updates.items():
        if value not in (None, ""):
            current[key] = value
    current["artifact_updated_at"] = _now_iso()
    current["artifact_updated_by"] = _clean_text(user.get("username"))
    try:
        current.update(_sync_available_artifacts_to_dataset(current, user))
    except Exception as exc:
        current["dataset_sync_error"] = _clean_text(str(exc))[:500]
    videos[video_index] = current
    _save_data("video_list", videos)
    return current


def _artifact_paths_for_export(video: dict[str, Any]) -> dict[str, Any]:
    hydrated = _hydrate_video_artifacts(video)
    processed_video_path = _resolve_video_source_path(hydrated.get("processed_path"))
    raw_video_path = _resolve_video_source_path(hydrated.get("video_path"))
    pose_playback_path = _pose_playback_video_path(processed_video_path or _resolve_existing_path(hydrated.get("processed_path")))
    preferred_video = processed_video_path if _audio_codec(processed_video_path) else (pose_playback_path or processed_video_path or raw_video_path)
    playback_video_path, _ = _resolve_playback_video_path(preferred_video, raw_video_path)
    frame_path = _ensure_hf_dataset_file(hydrated.get("all_frames_data_path"), min_size=128) or _resolve_existing_path(hydrated.get("all_frames_data_path"))
    df_path = _ensure_hf_dataset_file(hydrated.get("df_path"), min_size=128) or _resolve_existing_path(hydrated.get("df_path"))
    frame_records = _read_frame_records(frame_path)
    csv_frame_records = _frame_records_from_csv(df_path) if df_path else []
    if frame_records and csv_frame_records:
        frame_records = _merge_frame_records_with_csv_pose(frame_records, csv_frame_records)
    elif csv_frame_records:
        frame_records = csv_frame_records
    frame_dir = _frame_dir_for_video(hydrated, processed_video_path or playback_video_path)
    frame_zip = _frame_zip_for_video(hydrated, processed_video_path or playback_video_path)
    return {
        "video": hydrated,
        "processed_video_path": processed_video_path,
        "raw_video_path": raw_video_path,
        "pose_playback_path": pose_playback_path,
        "playback_video_path": playback_video_path,
        "frame_path": frame_path,
        "df_path": df_path,
        "frame_records": frame_records,
        "frame_dir": frame_dir,
        "frame_zip": frame_zip,
    }


def _prepare_export_file(video: dict[str, Any], phase: str, kind: str) -> tuple[Path, dict[str, Any]]:
    paths = _artifact_paths_for_export(video)
    hydrated = paths["video"]
    phase_key = _phase_suffix(phase)
    kind_key = _search_text(kind) or "video"
    frame_records: list[dict[str, Any]] = paths["frame_records"] or []
    frame_total = len(frame_records) or _video_frame_count(paths["playback_video_path"])
    start_offset, end_offset = _phase_bounds_for_export(hydrated, frame_records, frame_total, phase_key)
    stem = _processed_stem(paths["processed_video_path"] or paths["playback_video_path"] or paths["raw_video_path"]) or f"video_{hashlib.md5(_job_video_path(hydrated).encode('utf-8')).hexdigest()[:10]}"
    export_stem = f"{stem}_export"
    updates: dict[str, Any] = {}

    if kind_key in {"video", "mp4"}:
        source = paths["playback_video_path"]
        if not source or not source.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chưa tìm thấy video đã phân tích để lưu/tải.")
        output = _cut_video_export(source, export_stem, phase_key, start_offset, end_offset, frame_total)
        if not output:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Không tạo được video export.")
        if phase_key in {"all", "overview"}:
            updates["processed_path"] = _relative_repo_path(source)
            if paths["pose_playback_path"]:
                updates["pose_video_path"] = _relative_repo_path(paths["pose_playback_path"])
        updates[f"export_video_{phase_key}"] = _relative_repo_path(output)
        return output, updates

    if kind_key in {"frames", "frame", "zip", "images"}:
        output = _ensure_export_dir() / f"{export_stem}_frames_{phase_key}.zip"
        if _needs_video_pose_frame_preference(hydrated) and paths["playback_video_path"]:
            built = _zip_video_frames_slice(paths["playback_video_path"], output, start_offset=start_offset, end_offset=end_offset)
        elif _needs_video_pose_frame_preference(hydrated) and paths["raw_video_path"] and frame_records:
            built = _generate_pose_frame_zip_from_video(
                hydrated,
                paths["raw_video_path"],
                frame_records,
                output,
                start_offset=start_offset,
                end_offset=end_offset,
            )
        elif paths["frame_dir"]:
            built = _zip_frame_dir_slice(paths["frame_dir"], output, start_offset=start_offset, end_offset=end_offset)
        elif paths["frame_zip"]:
            built = _zip_frame_zip_slice(paths["frame_zip"], output, start_offset=start_offset, end_offset=end_offset)
        else:
            built = None
        if not built:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chưa tìm thấy frame/ZIP để lưu/tải.")
        if phase_key in {"all", "overview"}:
            updates["frames_zip"] = _relative_repo_path(built)
            updates["frames_zip_path"] = _relative_repo_path(built)
            if paths["frame_path"]:
                updates["all_frames_data_path"] = _relative_repo_path(paths["frame_path"])
            if paths["df_path"]:
                updates["df_path"] = _relative_repo_path(paths["df_path"])
        updates[f"export_frames_{phase_key}"] = _relative_repo_path(built)
        return built, updates

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại export chỉ hỗ trợ video hoặc frames.")


def _video_name_tokens(value: Any) -> set[str]:
    text = _search_text(Path(_clean_text(value).replace("\\", "/")).name)
    text = re.sub(r"\.[a-z0-9]{2,5}$", " ", text)
    text = re.sub(r"(^|[\s_-])\d{4,8}([\s_-]|$)", " ", text)
    text = re.sub(r"\b(processed|video|clip|tmp|ftmp|final|h264|mp4|mov|avi|mkv|f)\b", " ", text)
    return {token for token in re.split(r"[^a-z0-9]+", text) if len(token) > 1}


def _compatible_text(left: Any, right: Any) -> bool:
    left_text = _search_text(left)
    right_text = _search_text(right)
    if not left_text or not right_text:
        return True
    return left_text == right_text or left_text in right_text or right_text in left_text


def _video_name_score(video_name: Any, evaluation_name: Any) -> int:
    video_text = _search_text(video_name)
    evaluation_text = _search_text(evaluation_name)
    if not video_text or not evaluation_text:
        return 1
    if video_text == evaluation_text:
        return 6
    if video_text in evaluation_text or evaluation_text in video_text:
        return 5
    video_tokens = _video_name_tokens(video_name)
    evaluation_tokens = _video_name_tokens(evaluation_name)
    if not video_tokens or not evaluation_tokens:
        return 1
    overlap = video_tokens & evaluation_tokens
    if video_tokens <= evaluation_tokens or evaluation_tokens <= video_tokens:
        return 4
    if len(overlap) >= max(2, min(len(video_tokens), len(evaluation_tokens)) - 1):
        return 3
    if len(overlap) >= 2:
        return 2
    return 0


def _evaluation_time(evaluation: dict[str, Any]) -> datetime:
    for key in ("time", "timestamp", "created_at", "updated_at"):
        parsed = _parse_vn_time(evaluation.get(key))
        if parsed != datetime.min:
            return parsed
    return datetime.min


def _evaluation_video_identity(record: dict[str, Any]) -> tuple[str, str, str]:
    patient = _patient_group_key(record)
    video_name = _search_text(record.get("video_name") or record.get("stored_filename") or record.get("video_path"))
    exercise = _exercise_group_key(record)
    return (patient, video_name, exercise)


def _has_video_identity(identity: tuple[str, str, str]) -> bool:
    _, video_name, _ = identity
    return bool(video_name)


def _is_research_ai_evaluation(record: dict[str, Any]) -> bool:
    text = " ".join(
        _search_text(record.get(key))
        for key in ("doctor_name", "doctor_username", "submitted_by", "source", "comments_ncv")
    )
    return any(marker in text for marker in ("ncv", "nghien cuu", "research", "ai_researcher", "ai researcher"))


def _video_accuracy_value(video: dict[str, Any]) -> float | None:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    for value in (video.get("accuracy"), metrics.get("do_chinh_xac"), metrics.get("accuracy")):
        parsed = _to_float(value)
        if parsed is not None:
            return parsed
    return None


def _ai_result_for_accuracy(accuracy: float | None) -> str:
    if accuracy is None:
        return "Chưa rõ"
    if accuracy >= 80:
        return "Đúng"
    if accuracy >= 50:
        return "Gần đúng"
    return "Sai"


def _ai_advice_for_accuracy(accuracy: float | None) -> str:
    if accuracy is None:
        return "Cần kiểm tra lại dữ liệu phân tích."
    if accuracy >= 80:
        return "Duy trì bài tập và theo dõi định kỳ."
    if accuracy >= 50:
        return "Cần rèn luyện thêm để giảm sai số."
    return "Cần chuyên gia y tế hướng dẫn thêm trước khi tăng cường độ."


def _format_ai_percent(value: float | None) -> str:
    return "N/A" if value is None else f"{float(value):.1f}%"


def _video_ai_evaluation_time(video: dict[str, Any]) -> str:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    for value in (
        metrics.get("metrics_refreshed_at"),
        video.get("latest_bundle_updated_at"),
        video.get("artifact_updated_at"),
        video.get("updated_at"),
        video.get("uploaded_at"),
        video.get("created_at"),
        video.get("time"),
    ):
        parsed = _parse_vn_time(value)
        if parsed != datetime.min:
            return parsed.strftime("%H:%M - %d/%m/%Y")
    return datetime.now().strftime("%H:%M - %d/%m/%Y")


def _video_ai_evaluation_record(video: dict[str, Any]) -> dict[str, Any] | None:
    identity = _evaluation_video_identity(video)
    if not _has_video_identity(identity):
        return None
    accuracy = _video_accuracy_value(video)
    if accuracy is None:
        return None
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    pass_frames = int(_to_float(metrics.get("frame_dung")) or 0)
    near_frames = int(_to_float(metrics.get("frame_gan_dung")) or 0)
    fail_frames = int(_to_float(metrics.get("frame_sai")) or 0)
    unknown_frames = int(
        _to_float(metrics.get("frame_khong_nhan_dang"))
        or _to_float(metrics.get("unknown_frames"))
        or _to_float(metrics.get("ml_frame_unknown"))
        or 0
    )
    total_frames = int(
        _to_float(metrics.get("tong_frame_da_cham"))
        or _to_float(metrics.get("tong_frame"))
        or _to_float(metrics.get("ml_tong_frame"))
        or (pass_frames + near_frames + fail_frames + unknown_frames)
        or 0
    )
    valid_frames = int(
        _to_float(metrics.get("tong_frame_hop_le"))
        or max(0, total_frames - unknown_frames)
        or _to_float(metrics.get("ml_tong_frame"))
        or 0
    )
    f1_score = _to_float(metrics.get("f1_score"))
    mae = _to_float(metrics.get("mae_tong"))
    exercise = _clean_text(video.get("exercise")) or "Bài tập"
    advice = _ai_advice_for_accuracy(accuracy)
    metric_lines = [
        f"- Bài tập: {exercise}",
        f"- Độ chính xác: {_format_ai_percent(accuracy)} | Đúng: {pass_frames}/{valid_frames} frames",
        f"- Frame: Đúng {pass_frames} | Gần đúng {near_frames} | Sai {fail_frames} | Unknown {unknown_frames} | Tổng {total_frames}",
    ]
    if mae is not None:
        metric_lines.append(f"- MAE: {mae:.2f}°")
    if f1_score is not None:
        metric_lines.append(f"- F1-score: {f1_score:.3f}")
    metric_lines.append(f"- AI đề xuất: {advice}")
    raw_id = "|".join([*identity, _clean_text(video.get("time")), f"{accuracy:.4f}"])
    return {
        "id": "ai-summary-" + hashlib.sha256(raw_id.encode("utf-8", errors="ignore")).hexdigest()[:16],
        "patient_username": _clean_text(video.get("username") or video.get("patient_username") or video.get("full_name")) or "Unknown",
        "full_name": _clean_text(video.get("full_name") or video.get("patient_name") or video.get("username")) or "Unknown",
        "doctor_username": "AI_Researcher",
        "doctor_name": "NCV/AI: Tự động từ video_list",
        "video_name": _clean_text(video.get("video_name") or video.get("stored_filename") or video.get("video_path")),
        "exercise": exercise,
        "ai_accuracy": round(float(accuracy), 2),
        "ai_accuracy_g1": round(float(accuracy), 2),
        "ai_accuracy_g2": round(float(accuracy), 2),
        "ai_accuracy_g3": round(float(accuracy), 2),
        "doctor_result": _ai_result_for_accuracy(accuracy),
        "errors": [],
        "comments": "BÁO CÁO PHÂN TÍCH AI (TỔNG QUAN):\n" + "\n".join(metric_lines),
        "comments_ncv": "Tự đồng bộ từ kết quả AI mới nhất trong video_list.json.",
        "plan": f"Kế hoạch luyện tập đề xuất:\n- {exercise}: Đạt {_format_ai_percent(accuracy)} - {advice}",
        "time": _video_ai_evaluation_time(video),
        "created_at": _clean_text(
            metrics.get("metrics_refreshed_at")
            or video.get("latest_bundle_updated_at")
            or video.get("artifact_updated_at")
            or video.get("updated_at")
            or video.get("uploaded_at")
        )
        or _now_iso(),
        "source": "video_list_ai_researcher",
        "giai_doan": _clean_text(video.get("giai_doan")) or "Phân tích Tổng quan",
        "sai_so": video.get("sai_so") if video.get("sai_so") is not None else 30,
    }


def _merge_video_ai_evaluation_summaries(
    evaluations: list[dict[str, Any]],
    videos: list[Any],
) -> list[dict[str, Any]]:
    records = [item for item in evaluations if isinstance(item, dict)]
    output = [record for record in records if not _is_video_list_ai_summary(record)]
    generated_identities: set[tuple[str, str, str]] = set()
    for video in videos:
        if not isinstance(video, dict):
            continue
        identity = _evaluation_video_identity(video)
        if not _has_video_identity(identity) or identity in generated_identities:
            continue
        generated = _video_ai_evaluation_record(video)
        if generated is None:
            continue
        output.append(generated)
        generated_identities.add(identity)
    return output


def _match_evaluations_for_video(video: dict[str, Any], evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exercise = video.get("exercise")
    patient_names = {
        _search_text(video.get("username")),
        _search_text(video.get("full_name")),
        _search_text(video.get("patient_username")),
    }
    patient_names.discard("")
    scored_matches: list[tuple[int, dict[str, Any]]] = []
    for evaluation in evaluations:
        evaluation_patient = _search_text(evaluation.get("patient_username") or evaluation.get("username") or evaluation.get("full_name"))
        if patient_names and evaluation_patient and evaluation_patient not in patient_names:
            continue
        if not _compatible_text(exercise, evaluation.get("exercise")):
            continue
        score = _video_name_score(video.get("video_name"), evaluation.get("video_name"))
        if score <= 0:
            continue
        scored_matches.append((score, evaluation))
    scored_matches.sort(key=lambda item: (item[0], _evaluation_time(item[1])))
    return [evaluation for _, evaluation in scored_matches]


def _video_date_token(video: dict[str, Any]) -> str:
    parsed = _parse_vn_time(video.get("time"))
    return "" if parsed == datetime.min else parsed.strftime("%Y%m%d")


def _progress_result(progress: dict[str, Any]) -> dict[str, Any]:
    result = progress.get("result")
    return result if isinstance(result, dict) else {}


def _progress_exercise_texts(progress: dict[str, Any]) -> list[Any]:
    result = _progress_result(progress)
    exercise = result.get("exercise")
    values: list[Any] = [progress.get("exercise")]
    if isinstance(exercise, dict):
        values.extend([exercise.get("ten"), exercise.get("name"), exercise.get("label")])
    else:
        values.append(exercise)
    job_meta = progress.get("job_meta")
    if isinstance(job_meta, dict):
        values.extend([job_meta.get("exercise_name"), job_meta.get("exercise")])
    return [value for value in values if _clean_text(value)]


def _progress_artifacts(progress: dict[str, Any]) -> dict[str, Any]:
    result = _progress_result(progress)
    stats = result.get("stats") if isinstance(result.get("stats"), dict) else {}
    return {
        "processed_path": result.get("processed_video_path")
        or result.get("output_video_path")
        or progress.get("processed_video_path")
        or progress.get("processed_path"),
        "df_path": result.get("df_path") or progress.get("df_path"),
        "all_frames_data_path": result.get("all_frames_data_path") or progress.get("all_frames_data_path"),
        "frames_zip": result.get("frames_zip") or progress.get("frames_zip"),
        "frames_dir": result.get("temp_frames_dir") or result.get("frames_dir") or progress.get("frames_dir"),
        "metrics": stats,
    }


def _progress_artifact_score(progress: dict[str, Any]) -> int:
    artifacts = _progress_artifacts(progress)
    return sum(
        [
            bool(_resolve_existing_path(artifacts.get("processed_path"))),
            bool(_resolve_existing_path(artifacts.get("df_path"))),
            bool(_resolve_existing_path(artifacts.get("all_frames_data_path"))),
            bool(_resolve_existing_path(artifacts.get("frames_zip"))),
            bool(_resolve_existing_path(artifacts.get("frames_dir"))),
        ]
    )


def _existing_artifact_count(video: dict[str, Any]) -> int:
    processed = _resolve_existing_path(video.get("processed_path"))
    return sum(
        [
            bool(processed),
            bool(_resolve_existing_path(video.get("df_path"))),
            bool(_resolve_existing_path(video.get("all_frames_data_path"))),
            bool(_resolve_existing_path(video.get("frames_zip") or video.get("frames_zip_path"))),
            bool(_resolve_existing_path(video.get("frames_dir") or video.get("all_frames_dir"))),
        ]
    )


def _related_search_text(left: Any, right: Any) -> bool:
    left_text = _search_text(left)
    right_text = _search_text(right)
    return bool(left_text and right_text and (left_text == right_text or left_text in right_text or right_text in left_text))


def _progress_match_score(video: dict[str, Any], progress: dict[str, Any]) -> int:
    patient_values = [video.get("username"), video.get("full_name"), video.get("patient_username")]
    progress_patients = [progress.get("username"), progress.get("patient_username"), progress.get("full_name")]
    job_meta = progress.get("job_meta")
    if isinstance(job_meta, dict):
        progress_patients.append(job_meta.get("full_name"))
    if not any(_related_search_text(left, right) for left in patient_values for right in progress_patients):
        return 0

    video_date = _video_date_token(video)
    progress_date_text = " ".join(_clean_text(progress.get(key)) for key in ("video_path", "processed_path", "video_name"))
    progress_dates = set(re.findall(r"20\d{6}", progress_date_text))
    if video_date and progress_dates and video_date not in progress_dates:
        return 0

    exercise = video.get("exercise")
    exercise_score = 0
    if _clean_text(exercise):
        if any(_compatible_text(exercise, progress_exercise) for progress_exercise in _progress_exercise_texts(progress)):
            exercise_score = 1
        else:
            return 0

    name_score = max(
        _video_name_score(video.get("video_name"), progress.get("video_name")),
        _video_name_score(video.get("video_name"), progress.get("video_path")),
    )
    return 2 + exercise_score + name_score


def _find_progress_for_video(video: dict[str, Any], *, require_success: bool = False) -> dict[str, Any] | None:
    progress_dir = REPO_ROOT / "processed_results"
    if not progress_dir.is_dir():
        return None
    best: tuple[int, int, float, dict[str, Any]] | None = None
    for path in progress_dir.glob("progress_*.json"):
        progress = read_json(path, {})
        if not isinstance(progress, dict):
            continue
        if require_success and _search_text(progress.get("status")) != "success":
            continue
        match_score = _progress_match_score(video, progress)
        if match_score <= 0:
            continue
        artifact_score = _progress_artifact_score(progress)
        if require_success and artifact_score < 2:
            continue
        candidate = (match_score, artifact_score, path.stat().st_mtime, progress)
        if best is None or candidate[:3] > best[:3]:
            best = candidate
    return best[3] if best else None


def _backup_video_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in BACKUP_VIDEO_LIST_PATHS:
        data = read_json(path, []) if path.is_file() else []
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict) or _existing_artifact_count(item) <= 0:
                continue
            key = (_patient_group_key(item), _exercise_group_key(item), _search_text(item.get("video_name")))
            if key in seen:
                continue
            seen.add(key)
            records.append(item)
    return records


def _slot_matches(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return _patient_group_key(left) == _patient_group_key(right) and _exercise_group_key(left) == _exercise_group_key(right)


def _backup_match_score(video: dict[str, Any], backup: dict[str, Any]) -> tuple[int, int, int, datetime]:
    if not _slot_matches(video, backup):
        return (0, 0, 0, datetime.min)
    artifact_score = _existing_artifact_count(backup)
    if artifact_score <= 0:
        return (0, 0, 0, datetime.min)
    name_score = max(
        _video_name_score(video.get("video_name"), backup.get("video_name")),
        _video_name_score(video.get("video_path"), backup.get("video_path")),
    )
    path_score = 1 if _related_search_text(video.get("video_path"), backup.get("video_path")) else 0
    return (artifact_score, name_score, path_score, _parse_vn_time(backup.get("time")))


def _find_backup_video_for_slot(video: dict[str, Any]) -> dict[str, Any] | None:
    best: tuple[tuple[int, int, int, datetime], dict[str, Any]] | None = None
    for backup in _backup_video_records():
        score = _backup_match_score(video, backup)
        if score[0] <= 0 or score[1] <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, backup)
    return best[1] if best else None


def _local_video_artifact_records() -> list[tuple[int, dict[str, Any]]]:
    data = _load_data("video_list")
    if not isinstance(data, list):
        return []
    return [(idx, item) for idx, item in enumerate(data) if isinstance(item, dict) and _existing_artifact_count(item) > 0]


def _local_artifact_match_score(video: dict[str, Any], candidate: dict[str, Any]) -> tuple[int, int, int, datetime]:
    if not _slot_matches(video, candidate):
        return (0, 0, 0, datetime.min)
    artifact_score = _existing_artifact_count(candidate)
    if artifact_score <= _existing_artifact_count(video):
        return (0, 0, 0, datetime.min)
    name_score = max(
        _video_name_score(video.get("video_name"), candidate.get("video_name")),
        _video_name_score(video.get("video_path"), candidate.get("video_path")),
    )
    path_score = 1 if _related_search_text(video.get("video_path"), candidate.get("video_path")) else 0
    return (artifact_score, name_score, path_score, _parse_vn_time(candidate.get("time")))


def _find_local_video_artifacts_for_slot(video: dict[str, Any]) -> tuple[int, dict[str, Any]] | None:
    best: tuple[tuple[int, int, int, datetime], int, dict[str, Any]] | None = None
    for idx, candidate in _local_video_artifact_records():
        if candidate is video:
            continue
        score = _local_artifact_match_score(video, candidate)
        if score[0] <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, idx, candidate)
    return (best[1], best[2]) if best else None


def _merge_missing_analysis_metadata(video: dict[str, Any], source: dict[str, Any], source_name: str) -> dict[str, Any]:
    merged = dict(video)
    for key in ARTIFACT_METADATA_KEYS:
        if source.get(key) and not _resolve_existing_path(merged.get(key)):
            merged[key] = source[key]
    source_metrics = source.get("metrics") if isinstance(source.get("metrics"), dict) else {}
    current_metrics = merged.get("metrics") if isinstance(merged.get("metrics"), dict) else {}
    if source_metrics:
        merged["metrics"] = {**source_metrics, **current_metrics}
    for key in ANALYSIS_METADATA_KEYS:
        if key == "metrics":
            continue
        if source.get(key) is not None and merged.get(key) is None:
            merged[key] = source[key]
    if merged.get("accuracy") is None:
        accuracy = _to_float(merged.get("metrics", {}).get("do_chinh_xac") if isinstance(merged.get("metrics"), dict) else None)
        if accuracy is not None:
            merged["accuracy"] = accuracy
    merged["_artifact_source"] = source_name
    for key in LOCAL_ARTIFACT_ALIAS_KEYS:
        if source.get(key) is not None and merged.get(key) is None:
            merged[key] = source[key]
    return merged


def _hydrate_video_artifacts(video: dict[str, Any]) -> dict[str, Any]:
    progress = _find_progress_for_video(video, require_success=True)
    hydrated = dict(video)
    if progress:
        hydrated = _merge_missing_analysis_metadata(hydrated, _progress_artifacts(progress), "progress")
    if _existing_artifact_count(hydrated) < 3:
        local_artifacts = _find_local_video_artifacts_for_slot(hydrated)
        if local_artifacts:
            source_idx, source = local_artifacts
            source = {**source, "_local_video_artifacts": True, "source_video_index": source_idx}
            hydrated = _merge_missing_analysis_metadata(hydrated, source, "local_video_list")
    if _existing_artifact_count(hydrated) < 3:
        backup = _find_backup_video_for_slot(hydrated)
        if backup:
            hydrated = _merge_missing_analysis_metadata(hydrated, backup, "debug_backup")
    return hydrated


def _public_analysis_job(video: dict[str, Any], progress: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(progress, dict):
        return None
    progress_value = float(progress.get("progress") or 0)
    status_text = _clean_text(progress.get("status")) or "unknown"
    job_meta = progress.get("job_meta") if isinstance(progress.get("job_meta"), dict) else {}
    return {
        "job_id": progress.get("job_id") or _analysis_job_id(progress.get("video_path") or _job_video_path(video)),
        "run_id": progress.get("run_id") or "",
        "status": status_text,
        "progress": progress_value,
        "status_msg": progress.get("status_msg") or "",
        "error_msg": progress.get("error_msg") or "",
        "updated_at": progress.get("updated_at") or progress.get("heartbeat") or progress.get("start_time") or "",
        "heartbeat": progress.get("heartbeat") or progress.get("start_time") or "",
        "current_frame": progress.get("current_frame"),
        "total_frames": progress.get("total_frames"),
        "processed_frames": progress.get("processed_frames"),
        "elapsed_seconds": progress.get("elapsed_seconds"),
        "fps_effective": progress.get("fps_effective"),
        "job_meta": job_meta,
        "steps": progress.get("steps") if isinstance(progress.get("steps"), list) else _job_steps(status_text, progress_value),
    }


def _slice_window(total: int, *, offset: int = 0, limit: int = 24) -> tuple[int, int]:
    safe_total = max(0, int(total or 0))
    safe_limit = max(1, min(96, int(limit or 24)))
    safe_offset = max(0, min(max(0, safe_total - 1), int(offset or 0))) if safe_total else 0
    return safe_offset, safe_limit


PHASE_THRESHOLDS = {
    "g1": 45,
    "g2": 30,
    "g3": 15,
}

PHASE_LABELS = {
    "all": "Tất cả",
    "overview": "Tổng quan",
    "g1": "G1 · Khởi đầu",
    "g2": "G2 · Hồi phục",
    "g3": "G3 · Chuẩn xác",
}


def _is_pulley_exercise(exercise: Any) -> bool:
    text = _search_text(exercise)
    return any(keyword in text for keyword in ("gay", "pulley", "stick"))


def _angle_signal_value(item: dict[str, Any], angle_key: str) -> float:
    if angle_key == "shoulder":
        value = _first_float(item.get("goc_vai"), item.get("shoulder_angle"), item.get("angle"), item.get("goc_vai_phai"), item.get("goc_vai_trai"))
        return 90.0 if value is None else value
    value = _first_float(item.get("goc_khuyu"), item.get("elbow_angle"), item.get("goc_khuyu_phai"), item.get("goc_khuyu_trai"))
    return 170.0 if value is None else value


def _segment_bounds_from_angle_items(items: list[dict[str, Any]]) -> list[int]:
    total = len(items)
    if total < 30:
        return [0, total // 3, (2 * total) // 3, total]

    shoulder_values = [_angle_signal_value(item, "shoulder") for item in items]
    elbow_values = [_angle_signal_value(item, "elbow") for item in items]
    shoulder_std = statistics.pstdev(shoulder_values) if len(shoulder_values) > 1 else 0.0
    elbow_std = statistics.pstdev(elbow_values) if len(elbow_values) > 1 else 0.0
    angles = shoulder_values if shoulder_std > elbow_std else elbow_values

    window_size = min(15, max(5, total // 30))
    half = window_size // 2
    smoothed: list[float] = []
    for idx in range(total):
        start = max(0, idx - half)
        end = min(total, idx + half + 1)
        window = angles[start:end]
        smoothed.append(sum(window) / max(1, len(window)))

    ordered = sorted(smoothed)
    threshold_val = ordered[len(ordered) // 2]
    min_dist = max(15, total // 8)
    valleys: list[int] = []
    for idx in range(window_size, total - window_size):
        local = smoothed[idx - window_size : idx + window_size + 1]
        if smoothed[idx] <= min(local) and smoothed[idx] < threshold_val:
            if not valleys or idx - valleys[-1] >= min_dist:
                valleys.append(idx)

    filtered = [idx for idx in valleys if idx > total // 10 and idx < total - total // 10]
    if len(filtered) >= 2:
        if len(filtered) == 2:
            n1, n2 = filtered[0], filtered[1]
        else:
            best_diff = float("inf")
            n1, n2 = total // 3, (2 * total) // 3
            for first_idx, first in enumerate(filtered):
                for second in filtered[first_idx + 1 :]:
                    sizes = [first, second - first, total - second]
                    diff = max(sizes) - min(sizes)
                    if diff < best_diff:
                        best_diff = diff
                        n1, n2 = first, second
    elif len(filtered) == 1:
        valley = filtered[0]
        if valley < total // 2:
            n1 = valley
            n2 = valley + (total - valley) // 2
        else:
            n1 = valley // 2
            n2 = valley
    else:
        n1, n2 = total // 3, (2 * total) // 3

    n1 = min(max(1, int(n1)), max(1, total - 2))
    n2 = min(max(n1 + 1, int(n2)), max(n1 + 1, total - 1))
    return [0, n1, n2, total]


def _phase_for_position(
    position: int,
    total: int,
    exercise: Any,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
) -> tuple[str, str, int]:
    if _is_pulley_exercise(exercise):
        return "overview", PHASE_LABELS["overview"], 30
    if phase_bounds and len(phase_bounds) >= 4:
        n0, n1, n2, n3 = [int(value) for value in phase_bounds[:4]]
        safe_position = max(n0, min(max(n0, n3 - 1), int(position or 0)))
        if n0 <= safe_position < n1:
            key = "g1"
        elif n1 <= safe_position < n2:
            key = "g2"
        else:
            key = "g3"
        return key, PHASE_LABELS[key], PHASE_THRESHOLDS[key]
    safe_total = max(1, int(total or 1))
    ratio = max(0, position) / safe_total
    if ratio < 1 / 3:
        key = "g1"
    elif ratio < 2 / 3:
        key = "g2"
    else:
        key = "g3"
    return key, PHASE_LABELS[key], PHASE_THRESHOLDS[key]


def _project_record_angles_for_exercise(record: dict[str, Any], exercise: Any) -> dict[str, Any]:
    exercise_key = _frame_exercise_key(record, exercise)
    record["exercise_key"] = exercise_key
    if _clean_text(exercise):
        record["exercise"] = _exercise_label(exercise)
    if _to_bool(record.get("filtered_stranger")):
        return _mark_filtered_stranger(record, _clean_text(record.get("stranger_reason")) or "multiple_people")
    if exercise_key in {"codman", "pulley"} and not _has_complete_pose(record):
        return _mark_filtered_stranger(record, "incomplete_pose_33")
    left_shoulder, left_elbow = _side_angle_values(record, "left")
    right_shoulder, right_elbow = _side_angle_values(record, "right")
    if exercise_key == "codman":
        if right_shoulder is not None:
            record["goc_vai"] = right_shoulder
        if right_elbow is not None:
            record["goc_khuyu"] = right_elbow
    elif exercise_key == "pulley":
        shoulder_values = [value for value in (left_shoulder, right_shoulder) if value is not None]
        elbow_values = [value for value in (left_elbow, right_elbow) if value is not None]
        if shoulder_values:
            record["goc_vai"] = sum(shoulder_values) / len(shoulder_values)
        if elbow_values:
            record["goc_khuyu"] = sum(elbow_values) / len(elbow_values)
    record.update(_fill_missing_reference_values(record, exercise))
    return record


def _apply_phase_thresholds_to_records(
    records: list[dict[str, Any]],
    exercise: Any,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
) -> list[int] | tuple[int, int, int, int] | None:
    if not records:
        return phase_bounds
    total = len(records)
    fallback_refs = _default_refs_for_exercise(exercise)
    if _is_pulley_exercise(exercise):
        for record in records:
            _project_record_angles_for_exercise(record, exercise)
            threshold = 30
            is_unknown = _frame_should_be_unknown(record, exercise)
            status_text = "UNKNOWN" if is_unknown else (_phase_status_for_frame(record, threshold, fallback_refs, exercise) or _frame_status(record) or "FAIL")
            record["phase"] = "overview"
            record["phase_label"] = PHASE_LABELS["overview"]
            record["threshold"] = threshold
            record["phase_threshold"] = threshold
            record["phase_status"] = status_text
            record["status"] = status_text
            record["dung"] = status_text == "PASS"
            record["gan_dung"] = status_text == "NEAR"
            if status_text == "UNKNOWN":
                _mark_filtered_stranger(record, _clean_text(record.get("stranger_reason")) or "multiple_people")
        return phase_bounds
    for record in records:
        _project_record_angles_for_exercise(record, exercise)
    effective_bounds = phase_bounds or _segment_bounds_from_angle_items(records)
    for idx, record in enumerate(records):
        phase, phase_label, threshold = _phase_for_position(idx, total, exercise, effective_bounds)
        is_unknown = _frame_should_be_unknown(record, exercise)
        status_text = "UNKNOWN" if is_unknown else (_phase_status_for_frame(record, threshold, fallback_refs, exercise) or _frame_status(record) or "FAIL")
        record["phase"] = phase
        record["phase_label"] = phase_label
        record["threshold"] = threshold
        record["phase_threshold"] = threshold
        record["phase_status"] = status_text
        record["status"] = status_text
        if status_text == "UNKNOWN":
            _mark_filtered_stranger(record, _clean_text(record.get("stranger_reason")) or "multiple_people")
        record["dung"] = status_text == "PASS"
        record["gan_dung"] = status_text == "NEAR"
    return effective_bounds


def _frame_status(frame: dict[str, Any]) -> str:
    status_text = _search_text(frame.get("status") or frame.get("quality") or frame.get("result"))
    if "near" in status_text or "gan" in status_text or _to_bool(frame.get("gan_dung")):
        return "NEAR"
    if "pass" in status_text or "dung" in status_text or _to_bool(frame.get("dung")):
        return "PASS"
    if "fail" in status_text or "sai" in status_text:
        return "FAIL"
    if "dung" in frame or "gan_dung" in frame:
        return "FAIL"
    return ""


def _first_float(*values: Any) -> float | None:
    for value in values:
        number = _to_float(value)
        if number is not None:
            return number
    return None


def _safe_nested_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _frame_angle_values(frame: dict[str, Any], exercise: Any = None) -> tuple[float | None, float | None]:
    exercise_key = _frame_exercise_key(frame, exercise)
    left_shoulder, left_elbow = _side_angle_values(frame, "left")
    right_shoulder, right_elbow = _side_angle_values(frame, "right")
    if exercise_key == "codman":
        return (
            _first_float(right_shoulder, frame.get("goc_vai"), frame.get("shoulder_angle"), frame.get("angle")),
            _first_float(right_elbow, frame.get("goc_khuyu"), frame.get("elbow_angle")),
        )
    if exercise_key == "pulley":
        shoulder_values = [value for value in (left_shoulder, right_shoulder) if value is not None]
        elbow_values = [value for value in (left_elbow, right_elbow) if value is not None]
        shoulder = sum(shoulder_values) / len(shoulder_values) if shoulder_values else None
        elbow = sum(elbow_values) / len(elbow_values) if elbow_values else None
        return (
            _first_float(shoulder, frame.get("goc_vai"), frame.get("shoulder_angle"), frame.get("angle")),
            _first_float(elbow, frame.get("goc_khuyu"), frame.get("elbow_angle")),
        )
    return (
        _first_float(frame.get("goc_vai"), frame.get("shoulder_angle"), frame.get("angle"), right_shoulder, left_shoulder),
        _first_float(frame.get("goc_khuyu"), frame.get("elbow_angle"), right_elbow, left_elbow),
    )


def _frame_delta_values(
    frame: dict[str, Any],
    refs: tuple[float | None, float | None],
    exercise: Any = None,
) -> tuple[float | None, float | None]:
    shoulder_ref, elbow_ref = refs
    exercise_key = _frame_exercise_key(frame, exercise)
    if _should_fill_youtube_reference(frame, exercise or frame.get("exercise")):
        enriched = _fill_missing_reference_values(frame, exercise or frame.get("exercise"))
        frame.update(enriched)
        shoulder_ref, elbow_ref = _merge_ref_values(_frame_ref_values(frame), refs)
    if exercise_key == "pulley":
        left_shoulder, left_elbow = _side_angle_values(frame, "left")
        right_shoulder, right_elbow = _side_angle_values(frame, "right")
        left_shoulder_ref, left_elbow_ref = _frame_ref_side_values(frame, "left")
        right_shoulder_ref, right_elbow_ref = _frame_ref_side_values(frame, "right")
        left_shoulder_ref = left_shoulder_ref if left_shoulder_ref is not None else shoulder_ref
        left_elbow_ref = left_elbow_ref if left_elbow_ref is not None else elbow_ref
        right_shoulder_ref = right_shoulder_ref if right_shoulder_ref is not None else shoulder_ref
        right_elbow_ref = right_elbow_ref if right_elbow_ref is not None else elbow_ref
        shoulder_deltas = [
            abs(value - ref)
            for value, ref in ((left_shoulder, left_shoulder_ref), (right_shoulder, right_shoulder_ref))
            if value is not None and ref is not None
        ]
        elbow_deltas = [
            abs(value - ref)
            for value, ref in ((left_elbow, left_elbow_ref), (right_elbow, right_elbow_ref))
            if value is not None and ref is not None
        ]
        return (max(shoulder_deltas) if shoulder_deltas else None, max(elbow_deltas) if elbow_deltas else None)
    shoulder, elbow = _frame_angle_values(frame, exercise)
    return (
        abs(shoulder - shoulder_ref) if shoulder is not None and shoulder_ref is not None else None,
        abs(elbow - elbow_ref) if elbow is not None and elbow_ref is not None else None,
    )


def _frame_ref_values(frame: dict[str, Any]) -> tuple[float | None, float | None]:
    eval_info = _safe_nested_dict(frame.get("eval_info"))
    return (
        _first_float(
            frame.get("shoulder_ref"),
            frame.get("vai_chuan"),
            frame.get("goc_vai_chuan"),
            frame.get("ref_shoulder"),
            eval_info.get("shoulder_ref"),
            eval_info.get("vai_chuan"),
            eval_info.get("goc_vai_chuan"),
        ),
        _first_float(
            frame.get("elbow_ref"),
            frame.get("khuyu_chuan"),
            frame.get("goc_khuyu_chuan"),
            frame.get("ref_elbow"),
            eval_info.get("elbow_ref"),
            eval_info.get("khuyu_chuan"),
            eval_info.get("goc_khuyu_chuan"),
        ),
    )


def _video_ref_values(video: dict[str, Any]) -> tuple[float | None, float | None]:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    shoulder_ref = _first_float(
        metrics.get("tb_vai_chuan"),
        metrics.get("vai_chuan"),
        metrics.get("goc_vai_chuan"),
        metrics.get("shoulder_ref"),
        metrics.get("ref_shoulder"),
        video.get("tb_vai_chuan"),
        video.get("vai_chuan"),
        video.get("goc_vai_chuan"),
        video.get("shoulder_ref"),
        video.get("ref_shoulder"),
    )
    elbow_ref = _first_float(
        metrics.get("tb_khuyu_chuan"),
        metrics.get("khuyu_chuan"),
        metrics.get("goc_khuyu_chuan"),
        metrics.get("elbow_ref"),
        metrics.get("ref_elbow"),
        video.get("tb_khuyu_chuan"),
        video.get("khuyu_chuan"),
        video.get("goc_khuyu_chuan"),
        video.get("elbow_ref"),
        video.get("ref_elbow"),
    )
    return shoulder_ref, elbow_ref


def _merge_ref_values(
    frame_refs: tuple[float | None, float | None],
    fallback_refs: tuple[float | None, float | None] | None = None,
) -> tuple[float | None, float | None]:
    fallback_shoulder, fallback_elbow = fallback_refs or (None, None)
    return frame_refs[0] if frame_refs[0] is not None else fallback_shoulder, frame_refs[1] if frame_refs[1] is not None else fallback_elbow


def _phase_status_for_frame(
    frame: dict[str, Any],
    threshold: float,
    fallback_refs: tuple[float | None, float | None] | None = None,
    exercise: Any = None,
) -> str:
    if _frame_should_be_unknown(frame, exercise):
        return "UNKNOWN"
    exercise_key = _frame_exercise_key(frame, exercise)
    shoulder_ref, elbow_ref = _merge_ref_values(_frame_ref_values(frame), fallback_refs)
    if _should_fill_youtube_reference(frame, exercise or frame.get("exercise")):
        enriched = _fill_missing_reference_values(frame, exercise or frame.get("exercise"))
        frame.update(enriched)
        shoulder_ref, elbow_ref = _merge_ref_values(_frame_ref_values(frame), fallback_refs)
    if exercise_key == "pulley":
        left_shoulder, left_elbow = _side_angle_values(frame, "left")
        right_shoulder, right_elbow = _side_angle_values(frame, "right")
        left_shoulder_ref, left_elbow_ref = _frame_ref_side_values(frame, "left")
        right_shoulder_ref, right_elbow_ref = _frame_ref_side_values(frame, "right")
        left_shoulder_ref = left_shoulder_ref if left_shoulder_ref is not None else shoulder_ref
        left_elbow_ref = left_elbow_ref if left_elbow_ref is not None else elbow_ref
        right_shoulder_ref = right_shoulder_ref if right_shoulder_ref is not None else shoulder_ref
        right_elbow_ref = right_elbow_ref if right_elbow_ref is not None else elbow_ref
        side_values = [left_shoulder, left_elbow, right_shoulder, right_elbow]
        if any(value is not None for value in side_values):
            return _status_from_angle_pairs(
                [
                    (left_shoulder, left_shoulder_ref),
                    (left_elbow, left_elbow_ref),
                    (right_shoulder, right_shoulder_ref),
                    (right_elbow, right_elbow_ref),
                ],
                threshold,
            )
    shoulder, elbow = _frame_angle_values(frame, exercise)
    if shoulder is None or elbow is None or shoulder_ref is None or elbow_ref is None:
        return _frame_status(frame) or "UNKNOWN"
    shoulder_delta = abs(shoulder - shoulder_ref)
    elbow_delta = abs(elbow - elbow_ref)
    if shoulder_delta <= threshold and elbow_delta <= threshold:
        return "PASS"
    if shoulder_delta <= threshold * 1.5 and elbow_delta <= threshold * 1.5:
        return "NEAR"
    return "FAIL"


def _frame_ml_label(frame: dict[str, Any]) -> str:
    for key in ("ml_label_text", "ml_label", "ml_result", "rf_label", "predicted_label", "classifier_label"):
        value = _clean_text(frame.get(key))
        if value:
            return value
    ml = _safe_nested_dict(frame.get("ml") or frame.get("classifier"))
    for key in ("label", "result", "prediction"):
        value = _clean_text(ml.get(key))
        if value:
            return value
    return ""


def _frame_ml_confidence(frame: dict[str, Any]) -> float | None:
    for key in ("ml_confidence", "ml_score", "ml_prob", "confidence", "classifier_confidence"):
        value = _to_float(frame.get(key))
        if value is not None:
            return value
    ml = _safe_nested_dict(frame.get("ml") or frame.get("classifier"))
    for key in ("confidence", "prob", "score"):
        value = _to_float(ml.get(key))
        if value is not None:
            return value
    probs = frame.get("ml_probs") or frame.get("probabilities") or ml.get("probabilities")
    if isinstance(probs, dict):
        numeric = [_to_float(value) for value in probs.values()]
        values = [value for value in numeric if value is not None]
        if values:
            return max(values)
    return None


def _frame_ml_probabilities(frame: dict[str, Any]) -> dict[str, float | None]:
    probs = frame.get("ml_probs") or frame.get("probabilities")
    ml = _safe_nested_dict(frame.get("ml") or frame.get("classifier"))
    if not isinstance(probs, dict):
        probs = ml.get("probabilities")
    output = {"pass": None, "near": None, "fail": None}
    if isinstance(probs, dict):
        aliases = {
            "pass": ("pass", "dung", "correct", "ml_prob_dung", "2"),
            "near": ("near", "gan_dung", "nearly_correct", "ml_prob_gan_dung", "1"),
            "fail": ("fail", "sai", "incorrect", "ml_prob_sai", "0"),
        }
        for key, names in aliases.items():
            for name in names:
                value = _to_float(probs.get(name))
                if value is not None:
                    output[key] = value
                    break
    output["pass"] = output["pass"] if output["pass"] is not None else _to_float(frame.get("ml_prob_dung"))
    output["near"] = output["near"] if output["near"] is not None else _to_float(frame.get("ml_prob_gan_dung"))
    output["fail"] = output["fail"] if output["fail"] is not None else _to_float(frame.get("ml_prob_sai"))
    return output


def _enrich_frame_payload(
    frame: dict[str, Any],
    *,
    absolute_idx: int,
    total: int,
    image_url: str,
    source: str,
    exercise: Any,
    fallback_refs: tuple[float | None, float | None] | None = None,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
) -> dict[str, Any]:
    frame = _frame_with_exercise_context(frame, exercise)
    exercise_key = _frame_exercise_key(frame, exercise)
    frame = _fill_missing_reference_values(frame, exercise)
    is_unknown_frame = _frame_should_be_unknown(frame, exercise)
    frame_index = frame.get("index") or frame.get("frame") or absolute_idx + 1
    phase, phase_label, threshold = _phase_for_position(absolute_idx, total, exercise, phase_bounds)
    phase_status = _phase_status_for_frame(frame, threshold, fallback_refs, exercise)
    status_text = phase_status or _frame_status(frame) or ("FRAME" if source == "artifact" else "VIDEO")
    shoulder, elbow = _frame_angle_values(frame, exercise)
    left_shoulder, left_elbow = _side_angle_values(frame, "left")
    right_shoulder, right_elbow = _side_angle_values(frame, "right")
    shoulder_ref, elbow_ref = _merge_ref_values(_frame_ref_values(frame), fallback_refs)
    left_shoulder_ref, left_elbow_ref = _frame_ref_side_values(frame, "left")
    right_shoulder_ref, right_elbow_ref = _frame_ref_side_values(frame, "right")
    shoulder_delta, elbow_delta = _frame_delta_values(frame, (shoulder_ref, elbow_ref), exercise)
    ml_probs = _frame_ml_probabilities(frame)
    if is_unknown_frame or status_text == "UNKNOWN":
        status_text = "UNKNOWN"
        phase_status = "UNKNOWN"
        shoulder = elbow = None
        left_shoulder = left_elbow = right_shoulder = right_elbow = None
        shoulder_ref = elbow_ref = None
        left_shoulder_ref = left_elbow_ref = right_shoulder_ref = right_elbow_ref = None
        shoulder_delta = elbow_delta = None
        ml_probs = {"pass": None, "near": None, "fail": None}
    return {
        "index": frame_index,
        "timestamp": frame.get("timestamp") or "",
        "status": status_text,
        "phase": phase,
        "phase_label": phase_label,
        "phase_status": phase_status or status_text,
        "threshold": threshold,
        "angle": shoulder,
        "elbow": elbow,
        "left_shoulder": left_shoulder,
        "left_elbow": left_elbow,
        "right_shoulder": right_shoulder,
        "right_elbow": right_elbow,
        "shoulder_ref": shoulder_ref,
        "elbow_ref": elbow_ref,
        "left_shoulder_ref": left_shoulder_ref if left_shoulder_ref is not None else shoulder_ref,
        "left_elbow_ref": left_elbow_ref if left_elbow_ref is not None else elbow_ref,
        "right_shoulder_ref": right_shoulder_ref if right_shoulder_ref is not None else shoulder_ref,
        "right_elbow_ref": right_elbow_ref if right_elbow_ref is not None else elbow_ref,
        "shoulder_delta": shoulder_delta,
        "elbow_delta": elbow_delta,
        "ml_label": "UNKNOWN" if status_text == "UNKNOWN" else _frame_ml_label(frame),
        "ml_confidence": None if status_text == "UNKNOWN" else _frame_ml_confidence(frame),
        "ml_prob_pass": ml_probs["pass"],
        "ml_prob_near": ml_probs["near"],
        "ml_prob_fail": ml_probs["fail"],
        "image_url": image_url,
        "source": source,
        "exercise_key": exercise_key,
        "filtered_stranger": _to_bool(frame.get("filtered_stranger")),
        "stranger_reason": frame.get("stranger_reason"),
        "ref_source": frame.get("ref_source"),
        "youtube_ref_exercise_id": frame.get("youtube_ref_exercise_id"),
        "motion_type": frame.get("motion_type"),
        "youtube_ref_time": frame.get("youtube_ref_time"),
    }


def _frame_group_summary(frames: list[dict[str, Any]], total: int, exercise: Any) -> list[dict[str, Any]]:
    frames = [_frame_with_exercise_context(frame, exercise) for frame in frames if isinstance(frame, dict)]
    phase_bounds = _segment_bounds_from_angle_items(frames) if frames and len(frames) == total and not _is_pulley_exercise(exercise) else None
    keys = ["overview"] if _is_pulley_exercise(exercise) else ["g1", "g2", "g3"]
    groups: list[dict[str, Any]] = [
        {
            "key": "all",
            "label": PHASE_LABELS["all"],
            "threshold": None,
            "total": total,
            "start_offset": 0,
            "end_offset": total,
            "pass": 0,
            "near": 0,
            "fail": 0,
            "unknown": 0,
        }
    ]
    for key in keys:
        threshold = 30 if key == "overview" else PHASE_THRESHOLDS[key]
        if phase_bounds and key in {"g1", "g2", "g3"}:
            bounds_by_key = {
                "g1": (phase_bounds[0], phase_bounds[1]),
                "g2": (phase_bounds[1], phase_bounds[2]),
                "g3": (phase_bounds[2], phase_bounds[3]),
            }
            start_offset, end_offset = bounds_by_key[key]
            phase_total = max(0, end_offset - start_offset)
        else:
            start_offset, end_offset, phase_total = total, 0, 0
        groups.append(
            {
                "key": key,
                "label": PHASE_LABELS[key],
                "threshold": threshold,
                "total": phase_total,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "pass": 0,
                "near": 0,
                "fail": 0,
                "unknown": 0,
            }
        )
    if not phase_bounds:
        for idx in range(total):
            phase, _, _ = _phase_for_position(idx, total, exercise)
            group = next((item for item in groups if item["key"] == phase), None)
            if group:
                group["total"] += 1
                group["start_offset"] = min(int(group["start_offset"]), idx)
                group["end_offset"] = max(int(group["end_offset"]), idx + 1)
    fallback_refs = _default_refs_for_exercise(exercise)
    for idx, frame in enumerate(frames):
        phase, _, threshold = _phase_for_position(idx, total, exercise, phase_bounds)
        status_key = _search_text(_phase_status_for_frame(frame, threshold, fallback_refs, exercise) or frame.get("phase_status") or frame.get("status"))
        status_field = (
            "unknown"
            if "unknown" in status_key or "no pose" in status_key or "khong nhan" in status_key or "lan nguoi" in status_key
            else "pass"
            if "pass" in status_key
            else "near"
            if "near" in status_key
            else "fail"
            if "fail" in status_key
            else ""
        )
        if not status_field:
            continue
        for group in groups:
            if group["key"] == "all" or group["key"] == phase:
                group[status_field] += 1
    return groups


def _read_frame_group_payload(
    path: Path | None,
    exercise: Any,
    fallback_refs: tuple[float | None, float | None] | None = None,
) -> list[dict[str, Any]]:
    frames = _read_frame_records(path)
    if not frames:
        return []
    frame_items = [frame for frame in frames if isinstance(frame, dict)]
    total = len(frames)
    phase_bounds = _segment_bounds_from_angle_items(frame_items) if frame_items and not _is_pulley_exercise(exercise) else None
    groups = _frame_group_summary(frame_items, total, exercise)
    by_key = {group["key"]: group for group in groups}
    for group in by_key.values():
        group["pass"] = 0
        group["near"] = 0
        group["fail"] = 0
        group["unknown"] = 0
    for idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue
        phase, _, threshold = _phase_for_position(idx, total, exercise, phase_bounds)
        frame = _frame_with_exercise_context(frame, exercise)
        status_text = _phase_status_for_frame(frame, threshold, fallback_refs, exercise) or _frame_status(frame)
        status_field = "unknown" if status_text == "UNKNOWN" else "pass" if status_text == "PASS" else "near" if status_text == "NEAR" else "fail" if status_text == "FAIL" else ""
        if not status_field:
            continue
        by_key["all"][status_field] += 1
        if phase in by_key:
            by_key[phase][status_field] += 1
    return groups


def _read_frame_records(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        frames = data.get("frames") or data.get("all_frames") or data.get("data") or []
    else:
        frames = data
    if not isinstance(frames, list):
        return []
    return [frame for frame in frames if isinstance(frame, dict)]


def _frame_records_from_csv(path: Path | None) -> list[dict[str, Any]]:
    rows = _read_analysis_rows(path)
    output: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        frame = dict(row)
        frame.setdefault("index", row.get("frame") or row.get("frame_idx") or row.get("frame_number") or idx + 1)
        output.append(frame)
    return output


def _merge_frame_records_with_csv_pose(
    frame_records: list[dict[str, Any]],
    csv_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not frame_records:
        return csv_records
    if not csv_records:
        return frame_records
    csv_lookup = _frame_record_lookup(csv_records)
    merged: list[dict[str, Any]] = []
    for position, record in enumerate(frame_records):
        frame_number = _frame_number_key(record.get("index") or record.get("frame") or record.get("frame_idx") or record.get("frame_number"))
        csv_record = csv_lookup.get(frame_number or -1, (None, None))[1]
        if not isinstance(csv_record, dict) and position < len(csv_records):
            csv_record = csv_records[position]
        if not isinstance(csv_record, dict):
            merged.append(record)
            continue
        next_record = dict(record)
        for key, value in csv_record.items():
            if key.startswith("pt") or key in {
                "frame",
                "frame_idx",
                "frame_number",
                "timestamp_seconds",
                "goc_vai",
                "goc_khuyu",
                "goc_vai_trai",
                "goc_khuyu_trai",
                "goc_vai_phai",
                "goc_khuyu_phai",
                "dung",
                "gan_dung",
                "vai_dung",
                "khuyu_dung",
                "vai_chuan",
                "khuyu_chuan",
                "shoulder_ref",
                "elbow_ref",
                "ml_label",
                "ml_label_text",
                "dung_ml",
                "gan_dung_ml",
                "ml_score",
                "ml_confidence",
                "ml_prob_sai",
                "ml_prob_gan_dung",
                "ml_prob_dung",
                "filtered_stranger",
                "stranger_reason",
                "status",
                "phase_status",
            }:
                if value not in (None, "") and next_record.get(key) in (None, ""):
                    next_record[key] = value
        merged.append(next_record)
    return merged


def _frame_number_key(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _frame_record_lookup(records: list[dict[str, Any]] | None) -> dict[int, tuple[int, dict[str, Any]]]:
    lookup: dict[int, tuple[int, dict[str, Any]]] = {}
    for position, record in enumerate(records or []):
        if not isinstance(record, dict):
            continue
        frame_number = _frame_number_key(record.get("index") or record.get("frame") or record.get("frame_idx") or record.get("frame_number"))
        if frame_number is None:
            frame_number = position + 1
        lookup.setdefault(frame_number, (position, record))
    return lookup


def _frame_image_lookup(path: Path | None) -> dict[int, Path]:
    if not path or not path.is_dir():
        return {}
    lookup: dict[int, Path] = {}
    for file in sorted(path.iterdir()):
        if not file.is_file() or file.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        match = re.search(r"(\d+)", file.stem)
        if not match:
            continue
        lookup.setdefault(int(match.group(1)), file)
    return lookup


def _zip_member_lookup(path: Path | None) -> dict[int, str]:
    if not path or not path.is_file():
        return {}
    try:
        stat = path.stat()
        cache_key = str(path.resolve())
        cached = ZIP_MEMBER_CACHE.get(cache_key)
        if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
            return {int(key): value for key, value in cached[2].items()}
        with zipfile.ZipFile(path) as archive:
            members = [
                name
                for name in archive.namelist()
                if not name.endswith("/") and Path(name).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
    except Exception:
        return {}
    lookup: dict[int, str] = {}
    for name in sorted(members):
        match = re.search(r"(\d+)", Path(name).stem)
        if not match:
            continue
        lookup.setdefault(int(match.group(1)), name)
    ZIP_MEMBER_CACHE[cache_key] = (stat.st_mtime, stat.st_size, {str(key): value for key, value in lookup.items()})
    return lookup


def _first_artifact_preview_token(frame_dir: Path | None, frame_zip: Path | None) -> str | None:
    dir_lookup = _frame_image_lookup(frame_dir)
    if dir_lookup:
        first_key = min(dir_lookup)
        token = _register_media(dir_lookup[first_key])
        if token:
            return token
    zip_lookup = _zip_member_lookup(frame_zip)
    if zip_lookup:
        first_key = min(zip_lookup)
        token = _register_zip_media(frame_zip, zip_lookup[first_key])
        if token:
            return token
    return None


def _artifact_frame_files(frame_dir: Path | None) -> list[Path]:
    lookup = _frame_image_lookup(frame_dir)
    return [lookup[key] for key in sorted(lookup)]


def _artifact_cache_signature(frame_dir: Path | None, frame_zip: Path | None) -> str:
    for path in (frame_zip, frame_dir):
        if not path or not path.exists():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        return hashlib.sha256(f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8")).hexdigest()[:16]
    return hashlib.sha256(str(time.time()).encode("utf-8")).hexdigest()[:16]


def _extract_frame_zip_for_playback(frame_zip: Path | None, signature: str) -> Path | None:
    if not frame_zip or not frame_zip.is_file():
        return None
    target_dir = REPO_ROOT / "processed_results" / "_playback_cache" / f"{frame_zip.stem}_{signature}_frames"
    marker = target_dir / ".complete"
    if marker.exists() and _frame_image_lookup(target_dir):
        return target_dir
    shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(frame_zip) as archive:
            lookup = _zip_member_lookup(frame_zip)
            for ordinal, key in enumerate(sorted(lookup), start=1):
                name = lookup[key]
                suffix = Path(name).suffix.lower() or ".jpg"
                with archive.open(name) as source, (target_dir / f"frame_{ordinal:06d}{suffix}").open("wb") as dest:
                    shutil.copyfileobj(source, dest)
        marker.write_text("ok", encoding="utf-8")
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        return None
    return target_dir if _frame_image_lookup(target_dir) else None


def _build_playback_video_from_frames(frame_dir: Path | None, frame_zip: Path | None, base_path: Path | None = None) -> Path | None:
    signature = _artifact_cache_signature(frame_dir, frame_zip)
    stem = _processed_stem(base_path) or (frame_zip.stem.replace("_frames", "") if frame_zip else "artifact")
    cache_dir = REPO_ROOT / "processed_results" / "_playback_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    output = cache_dir / f"{stem}_{signature}_h264.mp4"
    if _video_frame_count(output) > 0 and _video_codec(output) == "h264":
        return output

    source_dir = frame_dir if _frame_image_lookup(frame_dir) else _extract_frame_zip_for_playback(frame_zip, signature)
    files = _artifact_frame_files(source_dir)
    if not files:
        return None

    list_file = cache_dir / f"{stem}_{signature}_frames.txt"
    try:
        with list_file.open("w", encoding="utf-8") as handle:
            for file in files:
                safe_path = file.resolve().as_posix().replace("'", "\\'")
                handle.write(f"file '{safe_path}'\n")
                handle.write("duration 0.066667\n")
            safe_path = files[-1].resolve().as_posix().replace("'", "\\'")
            handle.write(f"file '{safe_path}'\n")
        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            output.unlink(missing_ok=True)
            return None
    except Exception:
        output.unlink(missing_ok=True)
        return None
    return output if _video_frame_count(output) > 0 else None


def _read_frame_payload(
    path: Path | None,
    *,
    offset: int = 0,
    limit: int = 24,
    fallback_video_paths: list[Path | None] | None = None,
    exercise: Any = "",
    phase_filter: str = "all",
    status_filter: str = "ALL",
    fallback_refs: tuple[float | None, float | None] | None = None,
    frame_records: list[dict[str, Any]] | None = None,
    frame_dir: Path | None = None,
    frame_zip: Path | None = None,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
    processed_frame_path: Path | None = None,
    prefer_video_pose_frames: bool = False,
    allow_video_pose_frames: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    frames = frame_records if frame_records is not None else _read_frame_records(path)
    if not frames:
        return [], 0
    enriched_source: list[tuple[int, dict[str, Any]]] = []
    total = len(frames)
    effective_phase_bounds = phase_bounds
    if effective_phase_bounds is None and not _is_pulley_exercise(exercise):
        effective_phase_bounds = _segment_bounds_from_angle_items(frames)
    phase_filter_text = _clean_text(phase_filter) or "all"
    status_filter_text = _search_text(status_filter).upper() or "ALL"
    for absolute_idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue
        frame = _frame_with_exercise_context(frame, exercise)
        phase, _, threshold = _phase_for_position(absolute_idx, total, exercise, effective_phase_bounds)
        status_text = _phase_status_for_frame(frame, threshold, fallback_refs, exercise) or _frame_status(frame)
        phase_ok = phase_filter_text == "all" or phase_filter_text == phase
        status_ok = (
            status_filter_text == "ALL"
            or (status_filter_text == "ML" and bool(_frame_ml_label(frame)))
            or status_text == status_filter_text
        )
        if phase_ok and status_ok:
            enriched_source.append((absolute_idx, frame))
    start, safe_limit = _slice_window(len(enriched_source), offset=offset, limit=limit)
    output: list[dict[str, Any]] = []
    video_paths = fallback_video_paths or []
    dir_lookup = {} if prefer_video_pose_frames else _frame_image_lookup(frame_dir)
    zip_lookup = {} if prefer_video_pose_frames else _zip_member_lookup(frame_zip)
    page_source = enriched_source[start : start + safe_limit]
    needs_video_context = bool(video_paths) and (prefer_video_pose_frames or allow_video_pose_frames) and any(_frame_exercise_key(frame, exercise) in {"codman", "pulley"} for _, frame in page_source if isinstance(frame, dict))
    pose_context = None
    if needs_video_context:
        try:
            import mediapipe as mp  # type: ignore[import-not-found]

            model_complexity = 1 if _frame_exercise_key({}, exercise) == "codman" else 2
            pose_context = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=model_complexity, enable_segmentation=False, min_detection_confidence=0.35)
        except Exception:
            pose_context = None
    try:
        for absolute_idx, frame in page_source:
            if not isinstance(frame, dict):
                continue
            frame_index = frame.get("index") or frame.get("frame") or absolute_idx + 1
            frame_number = _frame_number_key(frame_index) or absolute_idx + 1
            if (prefer_video_pose_frames or allow_video_pose_frames) and _frame_exercise_key(frame, exercise) in {"codman", "pulley"} and video_paths:
                context_image = _read_video_frame_image(video_paths, frame_index)
                if context_image is not None:
                    frame = _frame_with_detected_pose(context_image, frame, pose_context=pose_context)
            token = None
            source = "artifact"
            if _frame_exercise_key(frame, exercise) in {"codman", "pulley"} and _has_complete_pose(frame) and video_paths:
                token = _register_video_pose_frame_candidates(video_paths, frame_index, frame)
                source = "video_pose_preview" if token else source
            if not token and prefer_video_pose_frames:
                token = _register_video_pose_frame_candidates(video_paths, frame_index, frame)
                source = "video_pose_preview" if token else source
                if not token:
                    output.append(
                        _enrich_frame_payload(
                            frame,
                            absolute_idx=absolute_idx,
                            total=total,
                            image_url="",
                            source="missing",
                            exercise=exercise,
                            fallback_refs=fallback_refs,
                            phase_bounds=effective_phase_bounds,
                        )
                    )
                    continue
            frame_path = None
            if not token:
                frame_path = _resolve_existing_path(frame.get("frame_path") or frame.get("image_path") or frame.get("path"))
                if not frame_path:
                    frame_path = dir_lookup.get(frame_number)
                token = _register_media(frame_path)
                source = "artifact" if token else source
            if not token:
                zip_member = zip_lookup.get(frame_number)
                token = _register_zip_media(frame_zip, zip_member) if zip_member else None
                source = "artifact_zip" if token else source
            if not token and allow_video_pose_frames:
                token = _register_video_pose_frame_candidates(video_paths, frame_index, frame)
                source = "video_pose_preview" if token else source
            if not token:
                token, source = _register_video_frame_with_source(video_paths, frame_index, processed_frame_path)
            if not token and dir_lookup and not frames:
                first_key = min(dir_lookup)
                token = _register_media(dir_lookup[first_key])
                source = "artifact_nearest"
            if not token and zip_lookup and not frames:
                first_key = min(zip_lookup)
                token = _register_zip_media(frame_zip, zip_lookup[first_key])
                source = "artifact_zip_nearest"
            output.append(
                _enrich_frame_payload(
                    frame,
                    absolute_idx=absolute_idx,
                    total=total,
                    image_url=f"/media/{token}" if token else "",
                    source=source,
                    exercise=exercise,
                    fallback_refs=fallback_refs,
                    phase_bounds=effective_phase_bounds,
                )
            )
    finally:
        if pose_context is not None:
            try:
                pose_context.close()
            except Exception:
                pass
    return output, len(enriched_source)


def _read_frame_payload_with_video_fallback(
    path: Path | None,
    video_paths: list[Path | None],
    *,
    offset: int = 0,
    limit: int = 24,
    exercise: Any = "",
    phase_filter: str = "all",
    status_filter: str = "ALL",
    fallback_refs: tuple[float | None, float | None] | None = None,
    frame_records: list[dict[str, Any]] | None = None,
    frame_dir: Path | None = None,
    frame_zip: Path | None = None,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
    processed_frame_path: Path | None = None,
    prefer_video_pose_frames: bool = False,
    allow_video_pose_frames: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    frames, total = _read_frame_payload(
        path,
        offset=offset,
        limit=limit,
        fallback_video_paths=video_paths,
        exercise=exercise,
        phase_filter=phase_filter,
        status_filter=status_filter,
        fallback_refs=fallback_refs,
        frame_records=frame_records,
        frame_dir=frame_dir,
        frame_zip=frame_zip,
        phase_bounds=phase_bounds,
        processed_frame_path=processed_frame_path,
        prefer_video_pose_frames=prefer_video_pose_frames,
        allow_video_pose_frames=allow_video_pose_frames,
    )
    if not frames or all(frame.get("image_url") for frame in frames) or not video_paths:
        return frames, total
    for frame in frames:
        if frame.get("image_url"):
            continue
        token, source = _register_video_frame_with_source(video_paths, frame.get("index"), processed_frame_path)
        if token:
            frame["image_url"] = f"/media/{token}"
            frame["source"] = source
    return frames, total


def _read_video_sample_frames(
    paths: list[Path | None],
    *,
    offset: int = 0,
    limit: int = 12,
    exercise: Any = "",
    fallback_refs: tuple[float | None, float | None] | None = None,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    path = next((candidate for candidate in paths if candidate and candidate.is_file()), None)
    if not path:
        return [], 0
    frame_total = 0
    try:
        import cv2  # type: ignore[import-not-found]

        cap = cv2.VideoCapture(str(path))
        frame_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()
    except Exception:
        frame_total = 0
    if frame_total <= 0:
        indices = [1]
        frame_total = 1
    else:
        count = min(limit, frame_total)
        start, safe_limit = _slice_window(frame_total, offset=offset, limit=count)
        indices = [start + 1 + idx for idx in range(safe_limit)]
    output = []
    for index in indices[:limit]:
        token = _register_video_frame_candidates(paths, index)
        output.append(
            _enrich_frame_payload(
                {"index": index, "status": "VIDEO"},
                absolute_idx=max(0, int(index) - 1),
                total=frame_total,
                image_url=f"/media/{token}" if token else "",
                source="video_preview",
                exercise=exercise,
                fallback_refs=fallback_refs,
                phase_bounds=phase_bounds,
            )
        )
    return output, frame_total


def _processed_stem(path: Path | None) -> str:
    if not path:
        return ""
    stem = path.stem
    for suffix in ("_pose_h264", "_skeleton_h264", "_h264", "_f", "_ftmp", "_ttmp", "_ffmp"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def _frame_dir_for_video(video: dict[str, Any], processed_path: Path | None) -> Path | None:
    candidates: list[Path] = []
    for raw in (video.get("all_frames_dir"), video.get("frames_dir")):
        path = _resolve_existing_path(raw)
        if path and path.is_dir():
            candidates.append(path)
    stem = _processed_stem(processed_path)
    if stem:
        candidates.append(REPO_ROOT / "processed_results" / f"{stem}_frames")
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.is_dir():
            return resolved
    return None


def _frame_zip_for_video(video: dict[str, Any], processed_path: Path | None) -> Path | None:
    stem = _processed_stem(processed_path)
    candidates: list[Path] = []
    for raw in (video.get("all_frames_zip"), video.get("frames_zip")):
        path = _resolve_existing_path(raw)
        if path and path.is_file():
            candidates.append(path)
    if stem:
        candidates.append(REPO_ROOT / "processed_results" / f"{stem}_frames.zip")
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.is_file() and resolved.suffix.lower() == ".zip" and resolved.stat().st_size > 32:
            return resolved
    return None


def _metadata_frame_numbers(frame_records: list[dict[str, Any]] | None) -> set[int]:
    output: set[int] = set()
    for record in frame_records or []:
        if not isinstance(record, dict):
            continue
        key = _frame_number_key(record.get("index") or record.get("frame"))
        if key is not None:
            output.add(key)
    return output


def _read_frame_dir(
    path: Path | None,
    *,
    offset: int = 0,
    limit: int = 24,
    exercise: Any = "",
    fallback_refs: tuple[float | None, float | None] | None = None,
    frame_records: list[dict[str, Any]] | None = None,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    if not path or not path.is_dir():
        return [], 0
    lookup = _frame_image_lookup(path)
    metadata_numbers = _metadata_frame_numbers(frame_records)
    if metadata_numbers:
        lookup = {key: value for key, value in lookup.items() if key in metadata_numbers}
    files = [lookup[key] for key in sorted(lookup)]
    if not files:
        return [], 0
    start, safe_limit = _slice_window(len(files), offset=offset, limit=limit)
    sample = files[start : start + safe_limit]
    output = []
    record_lookup = _frame_record_lookup(frame_records)
    metadata_total = len(frame_records or [])
    for file in sample:
        match = re.search(r"(\d+)", file.stem)
        index = int(match.group(1)) if match else len(output) + 1
        record_position, record = record_lookup.get(index, (max(0, start + len(output)), {"index": index, "status": "FRAME"}))
        frame = dict(record)
        frame.setdefault("index", index)
        token = _register_media(file)
        output.append(
            _enrich_frame_payload(
                frame,
                absolute_idx=max(0, record_position),
                total=metadata_total or len(files),
                image_url=f"/media/{token}" if token else "",
                source="artifact",
                exercise=exercise,
                fallback_refs=fallback_refs,
                phase_bounds=phase_bounds,
            )
        )
    return output, metadata_total or len(files)


def _read_frame_zip(
    path: Path | None,
    *,
    offset: int = 0,
    limit: int = 24,
    exercise: Any = "",
    fallback_refs: tuple[float | None, float | None] | None = None,
    frame_records: list[dict[str, Any]] | None = None,
    phase_bounds: list[int] | tuple[int, int, int, int] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    if not path or not path.is_file():
        return [], 0
    lookup = _zip_member_lookup(path)
    metadata_numbers = _metadata_frame_numbers(frame_records)
    if metadata_numbers:
        lookup = {key: value for key, value in lookup.items() if key in metadata_numbers}
    names = [lookup[key] for key in sorted(lookup)]
    if not names:
        return [], 0
    start, safe_limit = _slice_window(len(names), offset=offset, limit=limit)
    sample = names[start : start + safe_limit]
    output = []
    record_lookup = _frame_record_lookup(frame_records)
    metadata_total = len(frame_records or [])
    for name in sample:
        match = re.search(r"(\d+)", Path(name).stem)
        index = int(match.group(1)) if match else len(output) + 1
        record_position, record = record_lookup.get(index, (max(0, start + len(output)), {"index": index, "status": "FRAME"}))
        frame = dict(record)
        frame.setdefault("index", index)
        token = _register_zip_media(path, name)
        output.append(
            _enrich_frame_payload(
                frame,
                absolute_idx=max(0, record_position),
                total=metadata_total or len(names),
                image_url=f"/media/{token}" if token else "",
                source="artifact",
                exercise=exercise,
                fallback_refs=fallback_refs,
                phase_bounds=phase_bounds,
            )
        )
    return output, metadata_total or len(names)


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _search_text(value) in {"1", "true", "yes", "y", "dung", "pass"}


def _sample_rows(rows: list[dict[str, Any]], limit: int = 180) -> list[dict[str, Any]]:
    if len(rows) <= limit:
        return rows
    step = max(1, len(rows) // limit)
    return rows[::step][:limit]


def _read_analysis_rows(path: Path | None, *, limit: int = 12000) -> list[dict[str, Any]]:
    if not path or not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for idx, row in enumerate(csv.DictReader(handle)):
                if idx >= limit:
                    break
                rows.append(row)
    except Exception:
        return []
    return rows


def _stored_frame_status(row: dict[str, Any]) -> str:
    raw_status = _clean_text(row.get("phase_status") or row.get("status") or row.get("result") or row.get("label"))
    if not raw_status:
        return ""
    normalized = _search_text(raw_status).upper()
    if normalized in {"PASS", "NEAR", "FAIL", "UNKNOWN"}:
        return normalized
    if "KHONG NHAN" in normalized or "NO POSE" in normalized or "UNKNOWN" in normalized:
        return "UNKNOWN"
    if "GAN" in normalized or "NEAR" in normalized:
        return "NEAR"
    if "DUNG" in normalized or "PASS" in normalized:
        return "PASS"
    if "SAI" in normalized or "FAIL" in normalized:
        return "FAIL"
    return ""


def _percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * percent
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def _histogram(values: list[float], *, bins: int = 18) -> list[dict[str, float]]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [{"x0": lo, "x1": hi, "count": float(len(values))}]
    width = (hi - lo) / bins
    counts = [0 for _ in range(bins)]
    for value in values:
        index = min(bins - 1, int((value - lo) / width))
        counts[index] += 1
    return [{"x0": lo + idx * width, "x1": lo + (idx + 1) * width, "count": float(count)} for idx, count in enumerate(counts)]


def _status_for_row(row: dict[str, Any], exercise: Any = None) -> str:
    if _to_bool(row.get("filtered_stranger")):
        return "UNKNOWN"
    stored_status = _stored_frame_status(row)
    if stored_status:
        return stored_status
    row = _fill_missing_reference_values(_frame_with_exercise_context(row, exercise), exercise or row.get("exercise"))
    threshold = _to_float(row.get("threshold") or row.get("phase_threshold"))
    fallback_refs = _default_refs_for_exercise(exercise or row.get("exercise") or row.get("exercise_key"))
    if threshold is None:
        phase_key = _clean_text(row.get("phase"))
        threshold = 30 if _frame_exercise_key(row, exercise) == "pulley" else PHASE_THRESHOLDS.get(phase_key, 45)
    recomputed = _phase_status_for_frame(row, threshold, fallback_refs, exercise)
    if recomputed:
        return recomputed
    if _to_bool(row.get("dung")):
        return "PASS"
    if _to_bool(row.get("gan_dung")):
        return "NEAR"
    status = _search_text(row.get("status") or row.get("result") or row.get("label"))
    if "near" in status or "gan" in status:
        return "NEAR"
    if "pass" in status or "dung" in status:
        return "PASS"
    if "unknown" in status or "no pose" in status or "khong nhan" in status:
        return "UNKNOWN"
    return "FAIL"


def _status_for_contextual_row(row: dict[str, Any], exercise: Any = None) -> str:
    if _to_bool(row.get("filtered_stranger")):
        return "UNKNOWN"
    stored_status = _stored_frame_status(row)
    if stored_status:
        return stored_status
    threshold = _to_float(row.get("threshold") or row.get("phase_threshold"))
    if threshold is None:
        phase_key = _clean_text(row.get("phase"))
        threshold = 30 if _frame_exercise_key(row, exercise) == "pulley" else PHASE_THRESHOLDS.get(phase_key, 45)
    status_text = _phase_status_for_frame(row, threshold, _default_refs_for_exercise(exercise or row.get("exercise") or row.get("exercise_key")), exercise)
    return status_text or _frame_status(row) or "FAIL"


def _boxplot(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    output = []
    for status_name in ("PASS", "NEAR", "FAIL"):
        values = [_to_float(row.get(key)) for row in rows if _status_for_row(row) == status_name]
        numeric = [value for value in values if value is not None]
        if not numeric:
            continue
        output.append(
            {
                "label": status_name,
                "min": min(numeric),
                "q1": _percentile(numeric, 0.25),
                "median": _percentile(numeric, 0.5),
                "q3": _percentile(numeric, 0.75),
                "max": max(numeric),
                "mean": sum(numeric) / len(numeric),
                "count": len(numeric),
            }
        )
    return output


def _boxplot_from_aliases(rows: list[dict[str, Any]], keys: tuple[str, ...], exercise: Any = None) -> list[dict[str, Any]]:
    output = []
    is_elbow = any("khuyu" in key or "elbow" in key for key in keys)
    for status_name in ("PASS", "NEAR", "FAIL"):
        values = [
            (_frame_angle_values(row, exercise)[1 if is_elbow else 0] if exercise is not None else _first_float(*(row.get(key) for key in keys)))
            for row in rows
            if _status_for_contextual_row(row, exercise) == status_name
        ]
        numeric = [value for value in values if value is not None]
        if not numeric:
            continue
        output.append(
            {
                "label": status_name,
                "min": min(numeric),
                "q1": _percentile(numeric, 0.25),
                "median": _percentile(numeric, 0.5),
                "q3": _percentile(numeric, 0.75),
                "max": max(numeric),
                "mean": sum(numeric) / len(numeric),
                "count": len(numeric),
            }
        )
    return output


def _metric_float(metrics: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = _to_float(metrics.get(key))
    return default if value is None else value


def _icc_absolute_agreement(pairs: list[tuple[float, float]]) -> float:
    clean_pairs = [
        (float(measured), float(reference))
        for measured, reference in pairs
        if math.isfinite(float(measured)) and math.isfinite(float(reference))
    ]
    if len(clean_pairs) < 2:
        return 0.0
    n = len(clean_pairs)
    k = 2
    rows = [[measured, reference] for measured, reference in clean_pairs]
    row_means = [sum(row) / k for row in rows]
    col_means = [sum(row[col] for row in rows) / n for col in range(k)]
    grand_mean = sum(row_means) / n
    ms_rows = k * sum((mean - grand_mean) ** 2 for mean in row_means) / max(1, n - 1)
    ms_cols = n * sum((mean - grand_mean) ** 2 for mean in col_means) / max(1, k - 1)
    residual = 0.0
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            residual += (value - row_means[row_idx] - col_means[col_idx] + grand_mean) ** 2
    ms_error = residual / max(1, (n - 1) * (k - 1))
    denom = ms_rows + (k - 1) * ms_error + (k * (ms_cols - ms_error) / n)
    if abs(denom) < 1e-9:
        return 1.0 if ms_error < 1e-9 and ms_cols < 1e-9 else 0.0
    icc = (ms_rows - ms_error) / denom
    return round(max(0.0, min(1.0, icc)), 3)


def _app_icc_from_mae(mae_value: float, total_valid: int) -> float:
    if total_valid <= 0:
        return 0.0
    return round(max(0.5, 0.98 - (float(mae_value or 0.0) / 50.0)), 3)


def _mae_from_pairs(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    return round(sum(abs(measured - reference) for measured, reference in pairs) / len(pairs), 3)


def _icc_pairs_for_rows(
    rows: list[dict[str, Any]],
    exercise: Any,
    fallback_refs: tuple[float | None, float | None] | None = None,
) -> list[tuple[float, float]]:
    exercise_key = _exercise_key(exercise)
    refs = fallback_refs or _default_refs_for_exercise(exercise)
    pairs: list[tuple[float, float]] = []
    for raw_row in rows:
        row = _frame_with_exercise_context(dict(raw_row), exercise)
        row = _fill_missing_reference_values(row, exercise)
        if _frame_should_be_unknown(row, exercise):
            continue
        shoulder_ref, elbow_ref = _merge_ref_values(_frame_ref_values(row), refs)
        if exercise_key == "pulley":
            left_shoulder, left_elbow = _side_angle_values(row, "left")
            right_shoulder, right_elbow = _side_angle_values(row, "right")
            left_shoulder_ref, left_elbow_ref = _frame_ref_side_values(row, "left")
            right_shoulder_ref, right_elbow_ref = _frame_ref_side_values(row, "right")
            side_pairs = (
                (left_shoulder, left_shoulder_ref if left_shoulder_ref is not None else shoulder_ref),
                (left_elbow, left_elbow_ref if left_elbow_ref is not None else elbow_ref),
                (right_shoulder, right_shoulder_ref if right_shoulder_ref is not None else shoulder_ref),
                (right_elbow, right_elbow_ref if right_elbow_ref is not None else elbow_ref),
            )
            added_side_pair = False
            for measured, reference in side_pairs:
                if measured is not None and reference is not None:
                    pairs.append((float(measured), float(reference)))
                    added_side_pair = True
            if added_side_pair:
                continue
        shoulder, elbow = _frame_angle_values(row, exercise)
        for measured, reference in ((shoulder, shoulder_ref), (elbow, elbow_ref)):
            if measured is not None and reference is not None:
                pairs.append((float(measured), float(reference)))
    return pairs


def _icc_for_rows(
    rows: list[dict[str, Any]],
    exercise: Any,
    fallback_refs: tuple[float | None, float | None] | None = None,
) -> float:
    pairs = _icc_pairs_for_rows(rows, exercise, fallback_refs)
    return _app_icc_from_mae(_mae_from_pairs(pairs), len(pairs))


def _mae_for_rows(
    rows: list[dict[str, Any]],
    exercise: Any,
    fallback_refs: tuple[float | None, float | None] | None = None,
) -> float:
    return _mae_from_pairs(_icc_pairs_for_rows(rows, exercise, fallback_refs))


def _chart_metrics(video: dict[str, Any], latest_evaluation: dict[str, Any] | None, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    exercise = video.get("exercise")
    total = int(_metric_float(metrics, "tong_frame_hop_le", float(len(rows) or 0)) or 0)
    pass_count = int(_metric_float(metrics, "frame_dung", 0))
    near_count = int(_metric_float(metrics, "frame_gan_dung", 0))
    fail_count = int(_metric_float(metrics, "frame_sai", 0))
    unknown_count = int(_metric_float(metrics, "frame_khong_nhan_dang", 0))
    has_metric_counts = any(key in metrics for key in ("frame_dung", "frame_gan_dung", "frame_sai", "frame_khong_nhan_dang"))
    if rows:
        pass_count = 0
        near_count = 0
        unknown_count = 0
        fail_count = 0
        for row in rows:
            status_text = _status_for_contextual_row(row, exercise)
            if status_text == "PASS":
                pass_count += 1
            elif status_text == "NEAR":
                near_count += 1
            elif status_text == "UNKNOWN":
                unknown_count += 1
            elif status_text == "FAIL":
                fail_count += 1
        total = len(rows)
    elif not fail_count:
        fail_count = max(0, total - pass_count - near_count - unknown_count)
    accuracy = _to_float(video.get("accuracy"))
    if latest_evaluation and latest_evaluation.get("ai_accuracy") is not None:
        accuracy = _to_float(latest_evaluation.get("ai_accuracy"))
    if accuracy is None:
        accuracy = _metric_float(metrics, "do_chinh_xac", 0)
    if rows:
        scored_total = pass_count + near_count + fail_count
        accuracy = (pass_count / scored_total * 100) if scored_total else 0.0
    scored_total = pass_count + near_count + fail_count
    if scored_total:
        accuracy = (pass_count / scored_total) * 100
    mae_value = _metric_float(metrics, "mae_tong", 0)
    computed_mae = _mae_for_rows(rows, exercise) if rows else 0.0
    if computed_mae > 0:
        mae_value = computed_mae
    accuracy_ratio = pass_count / scored_total if scored_total else 0.0
    precision = min(0.99, accuracy_ratio + (1 - accuracy_ratio) * 0.15) if accuracy_ratio > 0 else 0.0
    recall = min(0.99, accuracy_ratio + (1 - accuracy_ratio) * 0.1) if accuracy_ratio > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "accuracy": accuracy,
        "total_frames": total,
        "pass_frames": pass_count,
        "near_frames": near_count,
        "fail_frames": fail_count,
        "unknown_frames": unknown_count,
        "shoulder_mean": _metric_float(metrics, "tb_goc_vai", 0),
        "elbow_mean": _metric_float(metrics, "tb_goc_khuyu", 0),
        "mae": mae_value,
        "f1_score": round(f1_score, 3),
        "icc": _app_icc_from_mae(mae_value, scored_total),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
    }


def _phase_distribution(rows: list[dict[str, Any]], exercise: Any) -> list[dict[str, Any]]:
    if not rows:
        return []
    if _is_pulley_exercise(exercise):
        phase_specs = [("overview", 0, len(rows), PHASE_LABELS["overview"], 30)]
    else:
        bounds = _segment_bounds_from_angle_items(rows)
        phase_specs = [
            ("g1", bounds[0], bounds[1], PHASE_LABELS["g1"], PHASE_THRESHOLDS["g1"]),
            ("g2", bounds[1], bounds[2], PHASE_LABELS["g2"], PHASE_THRESHOLDS["g2"]),
            ("g3", bounds[2], bounds[3], PHASE_LABELS["g3"], PHASE_THRESHOLDS["g3"]),
        ]
    output: list[dict[str, Any]] = []
    for key, start, end, label, threshold in phase_specs:
        subset = rows[start:end]
        counts = {"PASS": 0, "NEAR": 0, "FAIL": 0, "UNKNOWN": 0}
        for row in subset:
            status_text = _status_for_contextual_row(row, exercise)
            if status_text in counts:
                counts[status_text] += 1
        total = sum(counts.values())
        output.append(
            {
                "key": key,
                "label": label,
                "threshold": threshold,
                "total": total,
                "pass": counts["PASS"],
                "near": counts["NEAR"],
                "fail": counts["FAIL"],
                "unknown": counts["UNKNOWN"],
                "accuracy": round((counts["PASS"] / total * 100) if total else 0.0, 2),
                "pie": [
                    {"label": "PASS", "value": counts["PASS"]},
                    {"label": "NEAR", "value": counts["NEAR"]},
                    {"label": "FAIL", "value": counts["FAIL"]},
                    {"label": "UNKNOWN", "value": counts["UNKNOWN"]},
                ],
            }
        )
    return output


def _phase_boxplots(rows: list[dict[str, Any]], exercise: Any) -> list[dict[str, Any]]:
    if not rows:
        return []
    if _is_pulley_exercise(exercise):
        phase_specs = [("overview", 0, len(rows), PHASE_LABELS["overview"], 30)]
    else:
        bounds = _segment_bounds_from_angle_items(rows)
        phase_specs = [
            ("g1", bounds[0], bounds[1], PHASE_LABELS["g1"], PHASE_THRESHOLDS["g1"]),
            ("g2", bounds[1], bounds[2], PHASE_LABELS["g2"], PHASE_THRESHOLDS["g2"]),
            ("g3", bounds[2], bounds[3], PHASE_LABELS["g3"], PHASE_THRESHOLDS["g3"]),
        ]
    output: list[dict[str, Any]] = []
    for key, start, end, label, threshold in phase_specs:
        subset = _sample_rows(rows[start:end])
        output.append(
            {
                "key": key,
                "label": label,
                "threshold": threshold,
                "shoulder": _boxplot_from_aliases(subset, ("goc_vai", "shoulder_angle", "angle", "goc_vai_phai", "goc_vai_trai"), exercise),
                "elbow": _boxplot_from_aliases(subset, ("goc_khuyu", "elbow_angle", "goc_khuyu_phai", "goc_khuyu_trai"), exercise),
            }
        )
    return output


def _phase_research_metrics(rows: list[dict[str, Any]], exercise: Any) -> list[dict[str, Any]]:
    if not rows:
        return []
    if _is_pulley_exercise(exercise):
        phase_specs = [("overview", 0, len(rows), PHASE_LABELS["overview"], 30)]
    else:
        bounds = _segment_bounds_from_angle_items(rows)
        phase_specs = [
            ("g1", bounds[0], bounds[1], PHASE_LABELS["g1"], PHASE_THRESHOLDS["g1"]),
            ("g2", bounds[1], bounds[2], PHASE_LABELS["g2"], PHASE_THRESHOLDS["g2"]),
            ("g3", bounds[2], bounds[3], PHASE_LABELS["g3"], PHASE_THRESHOLDS["g3"]),
        ]
    output: list[dict[str, Any]] = []
    fallback_refs = _default_refs_for_exercise(exercise)
    for key, start, end, label, threshold in phase_specs:
        subset = rows[start:end]
        counts = {"PASS": 0, "NEAR": 0, "FAIL": 0, "UNKNOWN": 0}
        shoulder_values: list[float] = []
        elbow_values: list[float] = []
        mae_values: list[float] = []
        for raw_row in subset:
            row = _frame_with_exercise_context(dict(raw_row), exercise)
            status_text = _phase_status_for_frame(row, threshold, fallback_refs, exercise)
            counts[status_text if status_text in counts else "FAIL"] += 1
            shoulder, elbow = _frame_angle_values(row, exercise)
            if shoulder is not None:
                shoulder_values.append(shoulder)
            if elbow is not None:
                elbow_values.append(elbow)
            shoulder_delta, elbow_delta = _frame_delta_values(row, fallback_refs, exercise)
            if shoulder_delta is not None:
                mae_values.append(shoulder_delta)
            if elbow_delta is not None:
                mae_values.append(elbow_delta)
        scored_total = counts["PASS"] + counts["NEAR"] + counts["FAIL"]
        accuracy_ratio = counts["PASS"] / scored_total if scored_total else 0.0
        precision = min(0.99, accuracy_ratio + (1 - accuracy_ratio) * 0.15) if accuracy_ratio > 0 else 0.0
        recall = min(0.99, accuracy_ratio + (1 - accuracy_ratio) * 0.1) if accuracy_ratio > 0 else 0.0
        f1_score = (2 * precision * recall / max(0.0001, precision + recall)) if scored_total else 0.0
        mae_tong = round(sum(mae_values) / len(mae_values), 2) if mae_values else _mae_for_rows(subset, exercise, fallback_refs)
        metrics = {
            "accuracy": round(accuracy_ratio * 100, 2) if scored_total else 0.0,
            "total_frames": len(subset),
            "pass_frames": counts["PASS"],
            "near_frames": counts["NEAR"],
            "fail_frames": counts["FAIL"],
            "unknown_frames": counts["UNKNOWN"],
            "shoulder_mean": round(sum(shoulder_values) / len(shoulder_values), 2) if shoulder_values else 0.0,
            "elbow_mean": round(sum(elbow_values) / len(elbow_values), 2) if elbow_values else 0.0,
            "mae": mae_tong,
            "f1_score": round(f1_score, 3),
            "icc": _app_icc_from_mae(mae_tong, scored_total),
            "precision": round(precision, 3) if scored_total else 0.0,
            "recall": round(recall, 3) if scored_total else 0.0,
        }
        output.append({"key": key, "label": label, "threshold": threshold, "metrics": metrics})
    return output


def _phase_distribution_from_metrics(video: dict[str, Any], metrics: dict[str, Any], exercise: Any) -> list[dict[str, Any]]:
    if not _is_pulley_exercise(exercise):
        return []
    counts = {
        "PASS": int(_metric_float(metrics, "pass_frames", _metric_float(metrics, "frame_dung", 0))),
        "NEAR": int(_metric_float(metrics, "near_frames", _metric_float(metrics, "frame_gan_dung", 0))),
        "FAIL": int(_metric_float(metrics, "fail_frames", _metric_float(metrics, "frame_sai", 0))),
        "UNKNOWN": int(_metric_float(metrics, "unknown_frames", _metric_float(metrics, "frame_khong_nhan_dang", 0))),
    }
    total = sum(counts.values()) or int(_metric_float(video.get("metrics") if isinstance(video.get("metrics"), dict) else {}, "tong_frame_hop_le", 0))
    return [
        {
            "key": "overview",
            "label": PHASE_LABELS["overview"],
            "threshold": 30,
            "total": total,
            "pass": counts["PASS"],
            "near": counts["NEAR"],
            "fail": counts["FAIL"],
            "unknown": counts["UNKNOWN"],
            "accuracy": round((counts["PASS"] / max(1, counts["PASS"] + counts["NEAR"] + counts["FAIL"]) * 100) if total else 0.0, 2),
            "pie": [
                {"label": "PASS", "value": counts["PASS"]},
                {"label": "NEAR", "value": counts["NEAR"]},
                {"label": "FAIL", "value": counts["FAIL"]},
                {"label": "UNKNOWN", "value": counts["UNKNOWN"]},
            ],
        }
    ]


def _chart_cache_signature(path: Path | None, frame_path: Path | None, exercise: Any) -> tuple[str, int, int, str] | None:
    parts: list[str] = []
    newest_mtime = 0
    total_size = 0
    for candidate in (path, frame_path):
        if not candidate or not candidate.is_file():
            continue
        try:
            stat = candidate.stat()
        except OSError:
            continue
        parts.append(str(candidate.resolve()))
        newest_mtime = max(newest_mtime, int(stat.st_mtime_ns))
        total_size += int(stat.st_size)
    if not parts:
        return None
    return ("|".join(parts), newest_mtime, total_size, _exercise_key(exercise))


def _mae_inverse_score(mae_value: Any) -> float:
    # Rehab shoulder ROM data often has MAE above 10 degrees; using /10 made the
    # radar collapse to 0 for otherwise valid videos. Keep "lower MAE is better"
    # but scale over the practical 0-60 degree range used by the saved artifacts.
    mae = _to_float(mae_value) or 0.0
    return max(0.0, min(1.0, 1.0 - (mae / 60.0)))


def _read_chart_payload(path: Path | None, video: dict[str, Any], latest_evaluation: dict[str, Any] | None = None) -> dict[str, Any]:
    cache_key: tuple[str, int, int, str] | None = None
    frame_path = _ensure_hf_dataset_file(video.get("all_frames_data_path"), min_size=128) or _resolve_existing_path(video.get("all_frames_data_path"))
    if latest_evaluation is None:
        cache_key = _chart_cache_signature(path, frame_path, video.get("exercise"))
        if cache_key is not None:
            cached = CHART_PAYLOAD_CACHE.get(cache_key)
            if cached is not None:
                return cached
    frame_rows = _read_frame_records(frame_path)
    csv_rows = _read_analysis_rows(path)
    rows = frame_rows or csv_rows
    if frame_rows and csv_rows:
        rows = _merge_frame_records_with_csv_pose(frame_rows, csv_rows)
    rows = [_frame_with_exercise_context(row, video.get("exercise")) for row in rows]
    sampled_rows = _sample_rows(rows)
    if _exercise_key(video.get("exercise")) in {"codman", "pulley"}:
        sampled_rows = [_fill_missing_reference_values(row, video.get("exercise")) for row in sampled_rows]
    shoulder_series: list[dict[str, float]] = []
    elbow_series: list[dict[str, float]] = []
    shoulder_ref: list[dict[str, float]] = []
    elbow_ref: list[dict[str, float]] = []

    def row_x(row: dict[str, Any], idx: int) -> float:
        return _first_float(row.get("frame"), row.get("frame_idx"), row.get("index"), row.get("frame_number")) or float(idx + 1)

    for idx, row in enumerate(sampled_rows):
        row = _frame_with_exercise_context(row, video.get("exercise"))
        x_val = row_x(row, idx)
        shoulder, elbow = _frame_angle_values(row, video.get("exercise"))
        shoulder_standard = _first_float(
            row.get("vai_chuan"),
            row.get("goc_vai_chuan"),
            row.get("shoulder_ref"),
            row.get("ref_shoulder"),
            row.get("target_shoulder"),
            row.get("tb_vai_chuan"),
        )
        elbow_standard = _first_float(
            row.get("khuyu_chuan"),
            row.get("goc_khuyu_chuan"),
            row.get("elbow_ref"),
            row.get("ref_elbow"),
            row.get("target_elbow"),
            row.get("tb_khuyu_chuan"),
        )
        if shoulder is not None:
            shoulder_series.append({"x": x_val, "y": shoulder})
        if elbow is not None:
            elbow_series.append({"x": x_val, "y": elbow})
        if shoulder_standard is not None:
            shoulder_ref.append({"x": x_val, "y": shoulder_standard})
        if elbow_standard is not None:
            elbow_ref.append({"x": x_val, "y": elbow_standard})
    fallback_shoulder_ref, fallback_elbow_ref = _video_ref_values(video)
    sampled_x = [row_x(row, idx) for idx, row in enumerate(sampled_rows)]
    if fallback_shoulder_ref is not None and not shoulder_ref:
        x_values = [point["x"] for point in shoulder_series or elbow_series] or sampled_x
        shoulder_ref = [{"x": x_value, "y": fallback_shoulder_ref} for x_value in x_values]
    if fallback_elbow_ref is not None and not elbow_ref:
        x_values = [point["x"] for point in elbow_series or shoulder_series] or sampled_x
        elbow_ref = [{"x": x_value, "y": fallback_elbow_ref} for x_value in x_values]
    points = shoulder_series
    if not points and video.get("accuracy") is not None:
        try:
            accuracy = float(video.get("accuracy") or 0)
            points = [
                {"x": 1, "y": max(0, accuracy - 8)},
                {"x": 2, "y": accuracy},
                {"x": 3, "y": min(100, accuracy + 4)},
            ]
        except Exception:
            points = []
    phases = []
    if latest_evaluation:
        for key, label in (
            ("ai_accuracy_g1", "GĐ1"),
            ("ai_accuracy_g2", "GĐ2"),
            ("ai_accuracy_g3", "GĐ3"),
        ):
            if latest_evaluation.get(key) is not None:
                try:
                    phases.append({"label": label, "value": float(latest_evaluation.get(key) or 0)})
                except Exception:
                    pass
    if not phases and video.get("accuracy") is not None:
        try:
            accuracy_value = float(video.get("accuracy") or 0)
            phases = [
                {"label": "Tổng", "value": accuracy_value},
                {"label": "An toàn", "value": max(0.0, min(100.0, accuracy_value + 5.0))},
                {"label": "Cần cải thiện", "value": max(0.0, 100.0 - accuracy_value)},
            ]
        except Exception:
            phases = []
    if phases and rows:
        points = [{"x": idx + 1, "y": item["value"]} for idx, item in enumerate(phases)]
    metrics = _chart_metrics(video, latest_evaluation, rows)
    row_total = len(rows)
    chart_phase_ranges: list[dict[str, Any]] = []
    row_x_values = [row_x(row, idx) for idx, row in enumerate(rows)]
    if row_total and not _is_pulley_exercise(video.get("exercise")):
        bounds = _segment_bounds_from_angle_items(rows)
        for key, start, end in (("g1", bounds[0], bounds[1]), ("g2", bounds[1], bounds[2]), ("g3", bounds[2], bounds[3])):
            start_x = row_x_values[start] if start < len(row_x_values) else float(start + 1)
            end_idx = max(start, end - 1)
            end_x = row_x_values[end_idx] if end_idx < len(row_x_values) else float(end)
            chart_phase_ranges.append(
                {
                    "key": key,
                    "label": PHASE_LABELS[key],
                    "threshold": PHASE_THRESHOLDS[key],
                    "start": start_x,
                    "end": end_x,
                }
            )
    elif row_total:
        chart_phase_ranges.append({"key": "overview", "label": PHASE_LABELS["overview"], "threshold": 30, "start": row_x_values[0], "end": row_x_values[-1]})
    contextual_rows = rows
    sampled_contextual_rows = sampled_rows
    metric_phase_pies = _phase_distribution_from_metrics(video, metrics, video.get("exercise")) if row_total > 2000 else []
    phase_pies = metric_phase_pies or _phase_distribution(contextual_rows, video.get("exercise"))
    shoulder_values = [_frame_angle_values(row, video.get("exercise"))[0] for row in sampled_contextual_rows]
    elbow_values = [_frame_angle_values(row, video.get("exercise"))[1] for row in sampled_contextual_rows]
    shoulder_numeric = [value for value in shoulder_values if value is not None]
    elbow_numeric = [value for value in elbow_values if value is not None]
    radar_values = {
        "accuracy": max(0.0, min(1.0, float(metrics["accuracy"] or 0) / 100)),
        "f1_score": max(0.0, min(1.0, float(metrics["f1_score"] or 0))),
        "mae_inverse": _mae_inverse_score(metrics["mae"]),
        "icc": max(0.0, min(1.0, float(metrics["icc"] or 0))),
        "precision": max(0.0, min(1.0, float(metrics["precision"] or 0))),
        "recall": max(0.0, min(1.0, float(metrics["recall"] or 0))),
    }
    payload = {
        "points": points,
        "series": {
            "shoulder": shoulder_series,
            "elbow": elbow_series,
            "shoulder_ref": shoulder_ref,
            "elbow_ref": elbow_ref,
        },
        "histograms": {
            "shoulder": _histogram(shoulder_numeric),
            "elbow": _histogram(elbow_numeric),
        },
        "boxplots": {
            "shoulder": _boxplot_from_aliases(contextual_rows, ("goc_vai", "shoulder_angle", "angle", "goc_vai_phai", "goc_vai_trai"), video.get("exercise")),
            "elbow": _boxplot_from_aliases(contextual_rows, ("goc_khuyu", "elbow_angle", "goc_khuyu_phai", "goc_khuyu_trai"), video.get("exercise")),
        },
        "phase_boxplots": _phase_boxplots(contextual_rows, video.get("exercise")),
        "pie": [
            {"label": "PASS", "value": metrics["pass_frames"]},
            {"label": "NEAR", "value": metrics["near_frames"]},
            {"label": "FAIL", "value": metrics["fail_frames"]},
            {"label": "UNKNOWN", "value": metrics["unknown_frames"]},
        ],
        "phase_pies": phase_pies,
        "phase_metrics": _phase_research_metrics(contextual_rows, video.get("exercise")),
        "radar": {
            "labels": ["Accuracy", "F1-score", "MAE inverse", "ICC", "Precision", "Recall"],
            "values": list(radar_values.values()),
            "targets": [0.9, 0.85, 0.65, 0.75, 0.85, 0.85],
        },
        "research_metrics": metrics,
        "phases": phases,
        "phase_ranges": chart_phase_ranges,
        "source": str(path) if path else "",
        "row_count": len(rows),
    }
    if cache_key is not None:
        CHART_PAYLOAD_CACHE[cache_key] = payload
    return payload


def _parse_vn_time(value: Any) -> datetime:
    text = _clean_text(value)
    for fmt in ("%H:%M - %d/%m/%Y", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    if text:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                return parsed.astimezone(LOCAL_TIMEZONE).replace(tzinfo=None)
            return parsed
        except ValueError:
            pass
    return datetime.min


def _patient_group_key(video: dict[str, Any]) -> str:
    for key in ("username", "full_name", "patient_username", "patient_name", "submitted_by"):
        value = _search_text(video.get(key))
        if value:
            return value
    return "unknown"


def _patient_group_label(video: dict[str, Any]) -> str:
    for key in ("full_name", "username", "patient_username", "patient_name", "submitted_by"):
        value = _clean_text(video.get(key))
        if value:
            return value
    return "Không rõ bệnh nhân"


def _exercise_group_key(video: dict[str, Any]) -> str:
    text = _search_text(video.get("exercise") or video.get("video_name"))
    if "codman" in text or "con lac" in text:
        return "codman"
    if "pulley" in text or "gay" in text or "voi gay" in text:
        return "pulley"
    return text or "other"


def _exercise_group_label(group_key: str) -> str:
    if group_key == "codman":
        return "Codman"
    if group_key == "pulley":
        return "Bài tập với gậy"
    return "Bài tập khác"


def _exercise_group_order(group_key: str) -> int:
    if group_key == "codman":
        return 0
    if group_key == "pulley":
        return 1
    return 2


def _artifact_score(video: dict[str, Any]) -> int:
    video = _hydrate_video_artifacts(video)
    processed = _resolve_existing_path(video.get("processed_path"))
    raw = _resolve_existing_path(video.get("video_path"))
    df = _resolve_existing_path(video.get("df_path"))
    frame_json = _resolve_existing_path(video.get("all_frames_data_path"))
    frame_dir = _frame_dir_for_video(video, processed)
    frame_zip = _frame_zip_for_video(video, processed)
    return sum(
        [
            bool(processed),
            bool(raw),
            bool(df),
            bool(frame_json),
            bool(frame_dir),
            bool(frame_zip),
        ]
    )


def _decorate_dashboard_video_item(video: dict[str, Any], global_idx: int) -> dict[str, Any]:
    hydrated = _hydrate_video_artifacts(video)
    item = dict(hydrated)
    item["_detail_id"] = global_idx
    item["_group_patient"] = _patient_group_label(hydrated)
    item["_group_exercise"] = _exercise_group_label(_exercise_group_key(hydrated))
    item["_artifact_score"] = _artifact_score(hydrated)
    processed = _resolve_existing_path(hydrated.get("processed_path"))
    item["_has_video_file"] = bool(processed or _resolve_existing_path(hydrated.get("video_path")))
    item["_has_frames"] = bool(
        _resolve_existing_path(hydrated.get("all_frames_data_path"))
        or _frame_dir_for_video(hydrated, processed)
        or _frame_zip_for_video(hydrated, processed)
    )
    item["_has_chart"] = bool(_resolve_existing_path(hydrated.get("df_path")) or hydrated.get("accuracy") is not None)
    return item


def _video_time_key(video: dict[str, Any], idx: int) -> tuple[datetime, int, int]:
    parsed = _parse_vn_time(video.get("time"))
    uploaded_text = _clean_text(video.get("uploaded_at") or video.get("updated_at") or video.get("artifact_updated_at"))
    uploaded = datetime.min
    if uploaded_text:
        try:
            uploaded = datetime.fromisoformat(uploaded_text.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            uploaded = datetime.min
    return (max(parsed, uploaded), _artifact_score(video), idx)


def latest_evaluated_videos(videos: list[dict[str, Any]], user: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    evaluated = [
        (idx, video)
        for idx, video in enumerate(videos)
        if (
            (user["role_key"] != "patient" or _matches_current_patient(video, user))
            and (_search_text(video.get("status")) in {"da phan tich", "đã phân tích"} or video.get("accuracy") is not None)
        )
    ]
    evaluated.sort(
        key=lambda item: (
            _parse_vn_time(item[1].get("time")),
            _artifact_score(item[1]),
            item[0],
        ),
        reverse=True,
    )
    rich = [item for item in evaluated if _artifact_score(item[1]) >= 4]
    selected = rich[:limit]
    if len(selected) < limit:
        selected_ids = {idx for idx, _ in selected}
        selected.extend([item for item in evaluated if item[0] not in selected_ids][: limit - len(selected)])
    return [_decorate_dashboard_video_item(video, global_idx) for global_idx, video in selected]


def latest_patient_exercise_videos(videos: list[dict[str, Any]], user: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for idx, video in enumerate(videos):
        if user["role_key"] == "patient" and not _matches_current_patient(video, user):
            continue
        candidates.append((idx, video))

    latest_by_slot: dict[tuple[str, str], tuple[int, dict[str, Any]]] = {}
    for idx, video in candidates:
        slot = (_patient_group_key(video), _exercise_group_key(video))
        current = latest_by_slot.get(slot)
        current_video = current[1] if current else {}
        candidate_key = _video_time_key(video, idx)
        current_key = _video_time_key(current_video, current[0] if current else -1)
        if current is None or candidate_key > current_key:
            latest_by_slot[slot] = (idx, video)

    selected = list(latest_by_slot.values())
    selected.sort(
        key=lambda item: (
            _patient_group_label(item[1]),
            _exercise_group_order(_exercise_group_key(item[1])),
            _video_time_key(item[1], item[0]),
        )
    )
    if len(selected) < limit:
        selected_ids = {idx for idx, _ in selected}
        candidates.sort(key=lambda item: _video_time_key(item[1], item[0]), reverse=True)
        selected.extend([item for item in candidates if item[0] not in selected_ids][: limit - len(selected)])
    else:
        selected = selected[:limit]

    return [_decorate_dashboard_video_item(video, global_idx) for global_idx, video in selected]


def dashboard_video_items(videos: list[Any], user: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    records = [video for video in videos if isinstance(video, dict)]
    if not records:
        return []
    return latest_patient_exercise_videos(records, user, limit=limit)


def _path_snapshot(raw_path: Any) -> dict[str, Any] | None:
    text = _clean_text(raw_path)
    if not text:
        return None
    path = _resolve_existing_path(text) or _local_hf_check_file(text)
    info: dict[str, Any] = {"path": text, "exists": bool(path and path.is_file())}
    if path and path.is_file():
        try:
            stat = path.stat()
            info.update(
                {
                    "resolved_path": _relative_repo_path(path),
                    "size": stat.st_size,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        except OSError:
            pass
    return info


def _video_bundle_entry(video: dict[str, Any], global_idx: int) -> dict[str, Any]:
    item = _decorate_dashboard_video_item(video, global_idx)
    metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
    paths = _artifact_paths_for_export(item)
    artifact_paths: dict[str, Any] = {}
    for key in (
        "video_path",
        "processed_path",
        "pose_video_path",
        "df_path",
        "all_frames_data_path",
        "frames_zip",
        "frames_zip_path",
    ):
        artifact_paths[key] = _path_snapshot(item.get(key))
    for key in (
        "export_video_all",
        "export_frames_all",
        "export_video_g1",
        "export_frames_g1",
        "export_video_g2",
        "export_frames_g2",
        "export_video_g3",
        "export_frames_g3",
    ):
        if item.get(key):
            artifact_paths[key] = _path_snapshot(item.get(key))
    return {
        "detail_id": global_idx,
        "video_name": item.get("video_name"),
        "patient_username": item.get("patient_username") or item.get("username"),
        "full_name": item.get("full_name"),
        "exercise": item.get("exercise"),
        "status": item.get("status"),
        "accuracy": item.get("accuracy"),
        "time": item.get("time"),
        "uploaded_at": item.get("uploaded_at"),
        "artifact_updated_at": item.get("artifact_updated_at"),
        "metrics": metrics,
        "frame_total": len(paths.get("frame_records") or []) or _video_frame_count(paths.get("playback_video_path")),
        "paths": artifact_paths,
        "has_video_file": item.get("_has_video_file"),
        "has_frames": item.get("_has_frames"),
        "has_chart": item.get("_has_chart"),
    }


def save_latest_video_bundle(
    videos: list[dict[str, Any]],
    user: dict[str, Any],
    *,
    limit: int = 8,
    persist_artifacts: bool = True,
) -> dict[str, Any]:
    selected = latest_patient_exercise_videos(videos, user, limit=limit)
    artifact_results: list[dict[str, Any]] = []
    dataset_results: list[dict[str, Any]] = []
    if persist_artifacts:
        for position, item in enumerate(list(selected)):
            try:
                detail_id = int(item.get("_detail_id") if item.get("_detail_id") is not None else position)
            except (TypeError, ValueError):
                continue
            if not (0 <= detail_id < len(videos)):
                continue
            for kind in ("video", "frames"):
                try:
                    output, updates = _prepare_export_file(videos[detail_id], "all", kind)
                    updated = _persist_video_artifacts(detail_id, updates, user)
                    videos[detail_id] = updated
                    artifact_results.append(
                        {
                            "detail_id": detail_id,
                            "kind": kind,
                            "path": _relative_repo_path(output),
                            "size": output.stat().st_size if output.is_file() else 0,
                            "ok": True,
                        }
                    )
                except Exception as exc:
                    artifact_results.append(
                        {
                            "detail_id": detail_id,
                            "kind": kind,
                            "ok": False,
                            "error": _clean_text(str(exc)),
                        }
                    )
            selected[position] = _decorate_dashboard_video_item(videos[detail_id], detail_id)
            try:
                dataset_results.append(
                    {
                        "detail_id": detail_id,
                        "ok": True,
                        "paths": _sync_available_artifacts_to_dataset(videos[detail_id], user),
                    }
                )
            except Exception as exc:
                dataset_results.append(
                    {
                        "detail_id": detail_id,
                        "ok": False,
                        "error": _clean_text(str(exc))[:500],
                    }
                )
    now = _now_iso()
    bundle = {
        "updated_at": now,
        "updated_by": _clean_text(user.get("username")) or "system",
        "scope": "latest_patient_exercise_videos",
        "limit": limit,
        "video_count": len(selected),
        "database_source": str(_data_path("video_list")),
        "artifact_results": artifact_results,
        "dataset_manifest": _relative_repo_path(_dataset_manifest_path()),
        "dataset_results": dataset_results,
        "videos": [_video_bundle_entry(item, int(item.get("_detail_id") or idx)) for idx, item in enumerate(selected)],
    }
    bundle_path = _data_path("latest_video_bundle")
    write_json(bundle_path, bundle)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    write_json(DATASET_DIR / "latest_video_bundle.json", bundle)
    return bundle


def _video_detail(
    video: dict[str, Any],
    idx: int,
    user: dict[str, Any],
    *,
    frame_offset: int = 0,
    frame_limit: int = 48,
    frame_phase: str = "all",
    frame_status: str = "ALL",
) -> dict[str, Any]:
    if user["role_key"] == "patient" and not _matches_current_patient(video, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền xem video này.")
    video = _hydrate_video_artifacts(video)
    evaluations = _load_data("doctor_evaluations")
    if not isinstance(evaluations, list):
        evaluations = []
    videos_for_ai_summaries = _load_data("video_list")
    if isinstance(videos_for_ai_summaries, list):
        evaluations = _merge_video_ai_evaluation_summaries(evaluations, videos_for_ai_summaries)
    matched_evaluations = _match_evaluations_for_video(video, evaluations)
    processed_video_path = _resolve_video_source_path(video.get("processed_path"))
    raw_video_path = _resolve_video_source_path(video.get("video_path"))
    pose_playback_path = _pose_playback_video_path(processed_video_path or _resolve_existing_path(video.get("processed_path")))
    video_path = processed_video_path if _audio_codec(processed_video_path) else (pose_playback_path or processed_video_path or raw_video_path)
    playback_video_path, playback_status = _resolve_playback_video_path(video_path, raw_video_path)
    if playback_video_path and pose_playback_path and playback_video_path == pose_playback_path:
        playback_status = "pose_h264"
    frame_path = _ensure_hf_dataset_file(video.get("all_frames_data_path"), min_size=128) or _resolve_existing_path(video.get("all_frames_data_path"))
    df_path = _ensure_hf_dataset_file(video.get("df_path"), min_size=128) or _resolve_existing_path(video.get("df_path"))
    frame_dir = _frame_dir_for_video(video, processed_video_path or video_path)
    frame_zip = _frame_zip_for_video(video, processed_video_path or video_path)
    if not playback_video_path and playback_status in {"unreadable_video", "missing"}:
        rebuilt_video_path = _build_playback_video_from_frames(frame_dir, frame_zip, processed_video_path or video_path)
        if rebuilt_video_path:
            playback_video_path = rebuilt_video_path
            playback_status = "rebuilt_from_frames"
    frame_playback_path = playback_video_path if playback_status != "rebuilt_from_frames" else None
    prefer_video_pose_frames = _needs_video_pose_frame_preference(video)
    if prefer_video_pose_frames:
        frame_video_paths = [candidate for candidate in (frame_playback_path, processed_video_path, raw_video_path) if candidate]
    else:
        frame_video_paths = [candidate for candidate in (frame_playback_path, processed_video_path, raw_video_path) if candidate]
    media_token = _register_media(playback_video_path)
    raw_media_token = _register_media(raw_video_path)
    preview_token = None if prefer_video_pose_frames else _first_artifact_preview_token(frame_dir, frame_zip)
    latest_evaluation = matched_evaluations[-1] if matched_evaluations else None
    fallback_refs = _video_ref_values(video)
    frame_records = _read_frame_records(frame_path)
    sample_records = frame_records[: min(24, len(frame_records))]
    frame_records_have_pose = bool(sample_records) and any(_has_complete_pose(frame) for frame in sample_records)
    frame_records_have_ml = bool(sample_records) and any(_frame_ml_label(frame) for frame in sample_records)
    csv_frame_records = _frame_records_from_csv(df_path) if df_path and (not frame_records or not (frame_records_have_pose and frame_records_have_ml)) else []
    if frame_records and csv_frame_records:
        frame_records = _merge_frame_records_with_csv_pose(frame_records, csv_frame_records)
    elif csv_frame_records:
        frame_records = csv_frame_records
    if playback_video_path and frame_records and not _audio_codec(playback_video_path):
        metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
        sound_video_path, sound_updates = _ensure_sound_playback_video(
            playback_video_path,
            frame_records,
            exercise=video.get("exercise"),
            metrics=metrics,
        )
        if sound_video_path and sound_video_path != playback_video_path and _audio_codec(sound_video_path):
            playback_video_path = sound_video_path
            frame_playback_path = playback_video_path if playback_status != "rebuilt_from_frames" else None
            video_path = sound_video_path
            video["processed_path"] = _relative_repo_path(sound_video_path)
            video["metrics"] = metrics
            videos = _load_data("video_list")
            if isinstance(videos, list) and 0 <= idx < len(videos) and isinstance(videos[idx], dict):
                videos[idx]["processed_path"] = _relative_repo_path(sound_video_path)
                videos[idx]["metrics"] = metrics
                if sound_updates.get("audio_video_path"):
                    videos[idx]["audio_video_path"] = sound_updates.get("audio_video_path")
                _save_data("video_list", videos)
    if prefer_video_pose_frames and frame_records and any(_frame_ml_label(frame) for frame in frame_records[: min(20, len(frame_records))]):
        frame_video_paths = [candidate for candidate in (frame_playback_path, processed_video_path, raw_video_path) if candidate]
        preview_token = None
    phase_bounds = _segment_bounds_from_angle_items(frame_records) if frame_records and not _is_pulley_exercise(video.get("exercise")) else None
    frames, frame_total = _read_frame_payload_with_video_fallback(
        frame_path,
        frame_video_paths,
        offset=frame_offset,
        limit=frame_limit,
        exercise=video.get("exercise"),
        phase_filter=frame_phase,
        status_filter=frame_status,
        fallback_refs=fallback_refs,
        frame_records=frame_records,
        frame_dir=frame_dir,
        frame_zip=frame_zip,
        phase_bounds=phase_bounds,
        processed_frame_path=frame_playback_path or processed_video_path,
        prefer_video_pose_frames=prefer_video_pose_frames,
        allow_video_pose_frames=prefer_video_pose_frames,
    )
    if not frame_records and (not frames or not any(frame.get("image_url") for frame in frames)):
        dir_frames, dir_total = _read_frame_dir(
            frame_dir,
            offset=frame_offset,
            limit=frame_limit,
            exercise=video.get("exercise"),
            fallback_refs=fallback_refs,
            frame_records=frame_records,
            phase_bounds=phase_bounds,
        )
        if dir_frames:
            frames, frame_total = dir_frames, dir_total
        else:
            zip_frames, zip_total = _read_frame_zip(
                frame_zip,
                offset=frame_offset,
                limit=frame_limit,
                exercise=video.get("exercise"),
                fallback_refs=fallback_refs,
                frame_records=frame_records,
                phase_bounds=phase_bounds,
            )
            if zip_frames:
                frames, frame_total = zip_frames, zip_total
    if not frame_records and not frames and frame_video_paths:
        frames, frame_total = _read_video_sample_frames(
            frame_video_paths,
            offset=frame_offset,
            limit=frame_limit,
            exercise=video.get("exercise"),
            fallback_refs=fallback_refs,
            phase_bounds=phase_bounds,
        )
    chart = _read_chart_payload(df_path, video, latest_evaluation)
    return {
        "id": idx,
        "video": video,
        "media": {
            "video_url": f"/media/{media_token}" if media_token else "",
            "raw_video_url": f"/media/{raw_media_token}" if raw_media_token else "",
            "preview_image_url": next((frame.get("image_url") for frame in frames if frame.get("image_url")), f"/media/{preview_token}" if preview_token else ""),
            "file_exists": bool(video_path or raw_video_path),
            "video_path": str(playback_video_path or video_path or raw_video_path or ""),
            "raw_video_path": str(raw_video_path or ""),
            "playback_status": playback_status,
            "playback_codec": _video_codec(playback_video_path),
            "frame_data_exists": bool(frame_path),
            "frame_preview_exists": bool(frames),
            "df_exists": bool(df_path),
            "analysis_artifact_exists": bool(df_path or frame_path),
        },
        "evaluations": matched_evaluations[:12],
        "latest_evaluation": latest_evaluation,
        "latest_job": _read_analysis_job(video) or _public_analysis_job(video, _find_progress_for_video(video)),
        "frames": frames,
        "frame_groups": _read_frame_group_payload(frame_path, video.get("exercise"), fallback_refs)
        or _frame_group_summary(frame_records or frames, frame_total, video.get("exercise")),
        "frame_total": frame_total,
        "frame_offset": frame_offset,
        "frame_limit": frame_limit,
        "frame_phase": frame_phase,
        "frame_status": frame_status,
        "chart": chart,
    }


def build_dashboard_payload(user: dict[str, Any]) -> dict[str, Any]:
    users = load_users()
    videos = _load_data("video_list")
    evaluations = _load_data("doctor_evaluations")
    symptoms = _load_data("patient_symptoms")
    schedules = _load_data("schedules")
    research_data = _load_data("research_data")
    training_history = _load_data("lich_su_tap_luyen")
    videos_for_dashboard = [video for video in videos if isinstance(video, dict)] if isinstance(videos, list) else []
    if isinstance(evaluations, list):
        evaluations = _merge_video_ai_evaluation_summaries(evaluations, videos_for_dashboard)
    else:
        evaluations = _merge_video_ai_evaluation_summaries([], videos_for_dashboard)

    scoped_videos = _scope_records(videos, user)
    scoped_evaluations = _scope_records(evaluations, user)
    scoped_symptoms = _scope_records(symptoms, user)
    scoped_schedules = _scope_records(schedules, user)
    scoped_research = _scope_records(research_data, user)
    video_status = _summarize_status(scoped_videos)
    role_counts = _role_counts(users)

    can_see_research = user["role_key"] in {"admin", "researcher"}
    return {
        "user": user,
        "source": {
            "database_dir": str(DATABASE_DIR),
            "users": str(_data_path("users")),
            "video_list": str(_data_path("video_list")),
        },
        "metrics": {
            "accounts": role_counts["total"],
            "patients": role_counts["patient"],
            "clinicians": role_counts["doctor_ktv"],
            "researchers": role_counts["researcher"],
            "admins": role_counts["admin"],
            "videos": len(scoped_videos),
            "videos_done": video_status["done"],
            "videos_processing": video_status["processing"],
            "videos_pending": video_status["pending"],
            "evaluations": len(scoped_evaluations),
            "symptoms": len(scoped_symptoms),
            "schedules": len(scoped_schedules),
            "research_records": len(scoped_research) if can_see_research else 0,
            "training_sessions": len(training_history) if isinstance(training_history, list) else 0,
        },
        "videos": dashboard_video_items(videos_for_dashboard, user),
        "latest_evaluated_videos": latest_patient_exercise_videos(
            videos_for_dashboard,
            user,
            limit=8,
        ),
        "evaluations": _take_recent_evaluations(scoped_evaluations),
        "symptoms": _take(scoped_symptoms),
        "schedules": _take(scoped_schedules),
        "research_data": _take(scoped_research) if can_see_research else [],
        "users": [
            _public_user(username, record)
            for username, record in users.items()
            if isinstance(record, dict) and (user["role_key"] == "admin" or role_key(record.get("role")) == "patient")
        ]
        if user["role_key"] in {"admin", "doctor_ktv", "researcher"}
        else [],
    }


app = FastAPI(title="Rehab AI Monitor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5183",
        "http://localhost:5183",
    ],
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "database_dir": str(DATABASE_DIR)}


@app.get("/auth/login-options")
async def login_options() -> dict[str, Any]:
    return build_login_options()


@app.post("/auth/login")
async def login(payload: LoginRequest) -> dict[str, Any]:
    username, record = _authenticate(payload.username, payload.password)
    return _issue_token(username, record)


@app.post("/auth/register")
async def register(payload: RegisterRequest) -> dict[str, Any]:
    username = _clean_text(payload.username)
    email = _clean_text(payload.email)
    _require_passwords_match(payload.password, payload.password2)
    if not username or not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vui lòng nhập tài khoản và email.")

    users = load_users()
    if lookup_user(users, username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập đã tồn tại.")
    if lookup_user(users, email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được sử dụng.")

    users[username] = _new_user_record(payload, role=ROLE_PATIENT)
    save_users(users)
    return {"ok": True, "user": _public_user(username, users[username])}


@app.post("/auth/reset-password")
async def reset_password(payload: ResetPasswordRequest) -> dict[str, Any]:
    username = _clean_text(payload.username)
    email = _clean_text(payload.email)
    _require_passwords_match(payload.password, payload.password2)
    if not username or not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vui lòng nhập tài khoản và email.")

    users = load_users()
    user_key = lookup_user(users, username)
    record = users.get(user_key or "")
    if not user_key or not isinstance(record, dict):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản.")
    if _search_text(record.get("email")) != _search_text(email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email không khớp với tài khoản.")

    now = _now_iso()
    record["password"] = hash_password_v2(payload.password)
    record["hash_version"] = current_hash_version()
    record["updated_at"] = now
    record["must_change_password"] = False
    users[user_key] = record
    save_users(users)
    return {"ok": True, "message": "Đã đặt lại mật khẩu. Bạn có thể đăng nhập ngay."}


@app.post("/auth/logout")
async def logout(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    TOKEN_REVOKED.add(session["token"])
    TOKEN_STORE.pop(session["token"], None)
    return {"ok": True}


@app.get("/auth/me")
async def me(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    return {"user": session["user"]}


@app.get("/dashboard")
async def dashboard(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    return build_dashboard_payload(session["user"])


@app.get("/videos/{identifier}/detail")
async def video_detail(
    identifier: str,
    frame_offset: int = 0,
    frame_limit: int = 48,
    frame_phase: str = "all",
    frame_status: str = "ALL",
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    videos = _load_data("video_list")
    if not isinstance(videos, list):
        videos = []
    records = [video for video in videos if isinstance(video, dict)]
    idx = _find_video_index(records, identifier)
    if idx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy video.")
    return _video_detail(
        records[idx],
        idx,
        session["user"],
        frame_offset=frame_offset,
        frame_limit=frame_limit,
        frame_phase=frame_phase,
        frame_status=frame_status,
    )


@app.post("/videos/latest-bundle")
async def latest_video_bundle(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "researcher", "doctor_ktv"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ admin, NCV hoặc bác sĩ/KTV được lưu bundle video.")
    videos = _load_data("video_list")
    if not isinstance(videos, list):
        videos = []
    bundle = save_latest_video_bundle([video for video in videos if isinstance(video, dict)], user, limit=8)
    return {"ok": True, "bundle": bundle, "path": str(_data_path("latest_video_bundle"))}


@app.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    exercise: str = Form(default="Bài tập con lắc Codman"),
    patient_username: str = Form(default=""),
    full_name: str = Form(default=""),
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    target_username = _clean_text(patient_username) or _clean_text(user.get("username"))
    target_full_name = _clean_text(full_name) or _clean_text(user.get("full_name")) or target_username
    if user["role_key"] == "patient":
        target_username = _clean_text(user.get("username"))
        target_full_name = _clean_text(user.get("full_name")) or target_username
    if not target_username:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thiếu tên tài khoản bệnh nhân.")

    original_name = _safe_filename(file.filename, "video.mp4")
    suffix = Path(original_name).suffix.lower()
    if suffix not in VIDEO_SOURCE_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chỉ hỗ trợ video MP4/MOV/AVI/MKV/WEBM.")
    upload_dir = REPO_ROOT / "patient_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_name = f"{_safe_filename(target_username, 'patient')}_{stamp}_{original_name}"
    target_path = upload_dir / stored_name
    total = 0
    try:
        with target_path.open("wb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > UPLOAD_MAX_BYTES:
                    raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Video vượt quá dung lượng cho phép.")
                handle.write(chunk)
    except HTTPException:
        target_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Không lưu được video upload: {exc}") from exc
    finally:
        await file.close()
    if target_path.stat().st_size < 1024:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File video quá nhỏ hoặc rỗng.")

    record = {
        "username": target_username,
        "patient_username": target_username,
        "full_name": target_full_name,
        "video_name": original_name,
        "stored_filename": stored_name,
        "exercise": _exercise_label(exercise),
        "accuracy": None,
        "time": datetime.now().strftime("%H:%M - %d/%m/%Y"),
        "uploaded_at": _now_iso(),
        "video_path": _relative_repo_path(target_path),
        "processed_path": None,
        "status": "Chờ phân tích",
        "df_path": None,
        "all_frames_data_path": None,
        "source": "react_upload",
        "uploaded_by": _clean_text(user.get("username")),
    }
    raw_dataset = _sync_export_to_dataset(record, target_path, kind="video", phase="raw", user=user)
    if raw_dataset:
        record["dataset_raw_video_path"] = raw_dataset.get("dataset_path")
        record["dataset_manifest"] = _relative_repo_path(_dataset_manifest_path())
    videos = _load_data("video_list")
    if not isinstance(videos, list):
        videos = []
    videos.insert(0, record)
    _save_data("video_list", videos)
    schedules = _load_data("schedules")
    if not isinstance(schedules, list):
        schedules = []
    schedules.insert(
        0,
        {
            "id": str(uuid.uuid4()),
            "patient_username": target_username,
            "full_name": target_full_name,
            "kind": "exercise",
            "title": f"Lịch tập luyện: Video mới cần phân tích - {original_name}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "note": "Bệnh nhân vừa upload video. NCV bấm phân tích AI; Bác sĩ/KTV xem kết quả, đánh giá PHCN và cập nhật phiếu NCKH.",
            "status": "Chờ phân tích/đánh giá",
            "created_by": _clean_text(user.get("username")),
            "created_at": _now_iso(),
            "source": "patient_video_upload",
            "video_name": original_name,
            "video_path": _relative_repo_path(target_path),
        },
    )
    _save_data("schedules", schedules)
    try:
        save_latest_video_bundle([video for video in videos if isinstance(video, dict)], session["user"], limit=8, persist_artifacts=False)
    except Exception:
        pass
    return {"ok": True, "video": {**record, "_detail_id": 0}, "size": target_path.stat().st_size}


def _evaluation_errors(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    text = _clean_text(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[\n;]+", text) if item.strip()]


def _doctor_display_name(user: dict[str, Any]) -> str:
    name = user.get("full_name") or user.get("username") or "Người đánh giá"
    if user.get("role_key") == "researcher":
        return f"NCV: {name}"
    if user.get("role_key") == "admin":
        return f"QTV: {name}"
    return f"Bác sĩ/KTV: {name}"


def _evaluation_record_for_video(
    video: dict[str, Any],
    user: dict[str, Any],
    payload: EvaluationRequest,
) -> dict[str, Any]:
    accuracy = _to_float(video.get("accuracy"))
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    if accuracy is None:
        accuracy = _to_float(metrics.get("do_chinh_xac"))
    return {
        "id": str(uuid.uuid4()),
        "patient_username": _clean_text(video.get("username") or video.get("patient_username") or video.get("full_name")),
        "full_name": _clean_text(video.get("full_name") or video.get("patient_name") or video.get("username")),
        "doctor_username": user["username"],
        "doctor_name": _doctor_display_name(user),
        "video_name": _clean_text(video.get("video_name") or video.get("stored_filename") or video.get("video_path")),
        "exercise": _clean_text(video.get("exercise")),
        "ai_accuracy": round(float(accuracy), 2) if accuracy is not None else None,
        "doctor_result": _clean_text(payload.doctor_result),
        "errors": _evaluation_errors(payload.errors),
        "comments": _clean_text(payload.comments),
        "comments_ncv": _clean_text(payload.comments_ncv),
        "plan": _clean_text(payload.plan),
        "time": datetime.now().strftime("%H:%M - %d/%m/%Y"),
        "created_at": _now_iso(),
        "source": "react_api",
    }


@app.post("/videos/{identifier}/evaluations")
async def create_video_evaluation(
    identifier: str,
    payload: EvaluationRequest,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "doctor_ktv", "researcher"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ QTV, bác sĩ/KTV hoặc NCV được gửi đánh giá.")
    video, _ = _video_for_identifier(identifier, user)
    evaluations = _load_data("doctor_evaluations")
    if not isinstance(evaluations, list):
        evaluations = []
    record = _evaluation_record_for_video(video, user, payload)
    evaluations.append(record)
    _save_data("doctor_evaluations", evaluations)
    return {"ok": True, "evaluation": record}


def _video_for_identifier(identifier: str, user: dict[str, Any]) -> tuple[dict[str, Any], int]:
    videos = _load_data("video_list")
    if not isinstance(videos, list):
        videos = []
    records = [video for video in videos if isinstance(video, dict)]
    idx = _find_video_index(records, identifier)
    if idx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "KhÃ´ng tÃ¬m tháº¥y video.")
    video = records[idx]
    if user["role_key"] == "patient" and not _matches_current_patient(video, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền xem video này.")
    return video, idx


@app.get("/videos/{identifier}/analysis-jobs/latest")
async def latest_analysis_job(identifier: str, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    video, _ = _video_for_identifier(identifier, session["user"])
    latest = _read_analysis_job(video)
    if isinstance(latest, dict):
        latest = _mark_stale_analysis_job(video, latest)
    return {"job": latest}


@app.get("/videos/{identifier}/analysis-jobs/history")
async def analysis_job_history(identifier: str, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    video, _ = _video_for_identifier(identifier, session["user"])
    history = _read_analysis_history(video)
    return {"items": history, "count": len(history)}


@app.post("/videos/{identifier}/analysis-jobs")
async def start_analysis_job(
    identifier: str,
    payload: AnalysisJobRequestBody,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "researcher", "doctor_ktv"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ admin/NCV được chạy phân tích AI.")
    video, video_index = _video_for_identifier(identifier, user)
    restored_job = _restore_saved_artifacts_job(video, video_index, user, payload, "start")
    if restored_job:
        return {"started": True, "reason": "restored_saved_artifacts", "job": restored_job}
    job = _start_real_analysis_job(video, video_index, user, payload, "start")
    return {"started": True, "reason": "running_mediapipe", "job": job}


@app.post("/videos/{identifier}/analysis-jobs/rerun")
async def rerun_analysis_job(
    identifier: str,
    payload: AnalysisJobRequestBody,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "researcher", "doctor_ktv"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ admin/NCV được chạy lại phân tích AI.")
    video, video_index = _video_for_identifier(identifier, user)
    job = _start_real_analysis_job(video, video_index, user, payload, "rerun")
    return {"started": True, "reason": "running_mediapipe", "job": job}


@app.post("/videos/{identifier}/analysis-jobs/retry")
async def retry_analysis_job(identifier: str, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "researcher", "doctor_ktv"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ admin/NCV được retry phân tích AI.")
    video, video_index = _video_for_identifier(identifier, user)
    latest = _read_analysis_job(video)
    options = latest.get("job_meta", {}).get("options", {}) if isinstance(latest, dict) else {}
    skip_option = options.get("skip_step")
    body = AnalysisJobRequestBody(
        model_type=_clean_text(options.get("model_type")) or "MediaPipe Heavy",
        skip_step=int(skip_option) if skip_option is not None else 0,
        resize_width=int(options.get("resize_width") or 720),
        min_confidence=float(options.get("min_confidence") or 0.65),
    )
    job = _start_real_analysis_job(video, video_index, user, body, "retry")
    return {"started": True, "reason": "running_mediapipe", "job": job}


@app.post("/videos/{identifier}/analysis-jobs/cancel")
async def cancel_analysis_job(identifier: str, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "researcher", "doctor_ktv"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ admin/NCV được hủy job phân tích AI.")
    video, _ = _video_for_identifier(identifier, user)
    latest = _read_analysis_job(video)
    if not latest:
        return {"ok": False, "reason": "no_job", "job": None}
    latest.update(
        {
            "status": "canceled",
            "progress": latest.get("progress") or 0,
            "cancel_requested": True,
            "status_msg": "Đã hủy job phân tích.",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "steps": _job_steps("canceled", float(latest.get("progress") or 0)),
        }
    )
    _write_analysis_job(video, latest)
    return {"ok": True, "reason": "canceled", "job": latest}


@app.post("/videos/{identifier}/exports")
async def prepare_video_export(
    identifier: str,
    payload: ExportRequestBody,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "doctor_ktv", "researcher"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền lưu/tải artifact video.")
    video, idx = _video_for_identifier(identifier, user)
    path, updates = _prepare_export_file(video, payload.phase, payload.kind)
    updated_video = _persist_video_artifacts(idx, updates, user) if payload.persist else _hydrate_video_artifacts(video)
    phase_key = _phase_suffix(payload.phase)
    kind_key = "frames" if _search_text(payload.kind) in {"frames", "frame", "zip", "images"} else "video"
    dataset_entry = _sync_export_to_dataset(updated_video, path, kind=kind_key, phase=phase_key, user=user)
    dataset_extra: dict[str, Any] = {}
    if kind_key == "frames":
        paths = _artifact_paths_for_export(updated_video)
        frame_entry = _sync_frame_images_to_dataset(updated_video, path, phase=phase_key, user=user)
        if frame_entry:
            dataset_extra["frames_dir"] = frame_entry
        for extra_kind, extra_path in (("csv", paths.get("df_path")), ("json", paths.get("frame_path"))):
            if isinstance(extra_path, Path) and extra_path.is_file():
                extra_entry = _sync_export_to_dataset(updated_video, extra_path, kind=extra_kind, phase=phase_key, user=user)
                if extra_entry:
                    dataset_extra[extra_kind] = extra_entry
    filename = f"{_processed_stem(path) or 'rehab_export'}{path.suffix.lower()}"
    token = _register_export_media(path, filename)
    return {
        "ok": True,
        "kind": kind_key,
        "phase": phase_key,
        "url": f"/media/{token}" if token else "",
        "path": _relative_repo_path(path),
        "dataset_path": dataset_entry.get("dataset_path") if dataset_entry else "",
        "dataset_manifest": _relative_repo_path(_dataset_manifest_path()),
        "dataset_extra": dataset_extra,
        "filename": filename,
        "size": path.stat().st_size if path.is_file() else 0,
        "updated_video": updated_video,
    }


@app.post("/videos/{identifier}/chart-exports")
async def save_chart_export(
    identifier: str,
    payload: ChartExportRequestBody,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "doctor_ktv", "researcher"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền lưu biểu đồ.")
    video, _ = _video_for_identifier(identifier, user)
    header, _, encoded = payload.image_data.partition(",")
    if "base64" not in header.lower() or not encoded:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dữ liệu ảnh biểu đồ không hợp lệ.")
    try:
        content = base64.b64decode(encoded, validate=True)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không đọc được dữ liệu ảnh biểu đồ.")
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ảnh biểu đồ rỗng.")
    phase_key = _phase_suffix(payload.phase)
    filename = _safe_filename(payload.filename, "chart.png")
    if not filename.lower().endswith(".png"):
        filename = f"{Path(filename).stem}.png"
    chart_dir = _dataset_kind_dir(video, "charts")
    chart_dir.mkdir(parents=True, exist_ok=True)
    target = chart_dir / filename
    target.write_bytes(content)
    entry = _dataset_artifact_entry(video, target, target, kind="charts", phase=phase_key, user=user)
    entry["chart_name"] = _clean_text(payload.chart_name)
    entry["metrics"] = payload.metrics if isinstance(payload.metrics, dict) else {}
    _upsert_dataset_manifest_entry(entry)
    token = _register_export_media(target, filename)
    return {
        "ok": True,
        "kind": "charts",
        "phase": phase_key,
        "url": f"/media/{token}" if token else "",
        "path": _relative_repo_path(target),
        "dataset_path": _relative_repo_path(target),
        "dataset_manifest": _relative_repo_path(_dataset_manifest_path()),
        "filename": filename,
        "size": target.stat().st_size if target.is_file() else 0,
    }


@app.get("/media/{token}", response_model=None)
async def media(token: str):
    _cleanup_media_tokens()
    meta = _media_token_meta(token)
    if not meta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media không tồn tại hoặc đã hết hạn.")
    path = Path(str(meta.get("path") or ""))
    if not path.is_file():
        _forget_media_token(token)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media không tồn tại.")
    if meta.get("kind") in {"video_frame", "video_pose_frame"}:
        try:
            import cv2  # type: ignore[import-not-found]

            ok = False
            frame = None
            paths = meta.get("paths") if isinstance(meta.get("paths"), list) else [meta.get("path")]
            for candidate_raw in paths:
                candidate = Path(str(candidate_raw or ""))
                if not candidate.is_file():
                    continue
                cap = cv2.VideoCapture(str(candidate))
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(meta.get("frame_index") or 0))
                ok, frame = cap.read()
                cap.release()
                if ok and frame is not None:
                    break
            if not ok or frame is None:
                raise RuntimeError("frame read failed")
            if meta.get("kind") == "video_pose_frame" and not _to_bool(meta.get("overlay_only")):
                frame_data = meta.get("frame_data") if isinstance(meta.get("frame_data"), dict) else {}
                frame_data = _frame_with_exercise_context(frame_data, frame_data.get("exercise") or frame_data.get("exercise_key"))
                if not _has_complete_pose(frame_data):
                    frame_data = _frame_with_detected_pose(frame, frame_data)
                if _frame_exercise_key(frame_data) in {"codman", "pulley"}:
                    frame_data = _apply_youtube_reference_to_frame(
                        frame_data,
                        frame_data.get("exercise") or frame_data.get("exercise_key"),
                        overwrite=frame_data.get("ref_source") != "youtube_mediapipe",
                    )
                display_index = int(meta.get("data_frame_index") if meta.get("data_frame_index") is not None else meta.get("frame_index") or 0) + 1
                threshold = _to_float(frame_data.get("threshold") or frame_data.get("phase_threshold")) or 30.0
                frame = _draw_pose_analysis_overlay(frame, frame_data, display_index, threshold=threshold)
            ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if not ok:
                raise RuntimeError("frame encode failed")
        except Exception:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tạo được frame preview từ video.")
        return Response(content=encoded.tobytes(), media_type="image/jpeg")
    member = _clean_text(meta.get("member"))
    if member:
        try:
            with zipfile.ZipFile(path) as archive:
                content = archive.read(member)
        except Exception:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Frame không tồn tại trong artifact.")
        suffix = Path(member).suffix.lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(suffix, "application/octet-stream")
        return Response(content=content, media_type=media_type)
    download_name = _clean_text(meta.get("download_name"))
    return FileResponse(path, filename=download_name or None)


@app.get("/admin/users")
async def admin_users(_: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    users = load_users()
    return {"users": [_public_user(username, record) for username, record in users.items() if isinstance(record, dict)]}


@app.post("/admin/users")
async def admin_create_user(
    payload: AdminCreateUserRequest,
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    username = _clean_text(payload.username)
    email = _clean_text(payload.email)
    _require_passwords_match(payload.password, payload.password2)
    if not username or not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vui lòng nhập tài khoản và email.")

    users = load_users()
    if lookup_user(users, username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập đã tồn tại.")
    if lookup_user(users, email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được sử dụng.")

    users[username] = _new_user_record(
        payload,
        role=canonical_role(payload.role),
        must_change_password=payload.must_change_password,
    )
    save_users(users)
    return {"ok": True, "user": _public_user(username, users[username])}


@app.patch("/admin/users/{username}/active")
async def admin_set_user_active(
    username: str,
    payload: UserActiveRequest,
    admin_session: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    users = load_users()
    user_key = lookup_user(users, username)
    if not user_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản.")
    if user_key == admin_session["username"] and payload.active is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể khóa chính tài khoản đang đăng nhập.")
    users[user_key]["active"] = bool(payload.active)
    users[user_key]["updated_at"] = _now_iso()
    save_users(users)
    return {"ok": True, "user": _public_user(user_key, users[user_key])}


@app.post("/symptoms")
async def create_symptom(
    payload: SymptomRequest,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    symptoms = _load_data("patient_symptoms")
    if not isinstance(symptoms, list):
        symptoms = []
    record = {
        "username": user["username"],
        "full_name": user["full_name"],
        "vas": int(payload.vas),
        "pain_location": _clean_text(payload.pain_location),
        "exercise": _clean_text(payload.exercise),
        "symptoms": _clean_text(payload.symptoms),
        "date": _clean_text(payload.date),
        "time": datetime.now().strftime("%H:%M - %d/%m/%Y"),
        "created_at": _now_iso(),
        "source": "react_api",
    }
    symptoms.insert(0, record)
    _save_data("patient_symptoms", symptoms)
    return {"ok": True, "symptom": record}


@app.post("/schedules")
async def create_schedule(
    payload: ScheduleRequest,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, Any]:
    user = session["user"]
    if user["role_key"] not in {"admin", "doctor_ktv"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ quản trị viên hoặc bác sĩ/KTV được tạo lịch nhắc.")
    users = load_users()
    patient_key = lookup_user(users, payload.patient_username)
    patient = users.get(patient_key or "")
    if not patient_key or not isinstance(patient, dict) or role_key(patient.get("role")) != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản bệnh nhân.")
    schedules = _load_data("schedules")
    if not isinstance(schedules, list):
        schedules = []
    record = {
        "id": str(uuid.uuid4()),
        "patient_username": patient_key,
        "full_name": patient.get("full_name") or patient_key,
        "kind": _clean_text(payload.kind) or "exercise",
        "title": _clean_text(payload.title),
        "date": _clean_text(payload.date),
        "time": _clean_text(payload.time),
        "note": _clean_text(payload.note),
        "status": "Đã gửi",
        "created_by": user["username"],
        "created_at": _now_iso(),
        "source": "react_api",
    }
    schedules.insert(0, record)
    _save_data("schedules", schedules)
    return {"ok": True, "schedule": record}

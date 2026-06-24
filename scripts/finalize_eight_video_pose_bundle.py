from __future__ import annotations

import csv
import json
import math
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.json_store import write_json  # noqa: E402


TARGET_INDICES = [12, 10, 11, 1, 9, 6, 8, 4]

CAO_PULLEY_VIDEO_NAME = "042916_Cao Th\u1ecb Th\u01b0\u1eddng - B\u00e0i t\u1eadp v\u1edbi g\u1eady.mp4"
ROOT_SYNC_KEYS = [
    "username",
    "full_name",
    "video_name",
    "exercise",
    "accuracy",
    "time",
    "video_path",
    "raw_video_path",
    "processed_path",
    "status",
    "df_path",
    "all_frames_data_path",
    "detail_id",
    "patient_username",
    "artifact_updated_at",
    "frame_total",
    "has_video_file",
    "has_frames",
    "has_chart",
    "latest_bundle_updated_at",
    "video_time",
    "audio_video_path",
    "frames_zip_path",
    "frames_zip",
    "giai_doan",
    "sai_so",
]
ROOT_METRIC_KEYS = [
    "do_chinh_xac",
    "ty_le_tong_the",
    "ty_le_gan_dung",
    "ty_le_vai_dung",
    "ty_le_khuyu_dung",
    "frame_dung",
    "frame_gan_dung",
    "frame_sai",
    "frame_khong_nhan_dang",
    "tong_frame_hop_le",
    "tong_frame_da_cham",
    "tb_goc_vai",
    "tb_goc_khuyu",
    "min_goc_vai",
    "max_goc_vai",
    "min_goc_khuyu",
    "max_goc_khuyu",
    "mae_tong",
    "precision",
    "recall",
    "f1_score",
    "tb_vai_chuan",
    "tb_khuyu_chuan",
    "ref_source",
    "exercise_key",
    "phase_accuracy_g1",
    "phase_accuracy_g2",
    "phase_accuracy_g3",
    "thoi_gian",
    "tong_frame",
    "metrics_refreshed_at",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _search_text(value: Any) -> str:
    text = _clean_text(value).replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").lower()


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        number = float(value)
        if not math.isfinite(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _search_text(value) in {"1", "true", "yes", "y", "pass"}


def _relative_repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_existing_path(raw_path: Any) -> Path | None:
    text = _clean_text(raw_path).replace("\\", "/")
    if not text:
        return None
    candidates: list[Path] = []
    for prefix in ("/data/", "/app/"):
        if text.startswith(prefix):
            candidates.append(ROOT / text[len(prefix) :])
    raw = Path(text)
    candidates.append(raw if raw.is_absolute() else ROOT / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _find_patient_upload(*tokens: str) -> Path | None:
    needles = [_search_text(token) for token in tokens if token]
    for path in (ROOT / "patient_uploads").glob("*.mp4"):
        haystack = _search_text(path.name)
        if all(token in haystack for token in needles) and "_ftmp" not in haystack:
            return path
    return None


def _video_frame_count(path: Path | None) -> int:
    if not path or not path.is_file():
        return 0
    try:
        import cv2  # type: ignore[import-not-found]

        cap = cv2.VideoCapture(str(path))
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) if cap.isOpened() else 0
        cap.release()
        return count
    except Exception:
        return 0


def _video_frame_size(path: Path | None) -> tuple[int, int]:
    if not path or not path.is_file():
        return (0, 0)
    try:
        import cv2  # type: ignore[import-not-found]

        cap = cv2.VideoCapture(str(path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        return (width, height)
    except Exception:
        return (0, 0)


def _exercise_key(exercise: Any) -> str:
    text = _search_text(exercise)
    if "codman" in text or "con lac" in text:
        return "codman"
    if "gay" in text or "pulley" in text:
        return "pulley"
    return text or "unknown"


def _pose_landmarks(frame: dict[str, Any]) -> list[tuple[int, float, float, float]]:
    points = []
    for idx in range(33):
        x = _to_float(frame.get(f"pt{idx}_x"))
        y = _to_float(frame.get(f"pt{idx}_y"))
        if x is None or y is None:
            continue
        vis = _to_float(frame.get(f"pt{idx}_vis"))
        points.append((idx, x, y, 1.0 if vis is None else vis))
    return points


def _has_complete_pose(frame: dict[str, Any]) -> bool:
    return len(_pose_landmarks(frame)) >= 33


def _side_angle_values(frame: dict[str, Any], side: str) -> tuple[float | None, float | None]:
    if side == "left":
        return _to_float(frame.get("goc_vai_trai") or frame.get("left_shoulder_angle")), _to_float(
            frame.get("goc_khuyu_trai") or frame.get("left_elbow_angle")
        )
    return _to_float(frame.get("goc_vai_phai") or frame.get("right_shoulder_angle")), _to_float(
        frame.get("goc_khuyu_phai") or frame.get("right_elbow_angle")
    )


def _angle_values(frame: dict[str, Any], exercise: Any) -> tuple[float | None, float | None]:
    if _exercise_key(exercise) == "pulley":
        left_shoulder, left_elbow = _side_angle_values(frame, "left")
        right_shoulder, right_elbow = _side_angle_values(frame, "right")
        shoulder_values = [value for value in (left_shoulder, right_shoulder) if value is not None]
        elbow_values = [value for value in (left_elbow, right_elbow) if value is not None]
        shoulder = sum(shoulder_values) / len(shoulder_values) if shoulder_values else _to_float(frame.get("goc_vai"))
        elbow = sum(elbow_values) / len(elbow_values) if elbow_values else _to_float(frame.get("goc_khuyu"))
        return shoulder, elbow
    return (
        _to_float(frame.get("goc_vai") or frame.get("right_shoulder_angle") or frame.get("goc_vai_phai")),
        _to_float(frame.get("goc_khuyu") or frame.get("right_elbow_angle") or frame.get("goc_khuyu_phai")),
    )


def _ref_values(frame: dict[str, Any]) -> tuple[float | None, float | None]:
    return _to_float(frame.get("shoulder_ref") or frame.get("vai_chuan")), _to_float(frame.get("elbow_ref") or frame.get("khuyu_chuan"))


def _angle_between_points(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float | None:
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    norm_ba = math.hypot(*ba)
    norm_bc = math.hypot(*bc)
    if norm_ba <= 1e-9 or norm_bc <= 1e-9:
        return None
    cosine = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / (norm_ba * norm_bc)))
    return math.degrees(math.acos(cosine))


def _recompute_pose_angles(record: dict[str, Any], exercise: Any) -> dict[str, Any]:
    if not _has_complete_pose(record):
        return record
    points = {idx: (x, y) for idx, x, y, _ in _pose_landmarks(record)}

    def angle(indices: tuple[int, int, int]) -> float | None:
        if not all(idx in points for idx in indices):
            return None
        return _angle_between_points(points[indices[0]], points[indices[1]], points[indices[2]])

    output = dict(record)
    left_shoulder = angle((23, 11, 13))
    left_elbow = angle((11, 13, 15))
    right_shoulder = angle((24, 12, 14))
    right_elbow = angle((12, 14, 16))
    for key, value in {
        "goc_vai_trai": left_shoulder,
        "goc_khuyu_trai": left_elbow,
        "left_shoulder_angle": left_shoulder,
        "left_elbow_angle": left_elbow,
        "goc_vai_phai": right_shoulder,
        "goc_khuyu_phai": right_elbow,
        "right_shoulder_angle": right_shoulder,
        "right_elbow_angle": right_elbow,
    }.items():
        if value is not None:
            output[key] = value
    if _exercise_key(exercise) == "codman":
        if right_shoulder is not None:
            output["goc_vai"] = right_shoulder
            output["shoulder_angle"] = right_shoulder
        if right_elbow is not None:
            output["goc_khuyu"] = right_elbow
            output["elbow_angle"] = right_elbow
    elif _exercise_key(exercise) == "pulley":
        current_left_shoulder, current_left_elbow = _side_angle_values(output, "left")
        current_right_shoulder, current_right_elbow = _side_angle_values(output, "right")
        shoulder_values = [value for value in (current_left_shoulder, current_right_shoulder) if value is not None]
        elbow_values = [value for value in (current_left_elbow, current_right_elbow) if value is not None]
        if shoulder_values:
            output["goc_vai"] = sum(shoulder_values) / len(shoulder_values)
            output["shoulder_angle"] = output["goc_vai"]
        if elbow_values:
            output["goc_khuyu"] = sum(elbow_values) / len(elbow_values)
            output["elbow_angle"] = output["goc_khuyu"]
    return output


BLOCKING_PERSON_OVERLAP_REASONS = {
    "codman_helper_overlap",
    "multiple_people_overlap",
    "multi_person_overlap",
    "patient_overlap",
    "body_overlap",
    "person_overlap",
    "overlap_person",
}


def _has_required_pose_measurements(frame: dict[str, Any], exercise: Any) -> bool:
    exercise_key = _exercise_key(exercise)
    if exercise_key not in {"codman", "pulley"}:
        return True
    if not _has_complete_pose(frame):
        return False
    frame = _recompute_pose_angles(frame, exercise)
    if exercise_key == "pulley":
        values = (*_side_angle_values(frame, "left"), *_side_angle_values(frame, "right"))
        return all(value is not None for value in values)
    shoulder, elbow = _angle_values(frame, exercise)
    return shoulder is not None and elbow is not None


def _has_blocking_person_overlap(frame: dict[str, Any], exercise: Any) -> bool:
    reason = _search_text(frame.get("stranger_reason"))
    if reason in BLOCKING_PERSON_OVERLAP_REASONS:
        return True
    if reason in {"multiple_people", "pulley_multiple_people"}:
        return not _has_required_pose_measurements(frame, exercise)
    return False


def _frame_should_be_unknown(frame: dict[str, Any], exercise: Any) -> bool:
    exercise_key = _exercise_key(exercise)
    if exercise_key in {"codman", "pulley"} and not _has_required_pose_measurements(frame, exercise_key):
        return True
    if _to_bool(frame.get("filtered_stranger")) and _has_blocking_person_overlap(frame, exercise):
        return not _has_required_pose_measurements(frame, exercise)
    status_text = _clean_text(frame.get("status") or frame.get("phase_status")).upper()
    return status_text == "UNKNOWN" and _has_blocking_person_overlap(frame, exercise) and not _has_required_pose_measurements(frame, exercise)


def _ml_status(frame: dict[str, Any]) -> str:
    text = _search_text(
        frame.get("ml_label_text")
        or frame.get("ml_result")
        or frame.get("rf_label")
        or frame.get("predicted_label")
        or frame.get("classifier_label")
    )
    if "gan" in text or "near" in text:
        return "NEAR"
    if "sai" in text or "fail" in text or "incorrect" in text:
        return "FAIL"
    if "dung" in text or "pass" in text or "correct" in text:
        return "PASS"
    value = _to_float(frame.get("ml_label"))
    if value is None:
        return ""
    label = int(round(value))
    if label == 0:
        return "FAIL"
    if label == 1:
        return "NEAR"
    if label == 2:
        return "PASS"
    return ""


def _status(frame: dict[str, Any]) -> str:
    ml_status = _ml_status(frame)
    if ml_status:
        return ml_status
    text = _clean_text(frame.get("phase_status") or frame.get("status")).upper()
    if text in {"PASS", "NEAR", "FAIL"}:
        return text
    if _to_bool(frame.get("dung")):
        return "PASS"
    if _to_bool(frame.get("gan_dung")):
        return "NEAR"
    return "FAIL"


def _analysis_metrics(records: list[dict[str, Any]], exercise: Any) -> dict[str, Any]:
    pass_count = near_count = fail_count = unknown_count = 0
    shoulder_values: list[float] = []
    elbow_values: list[float] = []
    shoulder_refs: list[float] = []
    elbow_refs: list[float] = []
    mae_values: list[float] = []
    for record in records:
        if _frame_should_be_unknown(record, exercise) or _status(record) == "UNKNOWN":
            unknown_count += 1
            continue
        status = _status(record)
        if status == "PASS":
            pass_count += 1
        elif status == "NEAR":
            near_count += 1
        else:
            fail_count += 1
        shoulder, elbow = _angle_values(record, exercise)
        shoulder_ref, elbow_ref = _ref_values(record)
        if shoulder is not None:
            shoulder_values.append(shoulder)
        if elbow is not None:
            elbow_values.append(elbow)
        if shoulder_ref is not None:
            shoulder_refs.append(shoulder_ref)
        if elbow_ref is not None:
            elbow_refs.append(elbow_ref)
        if shoulder is not None and shoulder_ref is not None:
            mae_values.append(abs(shoulder - shoulder_ref))
        if elbow is not None and elbow_ref is not None:
            mae_values.append(abs(elbow - elbow_ref))
    valid = pass_count + near_count + fail_count
    accuracy = (pass_count / valid * 100.0) if valid else 0.0
    precision = pass_count / max(1, pass_count + fail_count) if valid else 0.0
    recall = pass_count / max(1, valid) if valid else 0.0
    f1 = (2 * precision * recall / max(0.0001, precision + recall)) if valid else 0.0
    phase_counts = {key: {"PASS": 0, "NEAR": 0, "FAIL": 0} for key in ("g1", "g2", "g3")}
    if _exercise_key(exercise) == "codman":
        for record in records:
            if _frame_should_be_unknown(record, exercise) or _status(record) == "UNKNOWN":
                continue
            phase_key = _clean_text(record.get("phase"))
            if phase_key not in phase_counts:
                continue
            status = _status(record)
            if status in phase_counts[phase_key]:
                phase_counts[phase_key][status] += 1

    def phase_accuracy(key: str) -> float:
        counts = phase_counts[key]
        denominator = counts["PASS"] + counts["NEAR"] + counts["FAIL"]
        return round((counts["PASS"] / denominator * 100.0) if denominator else 0.0, 2)

    return {
        "do_chinh_xac": round(accuracy, 2),
        "ty_le_tong_the": round(accuracy, 2),
        "ty_le_gan_dung": round((near_count / valid * 100.0) if valid else 0.0, 2),
        "ty_le_vai_dung": round(accuracy, 2),
        "ty_le_khuyu_dung": round(accuracy, 2),
        "frame_dung": pass_count,
        "frame_gan_dung": near_count,
        "frame_sai": fail_count,
        "frame_khong_nhan_dang": unknown_count,
        "tong_frame_hop_le": valid,
        "tong_frame_da_cham": len(records),
        "tb_goc_vai": round(sum(shoulder_values) / len(shoulder_values), 3) if shoulder_values else 0,
        "tb_goc_khuyu": round(sum(elbow_values) / len(elbow_values), 3) if elbow_values else 0,
        "min_goc_vai": min(shoulder_values) if shoulder_values else 0,
        "max_goc_vai": max(shoulder_values) if shoulder_values else 0,
        "min_goc_khuyu": min(elbow_values) if elbow_values else 0,
        "max_goc_khuyu": max(elbow_values) if elbow_values else 0,
        "mae_tong": round(sum(mae_values) / len(mae_values), 3) if mae_values else 0.0,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "tb_vai_chuan": round(sum(shoulder_refs) / len(shoulder_refs), 3) if shoulder_refs else 0,
        "tb_khuyu_chuan": round(sum(elbow_refs) / len(elbow_refs), 3) if elbow_refs else 0,
        "ref_source": "youtube_mediapipe" if _exercise_key(exercise) in {"codman", "pulley"} else "default",
        "exercise_key": _exercise_key(exercise),
        "phase_accuracy_g1": phase_accuracy("g1"),
        "phase_accuracy_g2": phase_accuracy("g2"),
        "phase_accuracy_g3": phase_accuracy("g3"),
        "thoi_gian": 0.0,
        "tong_frame": len(records),
    }


def _path_snapshot(raw_path: Any) -> dict[str, Any] | None:
    text = _clean_text(raw_path)
    if not text:
        return None
    path = _resolve_existing_path(text)
    info: dict[str, Any] = {"path": text, "exists": bool(path and path.is_file())}
    if path and path.is_file():
        stat = path.stat()
        info.update(
            {
                "resolved_path": _relative_repo_path(path),
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return info


def _bundle_entry(video: dict[str, Any], detail_id: int) -> dict[str, Any]:
    records = _load_records(_records_path(video))
    processed = _resolve_existing_path(video.get("processed_path"))
    frame_total = len(records) or _video_frame_count(processed)
    paths = dict(video.get("paths") if isinstance(video.get("paths"), dict) else {})
    for key in ("video_path", "raw_video_path", "processed_path", "df_path", "all_frames_data_path", "frames_zip", "frames_zip_path"):
        if video.get(key):
            paths[key] = _path_snapshot(video.get(key))
    return {
        "detail_id": detail_id,
        "video_name": video.get("video_name"),
        "patient_username": video.get("patient_username") or video.get("username"),
        "full_name": video.get("full_name"),
        "exercise": video.get("exercise"),
        "status": video.get("status"),
        "accuracy": video.get("accuracy"),
        "time": video.get("time"),
        "uploaded_at": video.get("uploaded_at"),
        "artifact_updated_at": video.get("artifact_updated_at"),
        "metrics": video.get("metrics") if isinstance(video.get("metrics"), dict) else {},
        "frame_total": frame_total,
        "paths": paths,
        "has_video_file": bool(processed and processed.is_file()),
        "has_frames": bool(records or _resolve_existing_path(video.get("frames_zip") or video.get("frames_zip_path"))),
        "has_chart": bool(_resolve_existing_path(video.get("df_path")) or video.get("accuracy") is not None),
    }


def _load_records(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("frames") or data.get("all_frames") or data.get("data") if isinstance(data, dict) else data
    return [row for row in rows if isinstance(row, dict)]


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    preferred = [
        "frame",
        "index",
        "timestamp",
        "timestamp_seconds",
        "exercise",
        "exercise_key",
        "goc_vai",
        "goc_khuyu",
        "goc_vai_trai",
        "goc_khuyu_trai",
        "goc_vai_phai",
        "goc_khuyu_phai",
        "shoulder_ref",
        "elbow_ref",
        "shoulder_ref_left",
        "elbow_ref_left",
        "shoulder_ref_right",
        "elbow_ref_right",
        "dung",
        "gan_dung",
        "phase",
        "phase_label",
        "threshold",
        "phase_threshold",
        "phase_status",
        "status",
        "detected",
        "filtered_stranger",
        "stranger_reason",
        "ref_source",
        "youtube_ref_exercise_id",
        "motion_subtype",
        "motion_type",
        "youtube_ref_time",
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
    pose_keys = [f"pt{idx}_{suffix}" for idx in range(33) for suffix in ("x", "y", "z", "vis")]
    fieldnames: list[str] = []
    for key in [*preferred, *pose_keys]:
        if any(key in record for record in records):
            fieldnames.append(key)
    for record in records:
        for key in record:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in fieldnames})


def _write_records_json(path: Path, records: list[dict[str, Any]]) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write("[")
        for idx, record in enumerate(records):
            if idx:
                handle.write(",")
            json.dump(record, handle, ensure_ascii=False)
        handle.write("]")
    tmp_path.replace(path)


def _records_path(video: dict[str, Any]) -> Path | None:
    path = _resolve_existing_path(video.get("all_frames_data_path"))
    if path and path.is_file():
        return path
    processed = _resolve_existing_path(video.get("processed_path"))
    stem = (processed.stem if processed else "").removesuffix("_sound").removesuffix("_f").removesuffix("_pose_h264")
    if stem.startswith("processed_"):
        candidate = ROOT / "processed_results" / f"f_{stem.removeprefix('processed_')}.json"
        if candidate.is_file():
            return candidate
    return None


def _csv_path(video: dict[str, Any], records_path: Path | None) -> Path | None:
    direct = _resolve_existing_path(video.get("df_path"))
    if direct and direct.is_file():
        return direct
    if records_path:
        stem = records_path.stem.removeprefix("f_")
        for suffix in ("_f_data.csv", "_data.csv"):
            candidate = ROOT / "processed_results" / f"processed_{stem}{suffix}"
            if candidate.is_file():
                return candidate
    return None


def _normalise_unknown(record: dict[str, Any], exercise: Any) -> dict[str, Any]:
    output = _recompute_pose_angles(dict(record), exercise)
    output.setdefault("exercise", exercise)
    output.setdefault("exercise_key", _exercise_key(exercise))
    if _frame_should_be_unknown(output, exercise):
        output["status"] = "UNKNOWN"
        output["phase_status"] = "UNKNOWN"
        output["dung"] = False
        output["gan_dung"] = False
    elif _to_bool(output.get("filtered_stranger")):
        output["filtered_stranger"] = False
        output["stranger_reason"] = None
    return output


def _refresh_records(video: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    exercise = video.get("exercise") or video.get("video_name")
    records_path = _records_path(video)
    records = [_normalise_unknown(record, exercise) for record in _load_records(records_path)]
    if not records_path or not records:
        return [], {}

    for position, record in enumerate(records):
        record.setdefault("index", record.get("frame") or position + 1)
        record.setdefault("frame", record.get("index") or position + 1)
        if _exercise_key(exercise) == "pulley":
            record.setdefault("phase", "overview")
            record.setdefault("phase_label", "Tổng quan")
            record.setdefault("threshold", 30)
            record.setdefault("phase_threshold", 30)
        elif not record.get("phase"):
            total = len(records)
            ratio = position / max(1, total)
            if ratio < 1 / 3:
                record["phase"], record["phase_label"], record["threshold"] = "g1", "Giai đoạn 1", 45
            elif ratio < 2 / 3:
                record["phase"], record["phase_label"], record["threshold"] = "g2", "Giai đoạn 2", 30
            else:
                record["phase"], record["phase_label"], record["threshold"] = "g3", "Giai đoạn 3", 15
            record.setdefault("phase_threshold", record["threshold"])
        if _frame_should_be_unknown(record, exercise):
            record["status"] = "UNKNOWN"
            record["phase_status"] = "UNKNOWN"
            record["dung"] = False
            record["gan_dung"] = False
            continue
        status = _status(record)
        record["status"] = status
        record["phase_status"] = status
        record["dung"] = status == "PASS"
        record["gan_dung"] = status == "NEAR"

    existing_metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    metrics = dict(existing_metrics)
    metrics.update(_analysis_metrics(records, exercise))
    metrics["metrics_refreshed_at"] = _now_iso()
    _write_records_json(records_path, records)
    csv_path = _csv_path(video, records_path)
    if csv_path:
        _write_csv(csv_path, records)
        video["df_path"] = _relative_repo_path(csv_path)
    video["all_frames_data_path"] = _relative_repo_path(records_path)
    video["metrics"] = metrics
    video["accuracy"] = round(float(metrics.get("do_chinh_xac") or 0), 2)
    video["status"] = "Đã phân tích"
    video["artifact_updated_at"] = _now_iso()
    return records, metrics


def _fix_cao_pulley(video: dict[str, Any]) -> None:
    combined = _search_text(" ".join(_clean_text(video.get(key)) for key in ("username", "patient_username", "full_name", "video_name", "exercise")))
    if not all(token in combined for token in ("cao", "thi", "thuong")) or _exercise_key(video.get("exercise") or video.get("video_name")) != "pulley":
        return
    raw_path = _find_patient_upload("cao", "042916", "_f")
    if raw_path and _video_frame_count(raw_path) > 0:
        raw = _relative_repo_path(raw_path)
        video["video_path"] = raw
        video["raw_video_path"] = raw
    video["video_name"] = CAO_PULLEY_VIDEO_NAME


def _sync_root_video_list(database_videos: list[dict[str, Any]], root_videos: list[Any]) -> None:
    while len(root_videos) < len(database_videos):
        root_videos.append({})
    for index in TARGET_INDICES:
        if index >= len(database_videos) or not isinstance(database_videos[index], dict):
            continue
        source = database_videos[index]
        target = dict(root_videos[index] if isinstance(root_videos[index], dict) else {})
        for key in ROOT_SYNC_KEYS:
            if key in source and source.get(key) is not None:
                target[key] = source[key]
        source_metrics = source.get("metrics") if isinstance(source.get("metrics"), dict) else {}
        target_metrics = dict(target.get("metrics") if isinstance(target.get("metrics"), dict) else {})
        for key in ROOT_METRIC_KEYS:
            if key in source_metrics:
                target_metrics[key] = source_metrics[key]
        if target_metrics:
            target["metrics"] = target_metrics
        source_paths = source.get("paths") if isinstance(source.get("paths"), dict) else {}
        target_paths = dict(target.get("paths") if isinstance(target.get("paths"), dict) else {})
        for key in ("video_path", "raw_video_path", "processed_path", "df_path", "all_frames_data_path", "frames_zip", "frames_zip_path"):
            if key in source_paths and source_paths[key] is not None:
                target_paths[key] = source_paths[key]
        if target_paths:
            target["paths"] = target_paths
        root_videos[index] = target


def _bundle_for_target_indices(database_videos: list[dict[str, Any]]) -> dict[str, Any]:
    now = _now_iso()
    selected = []
    for index in TARGET_INDICES:
        if not (0 <= index < len(database_videos)) or not isinstance(database_videos[index], dict):
            continue
        item = dict(database_videos[index])
        item["_detail_id"] = index
        item["latest_bundle_updated_at"] = now
        database_videos[index]["latest_bundle_updated_at"] = now
        selected.append(item)
    return {
        "updated_at": now,
        "updated_by": "system",
        "scope": "canonical_eight_video_pose_bundle",
        "limit": len(TARGET_INDICES),
        "target_indices": TARGET_INDICES,
        "video_count": len(selected),
        "database_source": str(ROOT / "database" / "video_list.json"),
        "artifact_results": [],
        "dataset_manifest": "database/dataset/dataset_manifest.json",
        "dataset_results": [],
        "videos": [_bundle_entry(item, int(item.get("_detail_id") or position)) for position, item in enumerate(selected)],
    }


def main_cli() -> int:
    db_path = ROOT / "database" / "video_list.json"
    root_path = ROOT / "video_list.json"
    database_videos = json.loads(db_path.read_text(encoding="utf-8"))
    root_videos = json.loads(root_path.read_text(encoding="utf-8"))

    results = []
    for index in TARGET_INDICES:
        video = database_videos[index]
        _fix_cao_pulley(video)
        records, metrics = _refresh_records(video)
        results.append(
            {
                "index": index,
                "video": video.get("video_name"),
                "records": len(records),
                "accuracy": metrics.get("do_chinh_xac"),
                "pass": metrics.get("frame_dung"),
                "near": metrics.get("frame_gan_dung"),
                "fail": metrics.get("frame_sai"),
                "unknown": metrics.get("frame_khong_nhan_dang"),
            }
        )

    bundle = _bundle_for_target_indices(database_videos)
    write_json(ROOT / "database" / "latest_video_bundle.json", bundle)
    dataset_dir = ROOT / "database" / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    write_json(dataset_dir / "latest_video_bundle.json", bundle)

    _sync_root_video_list(database_videos, root_videos)
    write_json(db_path, database_videos)
    write_json(root_path, root_videos)

    payload = json.dumps(
        {
            "updated": results,
            "bundle_updated_at": bundle.get("updated_at"),
            "bundle_video_count": bundle.get("video_count"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.buffer.write(payload.encode("utf-8", errors="backslashreplace") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import main  # noqa: E402
from storage.json_store import read_json, write_json  # noqa: E402


TARGET_INDICES = [0, 1, 2, 3, 4, 5, 6, 7]


def _records_for_video(video: dict[str, object]) -> list[dict[str, object]]:
    frame_path = main._resolve_existing_path(video.get("all_frames_data_path"))
    csv_path = main._resolve_existing_path(video.get("df_path"))
    records = main._read_frame_records(frame_path)
    sample = records[: min(24, len(records))]
    has_pose = bool(sample) and any(main._has_complete_pose(record) for record in sample)
    has_ml = bool(sample) and any(main._frame_ml_label(record) for record in sample)
    csv_records = main._frame_records_from_csv(csv_path) if csv_path and (not records or not (has_pose and has_ml)) else []
    if records and csv_records:
        records = main._merge_frame_records_with_csv_pose(records, csv_records)
    elif csv_records:
        records = csv_records
    exercise = video.get("exercise") or video.get("video_name") or ""
    contextual: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        item = main._frame_with_exercise_context(record, exercise)
        contextual.append(item)
    return contextual


def _status_for_record(record: dict[str, object], exercise: object) -> str:
    if main._to_bool(record.get("filtered_stranger")):
        return "UNKNOWN"
    status = str(record.get("phase_status") or record.get("status") or "").upper()
    if status in {"PASS", "NEAR", "FAIL", "UNKNOWN"}:
        return status
    if main._to_bool(record.get("dung")):
        return "PASS"
    if main._to_bool(record.get("gan_dung")):
        return "NEAR"
    threshold = main._to_float(record.get("threshold") or record.get("phase_threshold"))
    if threshold is None:
        threshold = 30 if main._is_pulley_exercise(exercise) else 45
    return main._phase_status_for_frame(record, float(threshold), exercise=exercise) or "FAIL"


def _ml_counts(records: list[dict[str, object]], exercise: object) -> dict[str, object]:
    counts = {"ml_frame_dung": 0, "ml_frame_gan_dung": 0, "ml_frame_sai": 0, "ml_frame_unknown": 0}
    confidences: list[float] = []
    for record in records:
        if main._frame_should_be_unknown(record, exercise):
            counts["ml_frame_unknown"] += 1
            continue
        label = main._search_text(main._frame_ml_label(record))
        if "gan" in label or "near" in label:
            counts["ml_frame_gan_dung"] += 1
        elif "dung" in label or "pass" in label or label == "2":
            counts["ml_frame_dung"] += 1
        elif label:
            counts["ml_frame_sai"] += 1
        conf = main._frame_ml_confidence(record)
        if conf is not None:
            confidences.append(float(conf))
    scored = counts["ml_frame_dung"] + counts["ml_frame_gan_dung"] + counts["ml_frame_sai"]
    counts["ml_tong_frame"] = scored
    counts["ml_do_chinh_xac"] = round((counts["ml_frame_dung"] / scored * 100) if scored else 0.0, 2)
    counts["ml_confidence_tb"] = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    return counts


def refresh_video(video: dict[str, object]) -> dict[str, object]:
    exercise = video.get("exercise") or video.get("video_name") or ""
    records = _records_for_video(video)
    pass_count = near_count = fail_count = unknown_count = 0
    shoulder_values: list[float] = []
    elbow_values: list[float] = []
    shoulder_refs: list[float] = []
    elbow_refs: list[float] = []
    mae_values: list[float] = []
    for record in records:
        status = _status_for_record(record, exercise)
        if status == "UNKNOWN":
            unknown_count += 1
            continue
        if status == "PASS":
            pass_count += 1
        elif status == "NEAR":
            near_count += 1
        else:
            fail_count += 1
        shoulder, elbow = main._frame_angle_values(record, exercise)
        if shoulder is not None:
            shoulder_values.append(float(shoulder))
        if elbow is not None:
            elbow_values.append(float(elbow))
        shoulder_ref, elbow_ref = main._frame_ref_values(record)
        fallback_shoulder, fallback_elbow = main._default_refs_for_exercise(exercise)
        shoulder_ref = shoulder_ref if shoulder_ref is not None else fallback_shoulder
        elbow_ref = elbow_ref if elbow_ref is not None else fallback_elbow
        if shoulder_ref is not None:
            shoulder_refs.append(float(shoulder_ref))
        if elbow_ref is not None:
            elbow_refs.append(float(elbow_ref))
        shoulder_delta, elbow_delta = main._frame_delta_values(record, (shoulder_ref, elbow_ref), exercise)
        if shoulder_delta is not None:
            mae_values.append(float(shoulder_delta))
        if elbow_delta is not None:
            mae_values.append(float(elbow_delta))
    valid = pass_count + near_count + fail_count
    accuracy = (pass_count / valid * 100) if valid else 0.0
    metrics = {
        "do_chinh_xac": round(accuracy, 2),
        "ty_le_tong_the": round(accuracy, 2),
        "ty_le_gan_dung": round((near_count / valid * 100) if valid else 0.0, 2),
        "ty_le_vai_dung": round(accuracy, 2),
        "ty_le_khuyu_dung": round(accuracy, 2),
        "frame_dung": pass_count,
        "frame_gan_dung": near_count,
        "frame_sai": fail_count,
        "frame_khong_nhan_dang": unknown_count,
        "tong_frame_hop_le": valid,
        "tong_frame_da_cham": valid + unknown_count,
        "tb_goc_vai": round(sum(shoulder_values) / len(shoulder_values), 3) if shoulder_values else 0,
        "tb_goc_khuyu": round(sum(elbow_values) / len(elbow_values), 3) if elbow_values else 0,
        "min_goc_vai": min(shoulder_values) if shoulder_values else 0,
        "max_goc_vai": max(shoulder_values) if shoulder_values else 0,
        "min_goc_khuyu": min(elbow_values) if elbow_values else 0,
        "max_goc_khuyu": max(elbow_values) if elbow_values else 0,
        "std_goc_vai": statistics.pstdev(shoulder_values) if len(shoulder_values) > 1 else 0,
        "std_goc_khuyu": statistics.pstdev(elbow_values) if len(elbow_values) > 1 else 0,
        "mae_tong": round(sum(mae_values) / len(mae_values), 3) if mae_values else 0,
        "precision": round(pass_count / max(1, pass_count + fail_count), 3) if valid else 0,
        "recall": round(pass_count / max(1, valid), 3) if valid else 0,
        "f1_score": round((2 * pass_count) / max(1, 2 * pass_count + fail_count + near_count), 3) if valid else 0,
        "icc": 0.0,
        "tb_vai_chuan": round(sum(shoulder_refs) / len(shoulder_refs), 3) if shoulder_refs else main._default_refs_for_exercise(exercise)[0],
        "tb_khuyu_chuan": round(sum(elbow_refs) / len(elbow_refs), 3) if elbow_refs else main._default_refs_for_exercise(exercise)[1],
        "ref_source": "youtube_mediapipe" if main._exercise_key(exercise) in {"codman", "pulley"} else "default",
        "exercise_key": main._exercise_key(exercise),
        "thoi_gian": 0.0,
    }
    metrics.update(_ml_counts(records, exercise))
    previous = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    for key in ("audio_status", "audio_events", "audio_path", "rendered_playback_frames", "playback_render_source"):
        if key in previous and key not in metrics:
            metrics[key] = previous[key]
    metrics["tong_frame"] = len(records)
    metrics["metrics_refreshed_at"] = main._now_iso()
    video["metrics"] = metrics
    video["accuracy"] = round(float(metrics.get("do_chinh_xac") or 0), 1)
    video["status"] = "Đã phân tích"
    return {
        "video_name": video.get("video_name"),
        "accuracy": video["accuracy"],
        "pass": metrics.get("frame_dung"),
        "near": metrics.get("frame_gan_dung"),
        "fail": metrics.get("frame_sai"),
        "unknown": metrics.get("frame_khong_nhan_dang"),
        "total": metrics.get("tong_frame"),
        "ml_accuracy": metrics.get("ml_do_chinh_xac"),
    }


def main_cli() -> int:
    path = REPO_ROOT / "database" / "video_list.json"
    videos = read_json(path, [])
    if not isinstance(videos, list):
        raise RuntimeError("database/video_list.json must be a list")
    results = []
    for index in TARGET_INDICES:
        if index >= len(videos) or not isinstance(videos[index], dict):
            continue
        results.append({"index": index, **refresh_video(videos[index])})
    write_json(path, videos)
    print(json.dumps({"updated": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

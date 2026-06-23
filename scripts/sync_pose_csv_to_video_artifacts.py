from __future__ import annotations

import csv
import json
import argparse
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import main  # noqa: E402
from storage.json_store import write_json  # noqa: E402


# Canonical 8-video bundle: 4 patients x 2 exercises.
# Index 13 is a duplicate Nguyen Thi Nga pulley slot with stale ftmp artifacts;
# index 6 is the complete, upright, REF-linked Nguyen Thi Nga pulley artifact.
TARGET_INDICES = [12, 10, 11, 1, 9, 6, 8, 4]
CSV_ALIAS_SUFFIXES = ("_f_data.csv", "_data.csv")


def _load_records(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("frames") or data.get("data") if isinstance(data, dict) else data
    return [row for row in rows if isinstance(row, dict)]


def _read_csv_records(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            item: dict[str, Any] = {}
            for key, value in row.items():
                if value in (None, ""):
                    continue
                number = main._to_float(value)
                if number is not None:
                    item[key] = number
                else:
                    item[key] = value
            item.setdefault("index", item.get("frame") or item.get("frame_idx") or item.get("frame_number") or index + 1)
            rows.append(item)
    return rows


def _csv_path_for_video(video: dict[str, Any], records_path: Path | None) -> Path | None:
    direct = main._resolve_existing_path(video.get("df_path"))
    if direct and direct.is_file():
        return direct
    processed = main._resolve_existing_path(video.get("processed_path"))
    stems: list[str] = []
    for path in (processed, records_path):
        if not path:
            continue
        stem = path.stem
        if stem.startswith("f_"):
            stems.append(f"processed_{stem.removeprefix('f_')}")
        else:
            for suffix in ("_sound", "_f", "_pose_h264", "_skeleton_h264", "_h264"):
                if stem.endswith(suffix):
                    stem = stem[: -len(suffix)]
            stems.append(stem)
    for stem in dict.fromkeys(stems):
        for suffix in CSV_ALIAS_SUFFIXES:
            candidate = REPO_ROOT / "processed_results" / f"{stem}{suffix}"
            if candidate.is_file():
                return candidate
    return None


def _records_path_for_video(video: dict[str, Any]) -> Path | None:
    path = main._resolve_existing_path(video.get("all_frames_data_path"))
    if path and path.is_file():
        return path
    processed = main._resolve_existing_path(video.get("processed_path"))
    if processed:
        stem = main._processed_stem(processed)
        if stem.startswith("processed_"):
            candidate = REPO_ROOT / "processed_results" / f"f_{stem.removeprefix('processed_')}.json"
            if candidate.is_file():
                return candidate
    return None


def _merge_records(records: list[dict[str, Any]], csv_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return csv_records
    if not csv_records:
        return records
    csv_lookup = main._frame_record_lookup(csv_records)
    output: list[dict[str, Any]] = []
    for position, record in enumerate(records):
        frame_number = main._frame_number_key(record.get("index") or record.get("frame") or record.get("frame_number")) or position + 1
        csv_record = csv_lookup.get(frame_number, (None, None))[1]
        if not isinstance(csv_record, dict) and position < len(csv_records):
            csv_record = csv_records[position]
        merged = dict(record)
        if isinstance(csv_record, dict):
            for key, value in csv_record.items():
                if value in (None, ""):
                    continue
                if key.startswith("pt") or merged.get(key) in (None, "") or key in {
                    "frame",
                    "timestamp",
                    "timestamp_seconds",
                    "ml_label",
                    "ml_label_text",
                    "dung_ml",
                    "gan_dung_ml",
                    "ml_score",
                    "ml_confidence",
                    "ml_prob_sai",
                    "ml_prob_gan_dung",
                    "ml_prob_dung",
                }:
                    merged[key] = value
        output.append(merged)
    return output


def _ensure_reference_aliases(record: dict[str, Any], exercise: Any) -> None:
    exercise_key = main._exercise_key(exercise)
    if exercise_key in {"codman", "pulley"} and main._has_complete_pose(record):
        missing_youtube_meta = (
            record.get("ref_source") != "youtube_mediapipe"
            or record.get("youtube_ref_time") in (None, "")
            or record.get("youtube_ref_exercise_id") in (None, "")
        )
        if missing_youtube_meta or not main._has_saved_reference_values(record):
            record.update(main._apply_youtube_reference_to_frame(record, exercise, overwrite=missing_youtube_meta))
    shoulder_ref, elbow_ref = main._frame_ref_values(record)
    fallback_shoulder, fallback_elbow = main._default_refs_for_exercise(exercise)
    shoulder_ref = shoulder_ref if shoulder_ref is not None else fallback_shoulder
    elbow_ref = elbow_ref if elbow_ref is not None else fallback_elbow
    if shoulder_ref is not None:
        record.setdefault("shoulder_ref", shoulder_ref)
        record.setdefault("vai_chuan", shoulder_ref)
    if elbow_ref is not None:
        record.setdefault("elbow_ref", elbow_ref)
        record.setdefault("khuyu_chuan", elbow_ref)
    if exercise_key == "pulley":
        for side in ("left", "right"):
            side_shoulder, side_elbow = main._frame_ref_side_values(record, side)
            side_shoulder = side_shoulder if side_shoulder is not None else shoulder_ref
            side_elbow = side_elbow if side_elbow is not None else elbow_ref
            if side == "left":
                if side_shoulder is not None:
                    record.setdefault("shoulder_ref_left", side_shoulder)
                    record.setdefault("vai_chuan_trai", side_shoulder)
                if side_elbow is not None:
                    record.setdefault("elbow_ref_left", side_elbow)
                    record.setdefault("khuyu_chuan_trai", side_elbow)
            else:
                if side_shoulder is not None:
                    record.setdefault("shoulder_ref_right", side_shoulder)
                    record.setdefault("vai_chuan_phai", side_shoulder)
                if side_elbow is not None:
                    record.setdefault("elbow_ref_right", side_elbow)
                    record.setdefault("khuyu_chuan_phai", side_elbow)
    if exercise_key in {"codman", "pulley"}:
        record.setdefault("ref_source", "youtube_mediapipe")


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    keys: list[str] = []
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
    for key in [*preferred, *pose_keys]:
        if any(key in record for record in records):
            keys.append(key)
    for record in records:
        for key in record:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows({key: record.get(key, "") for key in keys} for record in records)


def _status_counts(records: list[dict[str, Any]], exercise: Any) -> dict[str, int]:
    counts = {"PASS": 0, "NEAR": 0, "FAIL": 0, "UNKNOWN": 0}
    for record in records:
        status_text = main._phase_status_for_frame(
            record,
            float(main._to_float(record.get("threshold") or record.get("phase_threshold")) or (30 if main._exercise_key(exercise) == "pulley" else 45)),
            main._default_refs_for_exercise(exercise),
            exercise,
        )
        counts[status_text if status_text in counts else "FAIL"] += 1
    return counts


def _sync_one(video: dict[str, Any], index: int) -> dict[str, Any]:
    exercise = video.get("exercise") or video.get("video_name")
    records_path = _records_path_for_video(video)
    csv_path = _csv_path_for_video(video, records_path)
    if not records_path or not csv_path:
        return {"index": index, "skipped": "missing_json_or_csv", "video": video.get("video_name")}
    records = _merge_records(_load_records(records_path), _read_csv_records(csv_path))
    records = [main._frame_with_exercise_context(record, exercise) for record in records]
    for record in records:
        _ensure_reference_aliases(record, exercise)
    main._apply_phase_thresholds_to_records(records, exercise)
    for record in records:
        _ensure_reference_aliases(record, exercise)
    metrics = main._analysis_metrics(records, len(records), 0.0, exercise)
    records_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    _write_csv(csv_path, records)

    processed = main._resolve_existing_path(video.get("processed_path"))
    stem = main._processed_stem(processed) if processed else f"processed_{records_path.stem.removeprefix('f_')}"
    frame_zip = main._resolve_existing_path(video.get("frames_zip") or video.get("frames_zip_path"))
    inferred_zip = REPO_ROOT / "processed_results" / f"{stem}_frames.zip"
    if not frame_zip and inferred_zip.is_file():
        frame_zip = inferred_zip

    video["all_frames_data_path"] = main._relative_repo_path(records_path)
    video["df_path"] = main._relative_repo_path(csv_path)
    if frame_zip and frame_zip.is_file():
        video["frames_zip"] = main._relative_repo_path(frame_zip)
        video["frames_zip_path"] = main._relative_repo_path(frame_zip)
    video["metrics"] = metrics
    video["accuracy"] = round(float(metrics.get("do_chinh_xac") or 0), 2)
    video["status"] = "Đã phân tích"
    video["artifact_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    counts = _status_counts(records, exercise)
    return {
        "index": index,
        "video": video.get("video_name"),
        "records": len(records),
        "pose_missing": sum(1 for record in records if not main._has_complete_pose(record)),
        "counts": counts,
        "json": video.get("all_frames_data_path"),
        "csv": video.get("df_path"),
        "zip": video.get("frames_zip"),
    }


def _load_video_lists() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    database = json.loads((REPO_ROOT / "database" / "video_list.json").read_text(encoding="utf-8"))
    root = json.loads((REPO_ROOT / "video_list.json").read_text(encoding="utf-8"))
    return database, root


def _copy_synced_fields(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key in (
        "all_frames_data_path",
        "df_path",
        "frames_zip",
        "frames_zip_path",
        "metrics",
        "accuracy",
        "status",
        "artifact_updated_at",
    ):
        if key in source:
            target[key] = source[key]


def _parse_indices(raw_values: list[str] | None) -> list[int]:
    if not raw_values:
        return TARGET_INDICES
    output: list[int] = []
    for raw in raw_values:
        for item in str(raw).split(","):
            item = item.strip()
            if not item:
                continue
            output.append(int(item))
    return output


def main_cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indices", nargs="*", help="Video indices to sync, comma-separated values are accepted.")
    args = parser.parse_args()
    target_indices = _parse_indices(args.indices)
    database_videos, root_videos = _load_video_lists()
    results = []
    for index in target_indices:
        if index >= len(database_videos) or not isinstance(database_videos[index], dict):
            continue
        result = _sync_one(database_videos[index], index)
        results.append(result)
        if index < len(root_videos) and isinstance(root_videos[index], dict):
            _copy_synced_fields(root_videos[index], database_videos[index])
        write_json(REPO_ROOT / "database" / "video_list.json", database_videos)
        write_json(REPO_ROOT / "video_list.json", root_videos)
    print(json.dumps({"updated": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

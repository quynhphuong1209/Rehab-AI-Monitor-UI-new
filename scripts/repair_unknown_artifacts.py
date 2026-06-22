from __future__ import annotations

import csv
import json
import sys
import time
import zipfile
from pathlib import Path

import cv2
import mediapipe as mp

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import (  # noqa: E402
    CHART_PAYLOAD_CACHE,
    DATABASE_DIR,
    PHASE_THRESHOLDS,
    REPO_ROOT,
    _analysis_metrics,
    _apply_youtube_reference_to_frame,
    _clean_text,
    _default_refs_for_exercise,
    _draw_pose_analysis_overlay,
    _exercise_key,
    _exercise_label,
    _frame_exercise_key,
    _frame_number_key,
    _frame_with_detected_pose,
    _frame_with_exercise_context,
    _load_data,
    _mark_filtered_stranger,
    _phase_for_position,
    _phase_status_for_frame,
    _relative_repo_path,
    _resolve_existing_path,
    _resolve_video_source_path,
    _save_data,
    _to_bool,
    _to_float,
    _video_frame_count,
)


def write_records_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for record in records for key in record.keys() if not isinstance(record.get(key), (dict, list))})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: record.get(key) for key in fieldnames} for record in records)


def render_artifacts(source: Path, output_video: Path, frames_zip: Path, records: list[dict], exercise: str, fps: float) -> int:
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        return 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 720
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1280
    if output_video.is_file():
        existing = cv2.VideoCapture(str(output_video))
        out_w = int(existing.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        out_h = int(existing.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        existing.release()
        if out_w > 0 and out_h > 0:
            width, height = out_w, out_h
    tmp_video = output_video.with_name(f"{output_video.stem}_repair_tmp.mp4")
    tmp_zip = frames_zip.with_name(f"{frames_zip.stem}_repair_tmp.zip")
    tmp_video.unlink(missing_ok=True)
    tmp_zip.unlink(missing_ok=True)
    writer = cv2.VideoWriter(str(tmp_video), cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, fps), (width, height))
    if not writer.isOpened():
        cap.release()
        return 0
    done = 0
    last = time.time()
    try:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for pos, record in enumerate(records):
                frame_no = _frame_number_key(record.get("frame") or record.get("index") or record.get("frame_number")) or pos + 1
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_no - 1))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                if (frame.shape[1], frame.shape[0]) != (width, height):
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA if width < frame.shape[1] else cv2.INTER_LINEAR)
                threshold = _to_float(record.get("threshold") or record.get("phase_threshold"))
                if threshold is None:
                    _, _, threshold = _phase_for_position(pos, len(records), exercise)
                rendered = _draw_pose_analysis_overlay(frame, record, int(frame_no), threshold=float(threshold))
                writer.write(rendered)
                ok_jpg, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok_jpg:
                    archive.writestr(f"f_{pos + 1:06d}.jpg", encoded.tobytes())
                done += 1
                if done == 1 or done % 100 == 0 or time.time() - last >= 5:
                    print(f"render {done}/{len(records)}", flush=True)
                    last = time.time()
    finally:
        cap.release()
        writer.release()
    if done:
        tmp_video.replace(output_video)
        tmp_zip.replace(frames_zip)
    else:
        tmp_video.unlink(missing_ok=True)
        tmp_zip.unlink(missing_ok=True)
    return done


def main() -> int:
    needle = " ".join(sys.argv[1:]).strip().lower() or "cao codman"
    videos = _load_data("video_list")
    matches = []
    for idx, video in enumerate(videos):
        if not isinstance(video, dict):
            continue
        text = " ".join(str(video.get(key, "")) for key in ("video_name", "username", "full_name", "patient_username", "exercise")).lower()
        if all(part in text for part in needle.split()):
            matches.append((idx, video))
    if not matches:
        print(f"no video matched: {needle}")
        return 2
    idx, video = matches[0]
    exercise = _exercise_label(video.get("exercise") or video.get("video_name"))
    exercise_key = _exercise_key(exercise)
    if exercise_key not in {"codman", "pulley"}:
        print(f"unsupported exercise: {exercise}")
        return 3
    source = _resolve_video_source_path(video.get("video_path")) or _resolve_video_source_path(video.get("processed_path"))
    processed = _resolve_existing_path(video.get("processed_path")) or (REPO_ROOT / "processed_results" / f"repair_{idx}.mp4")
    frames_path = _resolve_existing_path(video.get("all_frames_data_path"))
    csv_path = _resolve_existing_path(video.get("df_path")) or processed.with_name(f"{processed.stem}_data.csv")
    frames_zip = _resolve_existing_path(video.get("frames_zip") or video.get("frames_zip_path")) or processed.with_name(f"{processed.stem}_frames.zip")
    if not source or not source.is_file() or not frames_path or not frames_path.is_file():
        print("missing source or frames", source, frames_path)
        return 4
    records = json.loads(frames_path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        print("empty records")
        return 5
    cap = cv2.VideoCapture(str(source))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    cap.release()
    unknown_before = sum(1 for row in records if isinstance(row, dict) and (_to_bool(row.get("filtered_stranger")) or _clean_text(row.get("status")).upper() == "UNKNOWN"))
    print(f"repair video index={idx} name={video.get('video_name')} frames={len(records)} unknown_before={unknown_before}", flush=True)
    updated = 0
    last = time.time()
    cap = cv2.VideoCapture(str(source))
    with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1 if exercise_key == "codman" else 2, enable_segmentation=False, min_detection_confidence=0.35) as pose:
        for pos, row in enumerate(records):
            if not isinstance(row, dict):
                continue
            frame_no = _frame_number_key(row.get("index") or row.get("frame") or row.get("frame_idx") or row.get("frame_number")) or pos + 1
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_no - 1))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            before = (_to_bool(row.get("filtered_stranger")), _clean_text(row.get("status")).upper())
            row = _frame_with_exercise_context(row, exercise)
            row = _frame_with_detected_pose(frame, row, pose_context=pose)
            phase, _, threshold = _phase_for_position(pos, len(records), exercise)
            row["phase"] = phase
            row["threshold"] = threshold
            row["phase_threshold"] = threshold
            if _to_bool(row.get("filtered_stranger")):
                _mark_filtered_stranger(row, _clean_text(row.get("stranger_reason")) or ("codman_helper_overlap" if exercise_key == "codman" else "pulley_multiple_people"))
            else:
                row = _apply_youtube_reference_to_frame(row, exercise, overwrite=True)
                status_text = _phase_status_for_frame(row, float(threshold), _default_refs_for_exercise(exercise), exercise)
                row["status"] = status_text
                row["phase_status"] = status_text
                row["dung"] = status_text == "PASS"
                row["gan_dung"] = status_text == "NEAR"
            records[pos] = row
            after = (_to_bool(row.get("filtered_stranger")), _clean_text(row.get("status")).upper())
            if after != before:
                updated += 1
            if pos == 0 or (pos + 1) % 100 == 0 or time.time() - last >= 5:
                print(f"scan {pos + 1}/{len(records)} updated={updated}", flush=True)
                last = time.time()
    cap.release()
    metrics = _analysis_metrics(records, len(records), 0.0, exercise)
    frames_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    write_records_csv(csv_path, records)
    rendered = render_artifacts(source, processed, frames_zip, records, exercise, fps)
    unknown_after = sum(1 for row in records if isinstance(row, dict) and (_to_bool(row.get("filtered_stranger")) or _clean_text(row.get("status")).upper() == "UNKNOWN"))
    videos[idx].update(
        {
            "metrics": metrics,
            "accuracy": metrics.get("do_chinh_xac", videos[idx].get("accuracy")),
            "processed_path": _relative_repo_path(processed),
            "df_path": _relative_repo_path(csv_path),
            "all_frames_data_path": _relative_repo_path(frames_path),
            "frames_zip": _relative_repo_path(frames_zip),
            "frames_zip_path": _relative_repo_path(frames_zip),
        }
    )
    _save_data("video_list", videos)
    CHART_PAYLOAD_CACHE.clear()
    print(
        json.dumps(
            {
                "updated": updated,
                "unknown_before": unknown_before,
                "unknown_after": unknown_after,
                "rendered": rendered,
                "frames": str(frames_path),
                "csv": str(csv_path),
                "video": str(processed),
                "zip": str(frames_zip),
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    _analysis_metrics,
    _apply_youtube_reference_to_frame,
    _clean_text,
    _codman_helper_overlap_detected,
    _default_refs_for_exercise,
    _draw_pose_analysis_overlay,
    _exercise_key,
    _exercise_label,
    _frame_number_key,
    _frame_with_exercise_context,
    _load_data,
    _mark_filtered_stranger,
    _mediapipe_candidate_from_crop,
    _phase_for_position,
    _phase_status_for_frame,
    _recompute_pose_angles_for_frame,
    _relative_repo_path,
    _resolve_existing_path,
    _resolve_video_source_path,
    _save_data,
    _to_bool,
)


def write_csv(path: Path, records: list[dict]) -> None:
    fields = sorted({key for row in records for key in row.keys() if not isinstance(row.get(key), (dict, list))})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fields} for row in records)


def render(source: Path, output: Path, zip_path: Path, records: list[dict], exercise: str, fps: float) -> int:
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        return 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 720
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1280
    if output.is_file():
        old = cv2.VideoCapture(str(output))
        old_w = int(old.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        old_h = int(old.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        old.release()
        if old_w > 0 and old_h > 0:
            width, height = old_w, old_h
    tmp_video = output.with_name(f"{output.stem}_fastrepair_tmp.mp4")
    tmp_zip = zip_path.with_name(f"{zip_path.stem}_fastrepair_tmp.zip")
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
            for pos, row in enumerate(records):
                frame_no = _frame_number_key(row.get("index") or row.get("frame") or row.get("frame_number")) or pos + 1
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_no - 1))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                if (frame.shape[1], frame.shape[0]) != (width, height):
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA if width < frame.shape[1] else cv2.INTER_LINEAR)
                _, _, fallback_threshold = _phase_for_position(pos, len(records), exercise)
                threshold = float(row.get("threshold") or row.get("phase_threshold") or fallback_threshold)
                out = _draw_pose_analysis_overlay(frame, row, int(frame_no), threshold=threshold)
                writer.write(out)
                ok_jpg, encoded = cv2.imencode(".jpg", out, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok_jpg:
                    archive.writestr(f"f_{pos + 1:06d}.jpg", encoded.tobytes())
                done += 1
                if done == 1 or done % 200 == 0 or time.time() - last >= 5:
                    print(f"render {done}/{len(records)}", flush=True)
                    last = time.time()
    finally:
        cap.release()
        writer.release()
    if done:
        tmp_video.replace(output)
        tmp_zip.replace(zip_path)
    return done


def main() -> int:
    needle = " ".join(sys.argv[1:]).lower() or "cao codman"
    videos = _load_data("video_list")
    match = None
    for idx, video in enumerate(videos):
        if not isinstance(video, dict):
            continue
        text = " ".join(str(video.get(k, "")) for k in ("video_name", "username", "full_name", "patient_username", "exercise")).lower()
        if all(part in text for part in needle.split()):
            match = (idx, video)
            break
    if not match:
        print("no match", needle)
        return 2
    idx, video = match
    exercise = _exercise_label(video.get("exercise") or video.get("video_name"))
    exercise_key = _exercise_key(exercise)
    source = _resolve_video_source_path(video.get("video_path")) or _resolve_video_source_path(video.get("processed_path"))
    processed = _resolve_existing_path(video.get("processed_path"))
    frames_path = _resolve_existing_path(video.get("all_frames_data_path"))
    csv_path = _resolve_existing_path(video.get("df_path")) or processed.with_name(f"{processed.stem}_data.csv")
    zip_path = _resolve_existing_path(video.get("frames_zip") or video.get("frames_zip_path")) or processed.with_name(f"{processed.stem}_frames.zip")
    if not source or not processed or not frames_path:
        print("missing artifact", source, processed, frames_path)
        return 3
    records = json.loads(frames_path.read_text(encoding="utf-8"))
    cap = cv2.VideoCapture(str(source))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    unknown_before = sum(1 for row in records if isinstance(row, dict) and (_to_bool(row.get("filtered_stranger")) or str(row.get("status", "")).upper() == "UNKNOWN"))
    print(f"fast repair {video.get('video_name')} frames={len(records)} unknown_before={unknown_before}", flush=True)
    updated = 0
    unknown = 0
    last = time.time()
    with mp.solutions.pose.Pose(static_image_mode=False, model_complexity=0, enable_segmentation=False, min_detection_confidence=0.3, min_tracking_confidence=0.3) as pose:
        for pos, row in enumerate(records):
            if not isinstance(row, dict):
                continue
            frame_no = _frame_number_key(row.get("index") or row.get("frame") or row.get("frame_idx") or row.get("frame_number")) or pos + 1
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_no - 1))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            h, w = frame.shape[:2]
            small_w = 360
            small_h = max(2, int(h * small_w / max(1, w)))
            small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
            row = _frame_with_exercise_context(row, exercise)
            candidate = _mediapipe_candidate_from_crop(pose, small, None)
            probe = {"index": frame_no, "exercise": exercise}
            if candidate:
                probe.update(candidate)
                probe = _recompute_pose_angles_for_frame(probe, small.shape, exercise)
            is_unknown = False
            if exercise_key == "codman":
                is_unknown = bool(candidate and _codman_helper_overlap_detected(small, probe))
            # Pulley still relies on already-marked records for now; HOG is too noisy on resized views.
            before_status = (_to_bool(row.get("filtered_stranger")), _clean_text(row.get("status")).upper())
            phase, _, threshold = _phase_for_position(pos, len(records), exercise)
            row["phase"] = phase
            row["threshold"] = threshold
            row["phase_threshold"] = threshold
            if is_unknown:
                _mark_filtered_stranger(row, "codman_helper_overlap")
                unknown += 1
            else:
                row = _apply_youtube_reference_to_frame(row, exercise, overwrite=True)
                status = _phase_status_for_frame(row, float(threshold), _default_refs_for_exercise(exercise), exercise)
                row["status"] = status
                row["phase_status"] = status
                row["dung"] = status == "PASS"
                row["gan_dung"] = status == "NEAR"
            after_status = (_to_bool(row.get("filtered_stranger")), _clean_text(row.get("status")).upper())
            if after_status != before_status:
                updated += 1
            records[pos] = row
            if pos == 0 or (pos + 1) % 200 == 0 or time.time() - last >= 5:
                print(f"scan {pos + 1}/{len(records)} unknown={unknown} updated={updated}", flush=True)
                last = time.time()
    cap.release()
    metrics = _analysis_metrics(records, len(records), 0.0, exercise)
    frames_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    write_csv(csv_path, records)
    rendered = render(source, processed, zip_path, records, exercise, fps)
    unknown_after = sum(1 for row in records if isinstance(row, dict) and (_to_bool(row.get("filtered_stranger")) or str(row.get("status", "")).upper() == "UNKNOWN"))
    videos[idx].update(
        {
            "metrics": metrics,
            "accuracy": metrics.get("do_chinh_xac", videos[idx].get("accuracy")),
            "processed_path": _relative_repo_path(processed),
            "df_path": _relative_repo_path(csv_path),
            "all_frames_data_path": _relative_repo_path(frames_path),
            "frames_zip": _relative_repo_path(zip_path),
            "frames_zip_path": _relative_repo_path(zip_path),
        }
    )
    _save_data("video_list", videos)
    print(json.dumps({"updated": updated, "unknown_before": unknown_before, "unknown_after": unknown_after, "rendered": rendered}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

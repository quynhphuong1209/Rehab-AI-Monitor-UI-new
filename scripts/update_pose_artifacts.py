from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.main import (  # noqa: E402
    _analysis_metrics,
    _apply_ml_to_records,
    _apply_people_filter_to_record,
    _apply_phase_thresholds_to_records,
    _apply_video_orientation,
    _clean_text,
    _disable_capture_autorotate,
    _ensure_sound_playback_video,
    _exercise_key,
    _force_portrait_pose_frame,
    _frame_number_key,
    _frame_with_detected_pose,
    _frame_without_pose_measurements,
    _load_data,
    _pose_landmarks,
    _redetect_or_keep_oriented_pose_for_preview_frame,
    _recompute_pose_angles_for_frame,
    _relative_repo_path,
    _render_analysis_artifacts_from_records,
    _resolve_existing_path,
    _resolve_readable_video_sibling,
    _resolve_video_source_path,
    _save_data,
    _to_float,
    _video_frame_count,
)


def _records_path(video: dict) -> Path | None:
    for key in ("all_frames_data_path", "frames_json", "results_json"):
        path = _resolve_existing_path(video.get(key))
        if path:
            return path
    processed = _resolve_existing_path(video.get("processed_path"))
    if processed:
        stem = processed.stem
        if stem.endswith("_sound"):
            stem = stem[: -len("_sound")]
        if stem.endswith("_f"):
            stem = stem[: -len("_f")]
        if stem.startswith("processed_"):
            candidate = REPO_ROOT / "processed_results" / f"f_{stem.removeprefix('processed_')}.json"
            if candidate.is_file():
                return candidate
    return None


def _load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rows = data.get("frames") or data.get("data") or []
    else:
        rows = data
    return [row for row in rows if isinstance(row, dict)]


def _write_records_csv(path: Path, records: list[dict]) -> None:
    if not records:
        return
    existing_header: list[str] = []
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                existing_header = next(reader, [])
        except Exception:
            existing_header = []
    keys: list[str] = []
    seen: set[str] = set()
    for key in existing_header:
        if key and key not in seen:
            keys.append(key)
            seen.add(key)
    for record in records:
        for key in record.keys():
            if key not in seen:
                keys.append(key)
                seen.add(key)
    if not keys:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def _write_records_json(path: Path, records: list[dict]) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write("[")
        for idx, record in enumerate(records):
            if idx:
                handle.write(",")
            json.dump(record, handle, ensure_ascii=False)
        handle.write("]")
    tmp_path.replace(path)


def _sideways_pose_needs_repair(record: dict) -> bool:
    if len(_pose_landmarks(record)) < 33:
        return False
    values = {
        key: _to_float(record.get(key))
        for key in (
            "pt11_x",
            "pt11_y",
            "pt12_x",
            "pt12_y",
            "pt23_x",
            "pt23_y",
            "pt24_x",
            "pt24_y",
            "pt27_y",
            "pt28_y",
        )
    }
    if any(value is None for value in values.values()):
        return False
    shoulder_dx = abs(values["pt11_x"] - values["pt12_x"])
    shoulder_dy = abs(values["pt11_y"] - values["pt12_y"])
    hip_dx = abs(values["pt23_x"] - values["pt24_x"])
    hip_dy = abs(values["pt23_y"] - values["pt24_y"])
    torso = ((values["pt23_y"] + values["pt24_y"]) / 2) - ((values["pt11_y"] + values["pt12_y"]) / 2)
    leg = ((values["pt27_y"] + values["pt28_y"]) / 2) - ((values["pt23_y"] + values["pt24_y"]) / 2)
    return (
        shoulder_dx < 0.035
        and shoulder_dy > 0.10
        and hip_dx < 0.025
        and hip_dy > 0.07
        and abs(torso) < 0.06
        and leg < 0.08
    )


def _repair_sideways_pose_record(record: dict, image_shape: tuple[int, int, int], exercise: str) -> dict:
    output = dict(record)
    orientation = _clean_text(output.get("auto_orientation")).lower()
    counterclockwise = "counterclockwise" in orientation
    for idx in range(33):
        x = _to_float(output.get(f"pt{idx}_x"))
        y = _to_float(output.get(f"pt{idx}_y"))
        if x is None or y is None:
            continue
        if counterclockwise:
            next_x = 1.0 - y
            next_y = x
        else:
            next_x = y
            next_y = 1.0 - x
        output[f"pt{idx}_x"] = max(0.0, min(1.0, next_x))
        output[f"pt{idx}_y"] = max(0.0, min(1.0, next_y))
    output["pose_repaired_sideways"] = True
    output["pose_sideways_repair"] = "counterclockwise_inverse" if counterclockwise else "clockwise_inverse"
    output = _recompute_pose_angles_for_frame(output, image_shape, exercise)
    return output


def _repair_sideways_records(records: list[dict], source: Path | None, exercise: str) -> int:
    try:
        import cv2  # type: ignore[import-not-found]

        cap = cv2.VideoCapture(str(source)) if source else None
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) if cap and cap.isOpened() else 0
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) if cap and cap.isOpened() else 0
        if cap:
            cap.release()
    except Exception:
        width = height = 0
    if width <= 0 or height <= 0:
        width = height = 1000
    image_shape = (height, width, 3)
    changed = 0
    for pos, record in enumerate(records):
        if not isinstance(record, dict) or not _sideways_pose_needs_repair(record):
            continue
        records[pos] = _repair_sideways_pose_record(record, image_shape, exercise)
        changed += 1
    return changed


def _video_source(video: dict) -> Path | None:
    for key in ("video_path", "raw_video_path", "processed_path", "audio_video_path"):
        path = _resolve_video_source_path(video.get(key))
        path = _resolve_readable_video_sibling(path)
        if path and path.is_file() and _video_frame_count(path) > 0:
            return path
    return None


def _processed_paths(video: dict, records_path: Path) -> tuple[Path, Path, Path]:
    processed = _resolve_existing_path(video.get("processed_path"))
    if processed and processed.suffix.lower() == ".mp4":
        stem = processed.stem
        if stem.endswith("_sound"):
            stem = stem[: -len("_sound")]
        if stem.endswith("_f"):
            stem = stem[: -len("_f")]
    else:
        stem = f"processed_{records_path.stem.removeprefix('f_')}"
    output = REPO_ROOT / "processed_results" / f"{stem}_f.mp4"
    frames_zip = _resolve_existing_path(video.get("frames_zip") or video.get("frames_zip_path")) or REPO_ROOT / "processed_results" / f"{stem}_frames.zip"
    csv_path = _resolve_existing_path(video.get("df_path")) or REPO_ROOT / "processed_results" / f"{stem}_data.csv"
    return output, frames_zip, csv_path


def _ffmpeg_probe(path: Path) -> tuple[float, int, int, int]:
    try:
        import cv2  # type: ignore[import-not-found]
    except Exception:
        return 30.0, 720, 1280, 0
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 720
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1280
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return fps, width, height, total


def update_video(
    idx: int,
    video: dict,
    *,
    render: bool,
    limit: int | None = None,
    force_redetect: bool = False,
    repair_sideways: bool = False,
) -> dict:
    exercise = video.get("exercise") or video.get("video_name")
    exercise_key = _exercise_key(exercise)
    if exercise_key not in {"codman", "pulley"}:
        return {"idx": idx, "skipped": "exercise"}
    records_path = _records_path(video)
    source = _video_source(video)
    if not records_path or not records_path.is_file() or not source:
        return {"idx": idx, "skipped": "missing_artifact_or_video"}

    records = _load_records(records_path)
    fps, width, height, total_frames = _ffmpeg_probe(source)
    output_video, frames_zip, csv_path = _processed_paths(video, records_path)
    changed = 0
    unknown_before = sum(1 for row in records if row.get("filtered_stranger") or _clean_text(row.get("status")).upper() == "UNKNOWN")

    if repair_sideways:
        changed = _repair_sideways_records(records, source, exercise)
        phase_bounds = _apply_phase_thresholds_to_records(records, exercise)
        metrics = _analysis_metrics(records, total_frames or len(records), 0.0, exercise)
        _write_records_json(records_path, records)
        if csv_path.is_file():
            _write_records_csv(csv_path, records)
            try:
                metrics = _apply_ml_to_records(csv_path, records_path, records, metrics, exercise)
            except Exception as exc:
                metrics["ml_status"] = f"skip ML refresh: {exc}"
            _write_records_csv(csv_path, records)
        unknown_after = sum(1 for row in records if row.get("filtered_stranger") or _clean_text(row.get("status")).upper() == "UNKNOWN")
        video["all_frames_data_path"] = _relative_repo_path(records_path)
        video["metrics"] = metrics
        video["accuracy"] = metrics.get("do_chinh_xac")
        video["status"] = "Đã phân tích"
        video["artifact_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "idx": idx,
            "video": video.get("video_name"),
            "frames": len(records),
            "changed": changed,
            "unknown_before": unknown_before,
            "unknown_after": unknown_after,
            "rendered": 0,
            "metrics": {k: metrics.get(k) for k in ("frame_dung", "frame_gan_dung", "frame_sai", "frame_khong_nhan_dang", "tong_frame_hop_le")},
        }

    try:
        import cv2  # type: ignore[import-not-found]
        import mediapipe as mp  # type: ignore[import-not-found]
    except Exception as exc:
        return {"idx": idx, "error": f"missing cv2/mediapipe: {exc}"}

    frame_targets = [
        int(_frame_number_key(row.get("frame") or row.get("index") or row.get("frame_number")) or pos + 1)
        for pos, row in enumerate(records)
    ]
    target_to_positions: dict[int, list[int]] = {}
    for pos, frame_no in enumerate(frame_targets):
        target_to_positions.setdefault(max(1, int(frame_no)), []).append(pos)
    cap = cv2.VideoCapture(str(source))
    _disable_capture_autorotate(cap)
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.35,
    )
    try:
        frame_no = 0
        processed_positions = 0
        max_target = max(target_to_positions) if target_to_positions else 0
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            frame_no += 1
            positions = target_to_positions.get(frame_no)
            if not positions:
                if max_target and frame_no > max_target:
                    break
                continue
            frame = _apply_video_orientation(frame, source)
            frame_h, frame_w = frame.shape[:2]
            if frame_w > 720:
                next_w = 720
                next_h = max(2, int(round(frame_h * next_w / max(1, frame_w))))
                next_h -= next_h % 2
                frame = cv2.resize(frame, (next_w, max(2, next_h)), interpolation=cv2.INTER_AREA)
            for pos in positions:
                if limit is not None and processed_positions >= limit:
                    break
                row = records[pos]
                row = {
                    **row,
                    "exercise": row.get("exercise") or exercise,
                    "exercise_key": row.get("exercise_key") or exercise_key,
                }
                source_row = _frame_without_pose_measurements(row) if force_redetect else row
                oriented_frame, oriented_row = _force_portrait_pose_frame(frame, source_row, exercise)
                before = json.dumps(
                    {
                        "status": row.get("status"),
                        "filtered": row.get("filtered_stranger"),
                        "points": len(_pose_landmarks(row)),
                        "reason": row.get("stranger_reason"),
                        "left_shoulder": row.get("goc_vai_trai") or row.get("left_shoulder_angle"),
                        "left_elbow": row.get("goc_khuyu_trai") or row.get("left_elbow_angle"),
                        "right_shoulder": row.get("goc_vai_phai") or row.get("right_shoulder_angle"),
                        "right_elbow": row.get("goc_khuyu_phai") or row.get("right_elbow_angle"),
                    },
                    sort_keys=True,
                )
                if force_redetect or len(_pose_landmarks(oriented_row)) < 33 or _clean_text(oriented_row.get("status")).upper() == "UNKNOWN":
                    oriented_row = _redetect_or_keep_oriented_pose_for_preview_frame(
                        oriented_frame,
                        oriented_row,
                        exercise,
                        pose_context=pose,
                    )
                elif exercise_key in {"codman", "pulley"}:
                    oriented_row = _recompute_pose_angles_for_frame(oriented_row, oriented_frame.shape, exercise)
                oriented_row = _apply_people_filter_to_record(oriented_frame, oriented_row, exercise)
                oriented_frame, row = _force_portrait_pose_frame(oriented_frame, oriented_row, exercise)
                row = _recompute_pose_angles_for_frame(row, oriented_frame.shape, exercise)
                records[pos] = row
                after = json.dumps(
                    {
                        "status": row.get("status"),
                        "filtered": row.get("filtered_stranger"),
                        "points": len(_pose_landmarks(row)),
                        "reason": row.get("stranger_reason"),
                        "left_shoulder": row.get("goc_vai_trai") or row.get("left_shoulder_angle"),
                        "left_elbow": row.get("goc_khuyu_trai") or row.get("left_elbow_angle"),
                        "right_shoulder": row.get("goc_vai_phai") or row.get("right_shoulder_angle"),
                        "right_elbow": row.get("goc_khuyu_phai") or row.get("right_elbow_angle"),
                    },
                    sort_keys=True,
                )
                if before != after:
                    changed += 1
                processed_positions += 1
            if limit is not None and processed_positions >= limit:
                break
            if processed_positions and processed_positions % 250 == 0:
                print(f"[{idx}] {video.get('video_name')} scanned {processed_positions}/{len(records)} changed={changed}", flush=True)
    finally:
        cap.release()
        pose.close()

    phase_bounds = _apply_phase_thresholds_to_records(records, exercise)
    metrics = _analysis_metrics(records, total_frames or len(records), 0.0, exercise)
    _write_records_json(records_path, records)

    if csv_path.is_file():
        _write_records_csv(csv_path, records)
        try:
            metrics = _apply_ml_to_records(csv_path, records_path, records, metrics, exercise)
        except Exception as exc:
            metrics["ml_status"] = f"skip ML refresh: {exc}"
        _write_records_csv(csv_path, records)

    rendered = 0
    if render:
        target_width = min(width, 720)
        target_width = max(2, target_width - (target_width % 2))
        target_height = max(2, int(round(height * target_width / max(1, width))))
        target_height -= target_height % 2
        rendered = _render_analysis_artifacts_from_records(
            source,
            output_video,
            frames_zip,
            records,
            fps=fps,
            skip=max(1, round(total_frames / max(1, len(records)))) if total_frames and len(records) < total_frames else 1,
            target_width=target_width,
            target_height=target_height,
            exercise=exercise,
            on_progress=lambda done, total: print(f"[{idx}] render {done}/{total}", flush=True),
        )
        if rendered:
            sound_path, sound_updates = _ensure_sound_playback_video(output_video, records, exercise=exercise, metrics=metrics)
            if sound_path:
                video["processed_path"] = _relative_repo_path(sound_path)
                if sound_updates.get("audio_video_path"):
                    video["audio_video_path"] = sound_updates["audio_video_path"]
            else:
                video["processed_path"] = _relative_repo_path(output_video)
            video["frames_zip"] = _relative_repo_path(frames_zip)
            video["frames_zip_path"] = _relative_repo_path(frames_zip)

    unknown_after = sum(1 for row in records if row.get("filtered_stranger") or _clean_text(row.get("status")).upper() == "UNKNOWN")
    video["all_frames_data_path"] = _relative_repo_path(records_path)
    video["metrics"] = metrics
    video["accuracy"] = metrics.get("do_chinh_xac")
    video["status"] = "Đã phân tích"
    video["artifact_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "idx": idx,
        "video": video.get("video_name"),
        "frames": len(records),
        "changed": changed,
        "unknown_before": unknown_before,
        "unknown_after": unknown_after,
        "rendered": rendered,
        "metrics": {k: metrics.get(k) for k in ("frame_dung", "frame_gan_dung", "frame_sai", "frame_khong_nhan_dang", "tong_frame_hop_le")},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indices", nargs="*", type=int)
    parser.add_argument("--contains", default="")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force-redetect", action="store_true")
    parser.add_argument("--repair-sideways", action="store_true")
    args = parser.parse_args()

    videos = _load_data("video_list")
    selected: list[int] = args.indices or []
    if args.contains:
        needle = args.contains.casefold()
        selected.extend(i for i, video in enumerate(videos) if needle in str(video.get("video_name") or "").casefold())
    if not selected:
        selected = [i for i, video in enumerate(videos) if _exercise_key(video.get("exercise") or video.get("video_name")) in {"codman", "pulley"}]
    selected = sorted(set(i for i in selected if 0 <= i < len(videos)))

    results = []
    for idx in selected:
        result = update_video(
            idx,
            videos[idx],
            render=args.render,
            limit=args.limit,
            force_redetect=args.force_redetect,
            repair_sideways=args.repair_sideways,
        )
        print(json.dumps(result, ensure_ascii=False), flush=True)
        results.append(result)
    _save_data("video_list", videos)
    print(json.dumps({"updated_videos": len(selected), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

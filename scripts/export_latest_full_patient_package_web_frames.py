"""Build a read-only export package with web-rendered frames.

This exporter intentionally writes only under processed_results/full_patient_exports.
It does not update database JSON, dataset artifacts, frame ZIPs, or video records.
By default, frame images are extracted from the current video source that the web
uses, so this does not reuse older frame ZIP artifacts. An optional overlay mode
can render the exact web preview overlay, but it is much slower.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from export_latest_full_patient_package import (  # noqa: E402
    BUNDLE_PATH,
    EVALUATIONS_PATH,
    EXPORT_ROOT,
    RESEARCH_PATH,
    SYMPTOMS_PATH,
    VIDEO_LIST_PATH,
    copy_common_binary_assets,
    copy_frame_subset,
    find_chart_dir,
    frame_counts,
    is_codman,
    is_stick_or_pulley,
    latest_chart_export_dir,
    link_or_copy,
    matching_rows,
    path_token,
    read_csv_rows,
    read_json,
    rel,
    repo_path,
    resolve_frames_zip,
    safe_name,
    source_path,
    source_raw_video,
    write_common_records,
    write_csv_rows,
    write_json,
)
from replace_export_charts_from_dataset import replace_export_charts  # noqa: E402

import backend.main as backend  # noqa: E402


def flatten_bundle_video(video: dict[str, Any]) -> dict[str, Any]:
    flat = dict(video)
    paths = video.get("paths") if isinstance(video.get("paths"), dict) else {}
    for key, snapshot in paths.items():
        if isinstance(snapshot, dict):
            value = snapshot.get("resolved_path") or snapshot.get("path")
        else:
            value = snapshot
        if value and not flat.get(key):
            flat[key] = value
    return flat


def frame_records_for_web(video: dict[str, Any], frame_path: Path | None, df_path: Path | None) -> list[dict[str, Any]]:
    frame_records = backend._read_frame_records(frame_path)
    sample_records = frame_records[: min(24, len(frame_records))]
    frame_records_have_pose = bool(sample_records) and any(backend._has_complete_pose(frame) for frame in sample_records)
    frame_records_have_ml = bool(sample_records) and any(backend._frame_ml_label(frame) for frame in sample_records)
    prefer_csv = backend._prefer_csv_frame_records(frame_path, df_path)
    csv_records = (
        backend._frame_records_from_csv(df_path)
        if df_path and (prefer_csv or not frame_records or not (frame_records_have_pose and frame_records_have_ml))
        else []
    )
    if frame_records and csv_records:
        return backend._merge_frame_records_with_csv_pose(frame_records, csv_records, prefer_csv=prefer_csv)
    if csv_records:
        return csv_records
    return frame_records


def unique_paths(paths: list[Path | None]) -> list[Path]:
    output: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if not path or not path.is_file():
            continue
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        if resolved in seen:
            continue
        seen.add(resolved)
        output.append(resolved)
    return output


def web_frame_video_paths(video: dict[str, Any], frame_records: list[dict[str, Any]]) -> tuple[list[Path], dict[str, Any]]:
    flat = flatten_bundle_video(video)
    audio_video_path = source_path(flat, "audio_video_path")
    processed_video_path = source_path(flat, "processed_path")
    raw_video_path = source_path(flat, "video_path") or source_raw_video(flat)
    use_original_pulley = backend._is_cao_thi_thuong_pulley_video(flat)
    if use_original_pulley:
        raw_video_path = backend._resolve_readable_video_sibling(raw_video_path)
    pose_playback_path = backend._pose_playback_video_path(processed_video_path)
    if use_original_pulley:
        preferred_video = audio_video_path or processed_video_path or pose_playback_path or raw_video_path
    else:
        preferred_video = audio_video_path or (
            processed_video_path
            if backend._audio_codec(processed_video_path)
            else (pose_playback_path or processed_video_path or raw_video_path)
        )
    playback_video_path, playback_status = backend._resolve_playback_video_path(preferred_video, raw_video_path)
    frame_playback_path = playback_video_path if playback_status != "rebuilt_from_frames" else None
    prefer_video_pose_frames = backend._needs_video_pose_frame_preference(flat)
    pose_exercise = backend._frame_exercise_key(flat, flat.get("exercise")) in {"codman", "pulley"}
    raw_pose_candidates = backend._raw_upload_candidates_for_video(flat) if pose_exercise else []
    if use_original_pulley:
        candidates = [processed_video_path, frame_playback_path, raw_video_path]
    elif prefer_video_pose_frames:
        if pose_exercise:
            candidates = [*raw_pose_candidates, raw_video_path, frame_playback_path, processed_video_path]
        else:
            candidates = [frame_playback_path, processed_video_path, raw_video_path]
    else:
        candidates = [frame_playback_path, processed_video_path, raw_video_path]
    if prefer_video_pose_frames and frame_records and any(backend._frame_ml_label(frame) for frame in frame_records[: min(20, len(frame_records))]):
        if pose_exercise:
            candidates = [*raw_pose_candidates, raw_video_path, frame_playback_path, processed_video_path]
        else:
            candidates = [frame_playback_path, processed_video_path, raw_video_path]
    readable = [path for path in unique_paths(candidates) if backend._video_frame_count(path) > 0]
    readable = sorted(readable, key=backend._pose_video_context_priority)
    return readable, {
        "raw_video": rel(raw_video_path) if raw_video_path else None,
        "processed_video": rel(processed_video_path) if processed_video_path else None,
        "pose_playback_video": rel(pose_playback_path) if pose_playback_path else None,
        "playback_video": rel(playback_video_path) if playback_video_path else None,
        "playback_status": playback_status,
        "prefer_video_pose_frames": prefer_video_pose_frames,
        "source_candidates": [rel(path) for path in readable],
    }


def frame_number(record: dict[str, Any], fallback: int) -> int:
    key = backend._frame_number_key(
        record.get("index") or record.get("frame") or record.get("frame_idx") or record.get("frame_number")
    )
    return key if key is not None else fallback


def render_web_frame_bytes(
    record: dict[str, Any],
    video: dict[str, Any],
    image: Any,
    source_has_legacy_overlay: bool,
    display_index: int,
    pose_context: Any = None,
) -> bytes | None:
    import cv2  # type: ignore[import-not-found]

    if image is None:
        return None

    frame_data = backend._frame_with_exercise_context(dict(record), record.get("exercise") or record.get("exercise_key") or video.get("exercise"))
    exercise_key = backend._frame_exercise_key(frame_data)
    image, frame_data = backend._force_portrait_pose_frame(image, frame_data, frame_data.get("exercise") or frame_data.get("exercise_key"))
    if source_has_legacy_overlay or backend._frame_has_analysis_overlay(image):
        image = backend._remove_legacy_analysis_overlay(image)
    if exercise_key in {"codman", "pulley"}:
        frame_data = backend._redetect_or_keep_oriented_pose_for_preview_frame(
            image,
            frame_data,
            exercise_key,
            pose_context=pose_context,
            allow_oriented_metadata_fallback=source_has_legacy_overlay,
        )
    elif not backend._has_complete_pose(frame_data):
        frame_data = backend._frame_with_detected_pose(image, frame_data, pose_context=pose_context)
    image, frame_data = backend._force_portrait_pose_frame(
        image,
        frame_data,
        exercise_key or frame_data.get("exercise") or frame_data.get("exercise_key"),
    )
    if exercise_key in {"codman", "pulley"}:
        frame_data = backend._apply_youtube_reference_to_frame(
            frame_data,
            frame_data.get("exercise") or frame_data.get("exercise_key"),
            overwrite=frame_data.get("ref_source") != "youtube_mediapipe",
        )
    threshold = backend._to_float(frame_data.get("threshold") or frame_data.get("phase_threshold")) or 30.0
    rendered = backend._draw_pose_analysis_overlay(image, frame_data, display_index, threshold=threshold)
    ok, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    return encoded.tobytes() if ok else None


def render_web_frame_image(record: dict[str, Any], video: dict[str, Any], source_paths: list[Path], source_index: int, display_index: int) -> bytes | None:
    import cv2  # type: ignore[import-not-found]

    image = None
    source_has_legacy_overlay = False
    for candidate in source_paths:
        cap = cv2.VideoCapture(str(candidate))
        backend._disable_capture_autorotate(cap)
        cap.set(cv2.CAP_PROP_POS_FRAMES, source_index)
        ok, frame = cap.read()
        cap.release()
        if ok and frame is not None:
            image = backend._apply_video_orientation(frame, candidate)
            source_has_legacy_overlay = backend._frame_has_analysis_overlay(image)
            break
    return render_web_frame_bytes(record, video, image, source_has_legacy_overlay, display_index)


def render_frames_for_video(
    video: dict[str, Any],
    frame_records: list[dict[str, Any]],
    source_paths: list[Path],
    output_dir: Path,
    *,
    label: str,
    progress_every: int = 250,
) -> dict[str, Any]:
    import cv2  # type: ignore[import-not-found]

    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = 0
    skipped = 0
    missing = 0
    total = len(frame_records)
    source_counts = [(path, backend._video_frame_count(path)) for path in source_paths if path and path.is_file()]
    source_counts = sorted(source_counts, key=lambda item: (item[1] >= total, item[1]), reverse=True)
    max_source_count = max((count for _, count in source_counts), default=0)
    if not source_counts or max_source_count <= 0:
        return {"rendered": 0, "skipped_existing": 0, "missing": total, "total": total, "error": "no readable source video"}

    captures: dict[Path, dict[str, Any]] = {}
    pose_context = None
    exercise_key = backend._frame_exercise_key(video, video.get("exercise"))
    needs_pose_redetect = exercise_key in {"codman", "pulley"} or any(
        isinstance(record, dict) and len(backend._pose_landmarks(record)) < 33
        for record in frame_records[: min(50, len(frame_records))]
    )
    try:
        if needs_pose_redetect:
            try:
                import mediapipe as mp  # type: ignore[import-not-found]

                pose_context = mp.solutions.pose.Pose(
                    static_image_mode=exercise_key == "codman",
                    model_complexity=2,
                    enable_segmentation=False,
                    min_detection_confidence=0.35,
                )
            except Exception:
                pose_context = None

        for path, count in source_counts:
            cap = cv2.VideoCapture(str(path))
            backend._disable_capture_autorotate(cap)
            captures[path] = {"cap": cap, "count": count, "current": -1}

        for position, record in enumerate(frame_records, start=1):
            target = output_dir / f"frame_{position:06d}.jpg"
            if target.is_file() and target.stat().st_size > 32:
                skipped += 1
                continue
            if not isinstance(record, dict):
                record = {"index": position}
            number = frame_number(record, position)
            source_index = min(max(0, number - 1), max(0, max_source_count - 1))
            image = None
            source_has_legacy_overlay = False
            for path, _count in source_counts:
                info = captures.get(path)
                if not info:
                    continue
                cap = info["cap"]
                if source_index != int(info.get("current", -1)) + 1:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, source_index)
                ok, frame = cap.read()
                info["current"] = source_index
                if ok and frame is not None:
                    image = backend._apply_video_orientation(frame, path)
                    source_has_legacy_overlay = backend._frame_has_analysis_overlay(image)
                    break
            content = render_web_frame_bytes(record, video, image, source_has_legacy_overlay, number, pose_context=pose_context)
            if content:
                target.write_bytes(content)
                rendered += 1
            else:
                missing += 1
            done = rendered + skipped + missing
            if progress_every > 0 and done % progress_every == 0:
                print(f"  {label}: {done}/{total} frames")
    finally:
        for info in captures.values():
            try:
                info["cap"].release()
            except Exception:
                pass
        if pose_context is not None:
            try:
                pose_context.close()
            except Exception:
                pass
    return {"rendered": rendered, "skipped_existing": skipped, "missing": missing, "total": total}


def extract_video_frames_for_video(
    frame_records: list[dict[str, Any]],
    source_paths: list[Path],
    output_dir: Path,
    *,
    label: str,
    progress_every: int = 500,
) -> dict[str, Any]:
    import cv2  # type: ignore[import-not-found]

    output_dir.mkdir(parents=True, exist_ok=True)
    readable = [path for path in source_paths if backend._video_frame_count(path) > 0]
    if not readable:
        return {"written": 0, "skipped_existing": 0, "missing": len(frame_records), "total": len(frame_records), "error": "no readable source video"}

    source_counts = [(path, backend._video_frame_count(path)) for path in readable]
    source, source_count = max(
        source_counts,
        key=lambda item: (item[1] >= len(frame_records), item[1]),
    )
    cap = cv2.VideoCapture(str(source))
    backend._disable_capture_autorotate(cap)
    written = 0
    skipped = 0
    missing = 0
    current_index = -1
    total = len(frame_records)
    try:
        for position, record in enumerate(frame_records, start=1):
            target = output_dir / f"frame_{position:06d}.jpg"
            if target.is_file() and target.stat().st_size > 32:
                skipped += 1
                continue
            if not isinstance(record, dict):
                record = {"index": position}
            number = frame_number(record, position)
            source_index = min(max(0, number - 1), max(0, source_count - 1))
            if source_index != current_index + 1:
                cap.set(cv2.CAP_PROP_POS_FRAMES, source_index)
            ok, frame = cap.read()
            current_index = source_index
            if not ok or frame is None:
                missing += 1
            else:
                frame = backend._apply_video_orientation(frame, source)
                ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                if ok:
                    target.write_bytes(encoded.tobytes())
                    written += 1
                else:
                    missing += 1
            done = written + skipped + missing
            if progress_every > 0 and done % progress_every == 0:
                print(f"  {label}: {done}/{total} frames")
    finally:
        cap.release()
    return {
        "source_video": rel(source),
        "written": written,
        "skipped_existing": skipped,
        "missing": missing,
        "total": total,
    }


def existing_rendered_frames(output_dir: Path, expected: int) -> list[Path]:
    frames = [output_dir / f"frame_{idx:06d}.jpg" for idx in range(1, expected + 1)]
    return [path for path in frames if path.is_file() and path.stat().st_size > 32]


def build_export(*, output_name: str | None = None, progress_every: int = 500, frame_mode: str = "video") -> Path:
    bundle = read_json(BUNDLE_PATH, {})
    videos = bundle.get("videos") if isinstance(bundle, dict) else []
    if not isinstance(videos, list):
        videos = []
    evaluations_all = read_json(EVALUATIONS_PATH, [])
    symptoms_all = read_json(SYMPTOMS_PATH, [])
    research_all = read_json(RESEARCH_PATH, [])
    chart_root = latest_chart_export_dir()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "full_web_rendered_overlay_frames" if frame_mode == "overlay" else "full_web_current_video_frames"
    export_dir = EXPORT_ROOT / (output_name or f"{prefix}_{stamp}")
    export_dir.mkdir(parents=True, exist_ok=True)

    write_json(export_dir / "database_snapshots" / "latest_video_bundle.json", bundle)
    write_json(export_dir / "database_snapshots" / "video_list.json", read_json(VIDEO_LIST_PATH, []))
    write_json(export_dir / "database_snapshots" / "doctor_evaluations.json", evaluations_all)
    write_json(export_dir / "database_snapshots" / "patient_symptoms.json", symptoms_all)
    write_json(export_dir / "database_snapshots" / "research_data.json", research_all)

    manifest: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_bundle": rel(BUNDLE_PATH),
        "bundle_updated_at": bundle.get("updated_at") if isinstance(bundle, dict) else "",
        "chart_export_source": rel(chart_root) if chart_root else None,
        "note": "Read-only export. Frames are taken from current web video sources and current JSON/CSV metadata; source web/runtime data was not modified.",
        "frame_mode": frame_mode,
        "patients": {},
        "videos": [],
        "totals": {
            "patients": 0,
            "videos": 0,
            "frames_all": 0,
            "render_missing": 0,
            "codman_phase_frames": 0,
            "metric_total_frames": 0,
            "mismatches": 0,
        },
    }

    for index, video in enumerate(videos[:8], start=1):
        if not isinstance(video, dict):
            continue
        flat_video = flatten_bundle_video(video)
        patient = safe_name(flat_video.get("full_name") or flat_video.get("patient_username") or f"patient-{index}")
        patient_folder = f"BN{len(manifest['patients']) + 1:02d}_{path_token(patient, 'patient', 28)}"
        if patient in manifest["patients"]:
            existing_dir = manifest["patients"][patient][0].get("patient_dir")
            patient_folder = Path(str(existing_dir)).name if existing_dir else patient_folder
        exercise_folder = "codman" if is_codman(flat_video) else "gay" if is_stick_or_pulley(flat_video) else "khac"
        video_stem = safe_name(Path(str(flat_video.get("video_name") or f"video-{index}.mp4")).stem)
        video_folder = f"{index:02d}_{path_token(video_stem, 'video', 42)}"
        video_dir = export_dir / patient_folder / exercise_folder / video_folder

        patient_evals = matching_rows(evaluations_all, patient)
        video_evals = matching_rows(evaluations_all, patient, str(flat_video.get("video_name") or ""))
        patient_symptoms = matching_rows(symptoms_all, patient)
        patient_research = matching_rows(research_all, patient)
        video_research = matching_rows(research_all, patient, str(flat_video.get("video_name") or "")) or patient_research

        write_json(export_dir / patient_folder / "patient_info.json", {"patient": patient, "folder": patient_folder})
        write_json(export_dir / patient_folder / "danh_gia_phcn_bac_si_ktv_tat_ca.json", patient_evals)
        write_json(export_dir / patient_folder / "phieu_nckh_benh_nhan_tat_ca.json", patient_research)
        write_json(export_dir / patient_folder / "trieu_chung_benh_nhan_tat_ca.json", patient_symptoms)

        raw_video = source_raw_video(flat_video)
        processed_video = source_path(flat_video, "processed_path")
        csv_path = source_path(flat_video, "df_path")
        frames_json_path = source_path(flat_video, "all_frames_data_path")
        frames_zip = resolve_frames_zip(flat_video)
        chart_dir = find_chart_dir(chart_root, index, patient, str(flat_video.get("video_name") or ""))
        metrics = flat_video.get("metrics") if isinstance(flat_video.get("metrics"), dict) else {}
        frame_records = frame_records_for_web(flat_video, frames_json_path, csv_path)
        source_videos, source_report = web_frame_video_paths(flat_video, frame_records)

        write_common_records(video_dir, flat_video, video_evals or patient_evals, patient_symptoms, video_research, metrics)
        copy_common_binary_assets(video_dir, raw_video, processed_video, frames_zip, chart_dir)
        link_or_copy(csv_path, video_dir / "du_lieu_csv" / "frame_data_all.csv")
        link_or_copy(frames_json_path, video_dir / "du_lieu_json" / "frame_data_all.json")

        csv_fields, csv_rows = read_csv_rows(csv_path)
        frame_json = read_json(frames_json_path, []) if frames_json_path else []
        frame_json_rows = frame_json if isinstance(frame_json, list) else []
        counts = frame_counts(flat_video)
        metric_total = counts["total_metric"] or len(frame_records)
        action = "Rendering overlay frames" if frame_mode == "overlay" else "Extracting current video frames"
        print(f"[{index}/8] {action}: {patient} - {flat_video.get('video_name')} ({len(frame_records)} frames)")
        if frame_mode == "overlay":
            render_report = render_frames_for_video(
                flat_video,
                frame_records,
                source_videos,
                video_dir / "frames_all",
                label=f"{index}/8",
                progress_every=progress_every,
            )
        else:
            render_report = extract_video_frames_for_video(
                frame_records,
                source_videos,
                video_dir / "frames_all",
                label=f"{index}/8",
                progress_every=progress_every,
            )
        frame_paths = existing_rendered_frames(video_dir / "frames_all", len(frame_records))
        all_count = len(frame_paths)

        video_manifest: dict[str, Any] = {
            "patient": patient,
            "patient_dir": rel(export_dir / patient_folder),
            "exercise_folder": exercise_folder,
            "video_name": flat_video.get("video_name"),
            "video_dir": rel(video_dir),
            "frames_all_count": all_count,
            "metric_total_frames": metric_total,
            "matches_metric_total": all_count == metric_total,
            "render_report": render_report,
            "web_frame_source": source_report,
            "codman_phase_counts": {},
            "copied_sources": {
                "raw_video": rel(raw_video) if raw_video else None,
                "processed_video": rel(processed_video) if processed_video else None,
                "csv": rel(csv_path) if csv_path else None,
                "frames_json": rel(frames_json_path) if frames_json_path else None,
                "frames_zip_original_artifact_read_only": rel(frames_zip) if frames_zip else None,
                "charts": rel(chart_dir) if chart_dir else None,
            },
        }
        manifest["totals"]["frames_all"] += all_count
        manifest["totals"]["render_missing"] += int(render_report.get("missing") or 0)
        manifest["totals"]["metric_total_frames"] += metric_total
        if all_count != metric_total:
            manifest["totals"]["mismatches"] += 1

        if is_codman(flat_video):
            for phase_name, phase_key, metrics_key in [
                ("giai_doan_1", "g1", "metrics_g1"),
                ("giai_doan_2", "g2", "metrics_g2"),
                ("giai_doan_3", "g3", "metrics_g3"),
            ]:
                start, end = backend._phase_bounds_for_export(flat_video, frame_records, all_count, phase_key)
                phase_dir = video_dir / phase_name
                phase_metrics = metrics.get(metrics_key) if isinstance(metrics.get(metrics_key), dict) else {}
                write_common_records(phase_dir, flat_video, video_evals or patient_evals, patient_symptoms, video_research, phase_metrics)
                copy_common_binary_assets(phase_dir, raw_video, processed_video, frames_zip, chart_dir)
                copied_frames = copy_frame_subset(frame_paths, start, end, phase_dir / "frames")
                write_json(phase_dir / "du_lieu_json" / f"frame_data_{phase_name}.json", frame_json_rows[start:end])
                write_csv_rows(phase_dir / "du_lieu_csv" / f"frame_data_{phase_name}.csv", csv_fields, csv_rows[start:end])
                write_json(
                    phase_dir / "du_lieu_json" / "phase_info.json",
                    {
                        "phase": phase_name,
                        "phase_key": phase_key,
                        "start_index_zero_based": start,
                        "end_index_exclusive": end,
                        "frame_count": copied_frames,
                        "metrics_key": metrics_key,
                        "split_source": "backend._phase_bounds_for_export / web phase logic",
                    },
                )
                video_manifest["codman_phase_counts"][phase_name] = copied_frames
                manifest["totals"]["codman_phase_frames"] += copied_frames

        manifest["videos"].append(video_manifest)
        manifest["patients"].setdefault(patient, []).append(video_manifest)
        write_json(export_dir / "manifest.partial.json", manifest)

    manifest["totals"]["patients"] = len(manifest["patients"])
    manifest["totals"]["videos"] = len(manifest["videos"])
    write_json(export_dir / "manifest.json", manifest)
    try:
        chart_result = replace_export_charts(export_dir)
        write_json(export_dir / "dataset_chart_replacement_totals.json", chart_result.get("totals", {}))
    except Exception as exc:
        write_json(export_dir / "dataset_chart_replacement_error.json", {"error": str(exc)})
    return export_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Export latest patient package with web-rendered frames.")
    parser.add_argument("--output-name", default=None, help="Optional folder name under processed_results/full_patient_exports.")
    parser.add_argument("--progress-every", type=int, default=500, help="Progress print interval in frames.")
    parser.add_argument(
        "--frame-mode",
        choices=["video", "overlay"],
        default="video",
        help="video extracts current source frames quickly; overlay renders exact web preview overlay slowly.",
    )
    args = parser.parse_args()
    output = build_export(output_name=args.output_name, progress_every=args.progress_every, frame_mode=args.frame_mode)
    print(output)


if __name__ == "__main__":
    main()

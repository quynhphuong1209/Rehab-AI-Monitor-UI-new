from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import main  # noqa: E402
from storage.json_store import read_json, write_json  # noqa: E402


def _records_for_video(video: dict[str, object]) -> tuple[list[dict[str, object]], Path | None]:
    frame_path = main._resolve_existing_path(video.get("all_frames_data_path"))
    csv_path = main._resolve_existing_path(video.get("df_path"))
    records = main._read_frame_records(frame_path)
    csv_records = main._frame_records_from_csv(csv_path)
    if records and csv_records:
        records = main._merge_frame_records_with_csv_pose(records, csv_records)
    elif csv_records:
        records = csv_records
    exercise = video.get("exercise") or video.get("video_name") or ""
    output: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        record = main._frame_with_exercise_context(record, exercise)
        if main._frame_exercise_key(record, exercise) in {"codman", "pulley"} and record.get("ref_source") != "youtube_mediapipe":
            record = main._apply_youtube_reference_to_frame(record, exercise, overwrite=False)
        output.append(record)
    return output, frame_path


def _video_stem(video: dict[str, object], index: int) -> str:
    for key in ("processed_path", "df_path", "all_frames_data_path"):
        raw = str(video.get(key) or "")
        name = Path(raw.replace("\\", "/")).stem
        if name:
            if name.startswith("f_"):
                return f"processed_{name[2:]}"
            if name.startswith("processed_"):
                for suffix in ("_sound", "_f_data", "_data", "_f", "_pose_h264"):
                    if name.endswith(suffix):
                        name = name[: -len(suffix)]
                return name
    return f"processed_video_{index}"


def _target_size(source: Path, max_width: int = 720) -> tuple[float, int, int]:
    import cv2  # type: ignore[import-not-found]

    cap = cv2.VideoCapture(str(source))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or max_width
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1280
    cap.release()
    target_width = min(width, max_width)
    target_width = max(2, target_width - (target_width % 2))
    target_height = max(2, int(round(height * (target_width / max(1, width)))))
    target_height -= target_height % 2
    return fps, target_width, target_height


def _render_video_only(
    source: Path,
    output_path: Path,
    records: list[dict[str, object]],
    *,
    exercise: object,
    fps: float,
    target_width: int,
    target_height: int,
) -> int:
    import cv2  # type: ignore[import-not-found]

    tmp = output_path.with_name(f"{output_path.stem}_tmp.mp4")
    tmp.unlink(missing_ok=True)
    cap = cv2.VideoCapture(str(source))
    writer = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, fps), (target_width, target_height))
    if not cap.isOpened() or not writer.isOpened():
        cap.release()
        writer.release()
        raise RuntimeError(f"Cannot open render pipeline for {source}")
    rendered = 0
    last_frame_number = 0
    last_report = time.monotonic()
    total = len(records)
    try:
        for pos, record in enumerate(records):
            frame_number = main._frame_number_key(record.get("frame") or record.get("index") or record.get("frame_number")) or pos + 1
            if frame_number != last_frame_number + 1:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_number - 1))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            last_frame_number = frame_number
            if (frame.shape[1], frame.shape[0]) != (target_width, target_height):
                interpolation = cv2.INTER_AREA if target_width < frame.shape[1] else cv2.INTER_LINEAR
                frame = cv2.resize(frame, (target_width, target_height), interpolation=interpolation)
            threshold = main._to_float(record.get("threshold") or record.get("phase_threshold"))
            if threshold is None:
                _, _, threshold = main._phase_for_position(pos, total, exercise)
            display_index = int(main._frame_number_key(record.get("index") or frame_number) or pos + 1)
            rendered_frame = main._draw_pose_analysis_overlay(frame, record, display_index, threshold=float(threshold))
            writer.write(rendered_frame)
            rendered += 1
            now = time.monotonic()
            if rendered == 1 or rendered % 250 == 0 or now - last_report >= 5:
                print(f"render {output_path.name}: {rendered}/{total}", flush=True)
                last_report = now
    finally:
        cap.release()
        writer.release()
    if rendered <= 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"No frames rendered for {source}")
    tmp.replace(output_path)
    return rendered


def _mux_h264(video_path: Path, final_path: Path, records: list[dict[str, object]], fps: float) -> dict[str, object]:
    audio_path, audio_metrics = main._mix_voice_audio_for_records(records, video_path, fps, len(records))
    tmp_final = final_path.with_name(f"{final_path.stem}_tmp{final_path.suffix}")
    tmp_final.unlink(missing_ok=True)
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video_path)]
    if audio_path and audio_path.is_file():
        command.extend(["-i", str(audio_path)])
    command.extend(["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    if audio_path and audio_path.is_file():
        command.extend(["-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest"])
    else:
        command.extend(["-map", "0:v:0", "-an"])
    command.extend(["-movflags", "+faststart", str(tmp_final)])
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=1200)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed")
    tmp_final.replace(final_path)
    return audio_metrics


def render_index(videos: list[object], index: int) -> dict[str, object]:
    if index < 0 or index >= len(videos) or not isinstance(videos[index], dict):
        raise RuntimeError(f"Invalid video index: {index}")
    video = videos[index]
    source = main._resolve_video_source_path(video.get("video_path")) or main._resolve_video_source_path(video.get("processed_path"))
    if not source:
        raise RuntimeError(f"Cannot resolve source video for index {index}")
    records, _ = _records_for_video(video)
    if not records:
        raise RuntimeError(f"No frame records for index {index}")
    pose_count = sum(1 for record in records[: min(120, len(records))] if main._has_complete_pose(record))
    if pose_count <= 0:
        raise RuntimeError(f"Records for index {index} do not include pose points")

    stem = _video_stem(video, index)
    output = REPO_ROOT / "processed_results" / f"{stem}_live.mp4"
    final = REPO_ROOT / "processed_results" / f"{stem}_live_sound.mp4"
    fps, target_width, target_height = _target_size(source)
    print(f"start index {index}: {video.get('video_name')} -> {final.name} ({len(records)} frames)", flush=True)
    rendered = _render_video_only(
        source,
        output,
        records,
        exercise=video.get("exercise") or video.get("video_name"),
        fps=fps,
        target_width=target_width,
        target_height=target_height,
    )
    audio_metrics = _mux_h264(output, final, records, fps)

    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    metrics = dict(metrics)
    metrics.update(audio_metrics)
    metrics["rendered_playback_frames"] = rendered
    metrics["playback_render_source"] = "live_overlay_from_current_frame_data"
    video["processed_path"] = main._relative_repo_path(final)
    video["metrics"] = metrics
    videos[index] = video
    return {
        "index": index,
        "video_name": video.get("video_name"),
        "rendered": rendered,
        "processed_path": video["processed_path"],
        "audio": audio_metrics,
    }


def main_cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("indices", nargs="+", type=int)
    args = parser.parse_args()
    db_path = REPO_ROOT / "database" / "video_list.json"
    videos = read_json(db_path, [])
    if not isinstance(videos, list):
        raise RuntimeError("database/video_list.json is not a list")
    results = []
    for index in args.indices:
        results.append(render_index(videos, index))
        write_json(db_path, videos)
    write_json(db_path, videos)
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

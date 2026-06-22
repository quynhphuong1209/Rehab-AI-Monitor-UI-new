from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import main  # noqa: E402
from storage.json_store import read_json, write_json  # noqa: E402


VIDEO_MATCH = "processed_results/f_1781140111.json"
DEST_FRAME_PATH = REPO_ROOT / "processed_results" / "f_1781140111.json"
SOURCE_POSE_PATH = REPO_ROOT / "processed_results" / "f_e0760f712b.json"
CSV_PATH = REPO_ROOT / "processed_results" / "processed_1781140111_f_data.csv"
OUTPUT_PATH = REPO_ROOT / "processed_results" / "processed_1781140111_f.mp4"
FINAL_PATH = REPO_ROOT / "processed_results" / "processed_1781140111_sound.mp4"
FRAMES_ZIP = REPO_ROOT / "processed_results" / "processed_1781140111_frames.zip"


def _backup_once(path: Path) -> None:
    if not path.exists():
        return
    backup = path.with_name(f"{path.stem}.before_pose_restore{path.suffix}")
    if not backup.exists():
        shutil.copy2(path, backup)


def _pose_keys(record: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for idx in range(33):
        for suffix in ("x", "y", "z", "vis"):
            key = f"pt{idx}_{suffix}"
            if key in record:
                copied[key] = record[key]
    for key in (
        "detected",
        "pose_selector",
        "pose_selector_score",
        "timestamp_seconds",
        "source_width",
        "source_height",
    ):
        if key in record:
            copied[key] = record[key]
    return copied


def _write_csv_from_records(path: Path, records: list[dict[str, object]]) -> None:
    fieldnames = sorted(
        {
            key
            for record in records
            for key, value in record.items()
            if not isinstance(value, (dict, list))
        }
    )
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key) for key in fieldnames})


def _video_index(videos: list[dict[str, object]]) -> int:
    for index, video in enumerate(videos):
        if str(video.get("all_frames_data_path", "")).replace("\\", "/") == VIDEO_MATCH:
            return index
    raise RuntimeError(f"Cannot find video record for {VIDEO_MATCH}")


def _status_counts(records: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        status = str(record.get("status") or record.get("phase_status") or "").upper()
        counts[status] = counts.get(status, 0) + 1
    return counts


def main_cli() -> int:
    dest_records = read_json(DEST_FRAME_PATH, [])
    source_records = read_json(SOURCE_POSE_PATH, [])
    if not isinstance(dest_records, list) or not isinstance(source_records, list):
        raise RuntimeError("Frame JSON must be a list")
    if len(dest_records) != len(source_records):
        raise RuntimeError(f"Frame count mismatch: dest={len(dest_records)} source={len(source_records)}")
    if not dest_records:
        raise RuntimeError("No frames to restore")

    _backup_once(DEST_FRAME_PATH)
    _backup_once(CSV_PATH)
    _backup_once(OUTPUT_PATH)
    _backup_once(FINAL_PATH)
    _backup_once(FRAMES_ZIP)

    restored = 0
    for index, (dest, source) in enumerate(zip(dest_records, source_records), start=1):
        if not isinstance(dest, dict) or not isinstance(source, dict):
            continue
        pose = _pose_keys(source)
        if len([key for key in pose if key.endswith("_x")]) < 33:
            raise RuntimeError(f"Source pose missing 33 points at frame {index}")
        dest.update(pose)
        dest["detected"] = True
        dest["filtered_stranger"] = False
        if str(dest.get("status") or dest.get("phase_status") or "").upper() != "UNKNOWN":
            dest["stranger_reason"] = ""
        dest["exercise_key"] = "codman"
        dest["exercise"] = dest.get("exercise") or "Bài tập con lắc Codman"
        dest["ref_source"] = dest.get("ref_source") or "youtube_mediapipe"
        restored += 1

    DEST_FRAME_PATH.write_text(json.dumps(dest_records, ensure_ascii=False), encoding="utf-8")
    _write_csv_from_records(CSV_PATH, dest_records)

    videos_raw = read_json(REPO_ROOT / "database" / "video_list.json", [])
    if not isinstance(videos_raw, list):
        raise RuntimeError("database/video_list.json must be a list")
    videos: list[dict[str, object]] = [video for video in videos_raw if isinstance(video, dict)]
    video_pos = _video_index(videos)
    video = videos[video_pos]
    source_video = main._resolve_video_source_path(video.get("video_path")) or main._resolve_video_source_path(video.get("processed_path"))
    if not source_video:
        raise RuntimeError("Cannot resolve source video")

    import cv2  # type: ignore[import-not-found]

    cap = cv2.VideoCapture(str(source_video))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 720
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1280
    cap.release()
    target_width = min(width, 720)
    target_width = max(2, target_width - (target_width % 2))
    target_height = max(2, int(round(height * (target_width / max(1, width)))))
    target_height -= target_height % 2

    rendered = main._render_analysis_artifacts_from_records(
        source_video,
        OUTPUT_PATH,
        FRAMES_ZIP,
        dest_records,
        fps=fps,
        skip=1,
        target_width=target_width,
        target_height=target_height,
        exercise=video.get("exercise") or "Bài tập con lắc Codman",
        on_progress=lambda done, total: print(f"render {done}/{total}", flush=True),
    )
    if rendered != len(dest_records):
        raise RuntimeError(f"Rendered {rendered}/{len(dest_records)} frames")

    audio_path, audio_metrics = main._mix_voice_audio_for_records(dest_records, OUTPUT_PATH, fps, len(dest_records))
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(OUTPUT_PATH)]
    if audio_path and audio_path.is_file():
        command.extend(["-i", str(audio_path)])
    command.extend(["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    if audio_path and audio_path.is_file():
        command.extend(["-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest"])
    else:
        command.extend(["-map", "0:v:0", "-an"])
    command.extend(["-movflags", "+faststart", str(FINAL_PATH)])
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=900)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed")

    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    metrics = dict(metrics)
    metrics.update(audio_metrics)
    metrics["rendered_frames"] = rendered
    metrics["frame_khong_nhan_dang"] = 0
    metrics["tong_frame_da_cham"] = len(dest_records)
    video["metrics"] = metrics
    video["accuracy"] = round(float(metrics.get("do_chinh_xac") or metrics.get("ty_le_tong_the") or 0), 1)
    video["status"] = "Đã phân tích"
    video["processed_path"] = "processed_results/processed_1781140111_sound.mp4"
    video["frames_zip"] = "processed_results/processed_1781140111_frames.zip"
    video["frames_zip_path"] = "processed_results/processed_1781140111_frames.zip"
    video["all_frames_data_path"] = "processed_results/f_1781140111.json"
    video["df_path"] = "processed_results/processed_1781140111_f_data.csv"
    videos_raw[video_pos] = video
    write_json(REPO_ROOT / "database" / "video_list.json", videos_raw)

    print(
        json.dumps(
            {
                "restored_pose_frames": restored,
                "rendered_frames": rendered,
                "counts": _status_counts(dest_records),
                "audio": audio_metrics,
                "video": str(FINAL_PATH),
                "frames_zip": str(FRAMES_ZIP),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import main  # noqa: E402
from storage.json_store import read_json, write_json  # noqa: E402


VIDEO_INDEX = 7
FRAME_PATH = REPO_ROOT / "processed_results" / "f_e0760f712b.json"
OUTPUT_PATH = REPO_ROOT / "processed_results" / "processed_e0760f712b.mp4"
FINAL_PATH = REPO_ROOT / "processed_results" / "processed_e0760f712b_f.mp4"
FRAMES_ZIP = REPO_ROOT / "processed_results" / "processed_e0760f712b_frames.zip"
PROGRESS_PATH = REPO_ROOT / "processed_results" / "progress_e0760f712b06f36c3c6181b45acd47c0.json"


def _update_progress(message: str, progress: float) -> None:
    payload = read_json(PROGRESS_PATH, {})
    if isinstance(payload, dict):
        payload["status"] = "processing" if progress < 1 else "success"
        payload["progress"] = progress
        payload["status_msg"] = message
        write_json(PROGRESS_PATH, payload)


def main_cli() -> int:
    videos = read_json(REPO_ROOT / "database" / "video_list.json", [])
    if not isinstance(videos, list) or VIDEO_INDEX >= len(videos):
        print("Missing video record")
        return 2
    video = videos[VIDEO_INDEX]
    source = main._resolve_video_source_path(video.get("video_path")) or main._resolve_video_source_path(video.get("processed_path"))
    if not source:
        print("Missing source video")
        return 2
    records = read_json(FRAME_PATH, [])
    if not isinstance(records, list) or not records:
        print("Missing records")
        return 2

    import cv2  # type: ignore[import-not-found]

    cap = cv2.VideoCapture(str(source))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 720
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1280
    cap.release()
    target_width = min(width, 720)
    target_width = max(2, target_width - (target_width % 2))
    target_height = max(2, int(round(height * (target_width / max(1, width)))))
    target_height = target_height - (target_height % 2)

    _update_progress("Đang render lại video/frames sau repair UNKNOWN.", 0.84)
    rendered = main._render_analysis_artifacts_from_records(
        source,
        OUTPUT_PATH,
        FRAMES_ZIP,
        records,
        fps=fps,
        skip=1,
        target_width=target_width,
        target_height=target_height,
        exercise=video.get("exercise") or "Bài tập con lắc Codman",
        on_progress=lambda done, total: _update_progress(f"Đang render lại overlay: frame {done}/{total}", 0.84 + min(0.08, done / max(1, total) * 0.08)),
    )
    FRAME_PATH.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    _update_progress("Đang mix âm thanh đúng/gần đúng/sai.", 0.93)
    audio_path, audio_metrics = main._mix_voice_audio_for_records(records, OUTPUT_PATH, fps, len(records))
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(OUTPUT_PATH),
    ]
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
        print(result.stderr)
        return result.returncode or 1

    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    metrics.update(audio_metrics)
    metrics["rendered_frames"] = rendered
    video["metrics"] = metrics
    video["processed_path"] = "processed_results/processed_e0760f712b_f.mp4"
    video["frames_zip"] = "processed_results/processed_e0760f712b_frames.zip"
    video["frames_zip_path"] = "processed_results/processed_e0760f712b_frames.zip"
    video["all_frames_data_path"] = "processed_results/f_e0760f712b.json"
    video["df_path"] = "processed_results/processed_e0760f712b_data.csv"
    videos[VIDEO_INDEX] = video
    write_json(REPO_ROOT / "database" / "video_list.json", videos)

    payload = read_json(PROGRESS_PATH, {})
    if isinstance(payload, dict):
        payload["status"] = "success"
        payload["progress"] = 1.0
        payload["status_msg"] = "Đã repair + render lại video/frames/audio; REF/ML/database đã cập nhật."
        result_payload = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        result_payload["processed_video_path"] = "processed_results/processed_e0760f712b_f.mp4"
        result_payload["output_video_path"] = "processed_results/processed_e0760f712b_f.mp4"
        result_payload["frames_zip"] = "processed_results/processed_e0760f712b_frames.zip"
        result_payload["frames_zip_path"] = "processed_results/processed_e0760f712b_frames.zip"
        stats = result_payload.get("stats") if isinstance(result_payload.get("stats"), dict) else {}
        stats.update(metrics)
        result_payload["stats"] = stats
        payload["result"] = result_payload
        write_json(PROGRESS_PATH, payload)
    print(json.dumps({"rendered": rendered, "audio": audio_metrics, "final": str(FINAL_PATH)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

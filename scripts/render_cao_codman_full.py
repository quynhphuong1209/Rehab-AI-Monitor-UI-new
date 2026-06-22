from __future__ import annotations

import json
import sys
import time
import zipfile
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import _draw_pose_analysis_overlay, _frame_number_key, _load_data, _phase_for_position, _resolve_existing_path, _resolve_video_source_path  # noqa: E402


def main() -> int:
    videos = _load_data("video_list")
    video = next(v for v in videos if isinstance(v, dict) and "Cao" in str(v.get("video_name")) and "Codman" in str(v.get("video_name")))
    source = _resolve_video_source_path(video.get("video_path")) or _resolve_video_source_path(video.get("processed_path"))
    records_path = _resolve_existing_path(video.get("all_frames_data_path"))
    output = ROOT / "processed_results" / "processed_1781140111_f.mp4"
    zip_path = ROOT / "processed_results" / "processed_1781140111_frames.zip"
    if not source or not records_path:
        print("missing source/records", source, records_path)
        return 2
    records = json.loads(records_path.read_text(encoding="utf-8"))
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        print("cannot open source", source)
        return 3
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0) or 30.0
    raw_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 1080
    raw_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 1920
    width = 720
    height = max(2, int(raw_h * width / max(1, raw_w)))
    height -= height % 2
    tmp = output.with_name(f"{output.stem}_full_tmp.mp4")
    tmp_h264 = output.with_name(f"{output.stem}_full_h264_tmp.mp4")
    tmp_zip = zip_path.with_name(f"{zip_path.stem}_full_tmp.zip")
    for path in (tmp, tmp_h264, tmp_zip):
        path.unlink(missing_ok=True)
    writer = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        cap.release()
        print("writer failed")
        return 4
    done = 0
    last = time.time()
    try:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for pos, record in enumerate(records):
                frame_no = _frame_number_key(record.get("index") or record.get("frame") or record.get("frame_number")) or pos + 1
                # Records are sequential for this artifact. Read sequentially to avoid slow random seek.
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                if (frame.shape[1], frame.shape[0]) != (width, height):
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
                _, _, fallback_threshold = _phase_for_position(pos, len(records), video.get("exercise"))
                threshold = float(record.get("threshold") or record.get("phase_threshold") or fallback_threshold)
                rendered = _draw_pose_analysis_overlay(frame, record, int(frame_no), threshold=threshold)
                writer.write(rendered)
                ok_jpg, encoded = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok_jpg:
                    archive.writestr(f"f_{pos + 1:06d}.jpg", encoded.tobytes())
                done += 1
                if done == 1 or done % 250 == 0 or time.time() - last >= 5:
                    print(f"render {done}/{len(records)}", flush=True)
                    last = time.time()
    finally:
        cap.release()
        writer.release()
    if done != len(records):
        print(f"incomplete render {done}/{len(records)}")
        return 5
    import subprocess

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(tmp),
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(tmp_h264),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=300)
    if result.returncode != 0 or not tmp_h264.is_file():
        print("ffmpeg failed", result.stderr[-500:])
        return 6
    tmp_h264.replace(output)
    tmp_zip.replace(zip_path)
    tmp.unlink(missing_ok=True)
    print(json.dumps({"rendered": done, "output": str(output), "zip": str(zip_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

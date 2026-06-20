"""Video background job helpers."""

from __future__ import annotations

import os
from datetime import datetime


def transcode_temp_path(final_h264_path: str) -> str:
    tmp_path = str(final_h264_path or "").replace("_f.mp4", "_ftmp.mp4")
    if tmp_path == final_h264_path:
        tmp_path = f"{final_h264_path}.ftmp.mp4"
    return tmp_path


def transcode_error_log_path(final_h264_path: str) -> str:
    return os.path.join(os.path.dirname(str(final_h264_path or "")), "transcode_error.txt")


def original_candidates_for_h264(video_path: str) -> list[str]:
    base_without_f = str(video_path or "").replace("_f.mp4", "")
    return [base_without_f + ext for ext in [".mp4", ".mov", ".MOV", ".avi", ".mkv"]]


def build_async_h264_command(src_path: str, tmp_h264_path: str, *, has_audio: bool) -> list[str]:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        src_path,
        "-vcodec",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "ultrafast",
        "-vf",
        "scale=-2:min(480\\,ih)",
        "-crf",
        "30",
        "-maxrate",
        "500k",
        "-bufsize",
        "1000k",
        "-movflags",
        "+faststart",
        "-threads",
        "2",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
    ]
    if has_audio:
        cmd.extend(["-c:a", "aac"])
    else:
        cmd.extend(["-an"])
    cmd.extend(["-f", "mp4", tmp_h264_path])
    return cmd


def write_transcode_error_log(
    error_log_path: str,
    *,
    cmd: list[str] | None = None,
    exit_code: int | None = None,
    stderr: str | None = None,
    message: str | None = None,
    exception: object | None = None,
    now: datetime | None = None,
) -> str:
    stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    with open(error_log_path, "w", encoding="utf-8") as handle:
        handle.write(f"Time: {stamp}\n")
        if cmd is not None:
            handle.write(f"Cmd: {' '.join(cmd)}\n")
        if exit_code is not None:
            handle.write(f"Exit Code: {exit_code}\n")
        if stderr is not None:
            handle.write(f"Stderr:\n{stderr}\n")
        if message:
            handle.write(f"Error: {message}\n")
        if exception is not None:
            handle.write(f"Exception: {exception}\n")
    return error_log_path

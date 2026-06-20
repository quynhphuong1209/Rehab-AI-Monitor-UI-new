from datetime import datetime

from video.jobs import (
    build_async_h264_command,
    original_candidates_for_h264,
    transcode_error_log_path,
    transcode_temp_path,
    write_transcode_error_log,
)


def test_transcode_paths_and_original_candidates():
    assert transcode_temp_path("clip_f.mp4") == "clip_ftmp.mp4"
    assert transcode_temp_path("clip.mp4") == "clip.mp4.ftmp.mp4"
    assert transcode_error_log_path("processed/clip_f.mp4").replace("\\", "/").endswith(
        "processed/transcode_error.txt"
    )
    assert original_candidates_for_h264("patient_uploads/clip_f.mp4") == [
        "patient_uploads/clip.mp4",
        "patient_uploads/clip.mov",
        "patient_uploads/clip.MOV",
        "patient_uploads/clip.avi",
        "patient_uploads/clip.mkv",
    ]


def test_build_async_h264_command_audio_modes():
    with_audio = build_async_h264_command("in.mov", "out_ftmp.mp4", has_audio=True)
    without_audio = build_async_h264_command("in.mov", "out_ftmp.mp4", has_audio=False)

    assert with_audio[:4] == ["ffmpeg", "-y", "-i", "in.mov"]
    assert with_audio[-3:] == ["-f", "mp4", "out_ftmp.mp4"]
    assert ["-c:a", "aac"] == with_audio[-5:-3]
    assert "-an" in without_audio


def test_write_transcode_error_log(tmp_path):
    log_path = tmp_path / "transcode_error.txt"

    write_transcode_error_log(
        str(log_path),
        cmd=["ffmpeg", "-i", "in.mov"],
        exit_code=1,
        stderr="bad codec",
        now=datetime(2026, 6, 20, 8, 30),
    )

    content = log_path.read_text(encoding="utf-8")
    assert "Time: 2026-06-20 08:30:00" in content
    assert "Cmd: ffmpeg -i in.mov" in content
    assert "Exit Code: 1" in content
    assert "bad codec" in content

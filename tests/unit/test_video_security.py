from video.serving import (
    allowed_media_file_path,
    build_video_media_url,
    media_token_from_request_path,
    register_media_token,
    resolve_media_token,
    video_media_allowed_roots,
)
from video.validation import sanitize_filename, upload_video_magic_matches


def test_sanitize_filename_removes_path_and_unsafe_chars():
    assert sanitize_filename("../../Benh nhan 01?.MP4") == "Benh_nhan_01_.mp4"


def test_video_magic_checks_known_headers():
    assert upload_video_magic_matches(".mp4", b"\x00\x00\x00\x18ftypmp42")
    assert upload_video_magic_matches(".avi", b"RIFFxxxxAVI ")
    assert not upload_video_magic_matches(".mp4", b"MZ executable")


def test_media_token_only_resolves_allowed_file(tmp_path):
    upload_root = tmp_path / "patient_uploads"
    upload_root.mkdir()
    video_path = upload_root / "clip.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    outside_path = tmp_path / "outside.mp4"
    outside_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")

    roots = video_media_allowed_roots(data_dir=tmp_path, upload_dir=upload_root)
    tokens = {}
    token = register_media_token(tokens, video_path, roots, ttl_seconds=60, token_factory=lambda _: "tok")

    assert token == "tok"
    assert allowed_media_file_path(video_path, roots) == str(video_path.resolve())
    assert allowed_media_file_path(outside_path, roots) is None
    assert resolve_media_token(tokens, "tok", roots) == str(video_path.resolve())
    assert media_token_from_request_path("/_media/tok/clip.mp4") == "tok"
    assert build_video_media_url(8765, "tok", video_path).endswith("/_media/tok/clip.mp4")

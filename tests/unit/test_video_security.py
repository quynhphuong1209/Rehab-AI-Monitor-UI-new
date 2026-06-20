from video.serving import (
    TranscodingJobRegistry,
    allowed_media_file_path,
    build_direct_video_html,
    build_video_media_url,
    get_final_h264_path,
    is_http_video_source,
    is_non_playable_video_path,
    is_scratch_video_path,
    media_token_from_request_path,
    register_media_token,
    resolve_media_token,
    strip_to_original_upload,
    video_fallback_paths,
    video_media_allowed_roots,
    video_raw_only_paths,
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


def test_transcoding_job_registry_prevents_duplicate_jobs():
    registry = TranscodingJobRegistry()

    assert registry.start("clip_f.mp4")
    assert not registry.start("clip_f.mp4")
    assert "clip_f.mp4" in registry
    assert len(registry) == 1

    registry.discard("clip_f.mp4")
    assert "clip_f.mp4" not in registry
    assert registry.start("clip_f.mp4")


def test_direct_http_video_html_escapes_url():
    unsafe_url = 'https://example.test/clip.mp4" onerror="alert(1)'

    assert is_http_video_source(unsafe_url)
    assert not is_http_video_source("patient_uploads/clip.mp4")

    html = build_direct_video_html(unsafe_url)
    assert "https://example.test/clip.mp4&quot; onerror=&quot;alert(1)" in html
    assert 'src="https://example.test/clip.mp4" onerror="alert(1)"' not in html


def test_video_path_helpers_filter_artifacts_and_build_fallbacks():
    assert is_non_playable_video_path("D:/data/processed_results/processed_clip/_frames/out.mp4")
    assert is_non_playable_video_path("results.csv")
    assert not is_non_playable_video_path("patient_uploads/clip.mov")

    assert get_final_h264_path("patient_uploads/clip.mov") == "patient_uploads/clip_f.mp4"
    assert get_final_h264_path("patient_uploads/clip_f.mp4") == "patient_uploads/clip_f.mp4"
    assert is_scratch_video_path("patient_uploads/clip_ftmp.mp4")
    assert strip_to_original_upload("patient_uploads/clip_f.mp4") == "patient_uploads/clip.mp4"

    assert video_fallback_paths("patient_uploads/clip.mov") == [
        "patient_uploads/clip_f.mp4",
        "patient_uploads/clip.mov",
    ]
    assert video_raw_only_paths("patient_uploads/clip.mp4") == [
        "patient_uploads/clip.mp4",
        "patient_uploads/clip.mov",
    ]

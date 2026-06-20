from backend.hf_workflow import (
    hf_auth_headers,
    hf_dataset_resolve_url,
    hf_is_library_error,
    hf_local_target_path,
    hf_min_size_for_path,
    hf_token_fingerprint,
)


def test_hf_min_size_for_path_by_extension():
    assert hf_min_size_for_path("metrics.csv") == 80
    assert hf_min_size_for_path("video_list.json") == 2
    assert hf_min_size_for_path("clip.mp4") == 5 * 1024


def test_hf_auth_and_fingerprint_helpers():
    assert hf_auth_headers(None) == {}
    assert hf_auth_headers("tok") == {"Authorization": "Bearer tok"}
    assert hf_token_fingerprint("tok", "dataset") == hf_token_fingerprint("tok", "dataset")


def test_hf_library_error_detection():
    assert hf_is_library_error("ImportError: cannot import name HfApi")
    assert hf_is_library_error("No module named 'huggingface_hub'")
    assert not hf_is_library_error("HTTP 404")


def test_hf_dataset_url_and_local_target_normalize_paths(tmp_path):
    url = hf_dataset_resolve_url("owner/data", r"patient_uploads\clip 1.mp4")
    assert url == "https://huggingface.co/datasets/owner/data/resolve/main/patient_uploads/clip%201.mp4"

    target = hf_local_target_path(tmp_path, r"patient_uploads\clip.mp4")
    assert target.endswith("patient_uploads/clip.mp4") or target.endswith(r"patient_uploads\clip.mp4")

from backend.frame_gallery import (
    filter_frame_indices,
    frame_phase_status,
    frame_status_counts,
    paginate_indices,
    resolve_phase_threshold,
)


PHASE_ERROR = {"g1": 45, "g2": 30, "g3": 15}


def test_resolve_phase_threshold_uses_segment_bounds():
    assert resolve_phase_threshold({"index": 2}, None, segment_bounds=[0, 3, 6, 9], phase_error=PHASE_ERROR) == 45
    assert resolve_phase_threshold({"index": 5}, None, segment_bounds=[0, 3, 6, 9], phase_error=PHASE_ERROR) == 30
    assert resolve_phase_threshold({"index": 8}, None, segment_bounds=[0, 3, 6, 9], phase_error=PHASE_ERROR) == 15
    assert resolve_phase_threshold({"index": 8}, 12, segment_bounds=[0, 3, 6, 9], phase_error=PHASE_ERROR) == 12


def test_frame_phase_status_regular_and_gay_exercise():
    regular = {"goc_vai": 92, "goc_khuyu": 171, "eval_info": {"shoulder_ref": 90, "elbow_ref": 170}}
    near = {"goc_vai": 130, "goc_khuyu": 210, "eval_info": {"shoulder_ref": 90, "elbow_ref": 170}}
    fail = {"goc_vai": 180, "goc_khuyu": 40, "eval_info": {"shoulder_ref": 90, "elbow_ref": 170}}
    gay = {
        "goc_vai_trai": 91,
        "goc_vai_phai": 89,
        "goc_khuyu_trai": 169,
        "goc_khuyu_phai": 171,
        "eval_info": {"shoulder_ref": 90, "elbow_ref": 170},
    }

    assert frame_phase_status(regular, 15, is_gay_exercise=False, segment_bounds=None, phase_error=PHASE_ERROR) == "PASS"
    assert frame_phase_status(near, 30, is_gay_exercise=False, segment_bounds=None, phase_error=PHASE_ERROR) == "NEAR"
    assert frame_phase_status(fail, 30, is_gay_exercise=False, segment_bounds=None, phase_error=PHASE_ERROR) == "FAIL"
    assert frame_phase_status(gay, 15, is_gay_exercise=True, segment_bounds=None, phase_error=PHASE_ERROR) == "PASS"


def test_filter_count_and_paginate_frame_indices():
    frames = [{"status": "PASS"}, {"status": "NEAR"}, {"status": "FAIL"}, {"status": "PASS"}]
    status_fn = lambda frame: frame["status"]

    assert filter_frame_indices([0, 1, 2, 3], frames, "PASS", status_fn) == [0, 3]
    assert filter_frame_indices([0, 1, 2, 3], frames, "Tất cả", status_fn) == [0, 1, 2, 3]
    assert frame_status_counts([0, 1, 2, 3], frames, status_fn) == {"PASS": 2, "NEAR": 1, "FAIL": 1}
    assert paginate_indices([0, 1, 2, 3, 4], page=2, per_page=2) == ([2, 3], 2, 3, 5)
    assert paginate_indices([0, 1, 2], page=99, per_page=2) == ([2], 2, 2, 3)

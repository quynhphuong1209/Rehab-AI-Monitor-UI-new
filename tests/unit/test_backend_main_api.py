from __future__ import annotations

import json

import numpy as np

import backend.main as backend_main
from backend.main import (
    ROLE_ADMIN,
    ROLE_DOCTOR_KTV,
    ROLE_PATIENT,
    ROLE_RESEARCHER,
    EvaluationRequest,
    _auto_orient_pose_preview,
    _evaluation_record_for_video,
    _force_portrait_pose_frame,
    _frame_group_summary,
    _phase_for_position,
    _segment_bounds_from_angle_items,
    _resolve_playback_video_path,
    _resolve_readable_video_sibling,
    _read_frame_payload,
    _read_frame_dir,
    _read_chart_payload,
    _frame_should_be_unknown,
    _has_complete_pose,
    _local_artifact_match_score,
    _mark_filtered_stranger,
    _scope_records,
    _merge_video_ai_evaluation_summaries,
    _match_evaluations_for_video,
    _media_token_meta,
    _match_youtube_reference_for_frame,
    _needs_video_pose_frame_preference,
    _phase_status_for_frame,
    _pose_video_context_priority,
    _take_recent_evaluations,
    _video_detail,
    _hydrate_video_artifacts,
    build_login_options,
    canonical_role,
    role_key,
)


def complete_pose_record(**updates):
    record = {
        "shoulder_ref": 90,
        "elbow_ref": 170,
    }
    for idx in range(33):
        record[f"pt{idx}_x"] = 0.5
        record[f"pt{idx}_y"] = 0.5
    record.update(updates)
    return record


def test_role_key_accepts_vietnamese_and_short_aliases() -> None:
    assert role_key("Quản trị viên") == "admin"
    assert role_key("QTV") == "admin"
    assert role_key("Bác sĩ / KTV PHCN") == "doctor_ktv"
    assert role_key("NCV") == "researcher"
    assert role_key("Bệnh nhân") == "patient"


def test_canonical_role_returns_public_labels() -> None:
    assert canonical_role("admin") == ROLE_ADMIN
    assert canonical_role("bac si") == ROLE_DOCTOR_KTV
    assert canonical_role("nghien cuu vien") == ROLE_RESEARCHER
    assert canonical_role("") == ROLE_PATIENT


def test_patient_scope_limits_records_to_current_user() -> None:
    user = {
        "username": "patient-a",
        "full_name": "Nguyen Van A",
        "role_key": "patient",
    }
    records = [
        {"username": "patient-a", "value": 1},
        {"patient_username": "Nguyen Van A", "value": 2},
        {"username": "patient-b", "value": 3},
    ]

    assert _scope_records(records, user) == records[:2]


def test_clinical_roles_can_see_all_records() -> None:
    user = {
        "username": "doctor",
        "full_name": "Doctor",
        "role_key": "doctor_ktv",
    }
    records = [{"username": "a"}, {"username": "b"}]

    assert _scope_records(records, user) == records


def test_login_options_group_users_by_role(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.main.load_users",
        lambda: {
            "admin1": {"role": ROLE_ADMIN, "full_name": "Admin 1", "password": "hidden"},
            "doctor1": {"role": ROLE_DOCTOR_KTV, "full_name": "Doctor 1", "password": "hidden"},
            "patient1": {"role": ROLE_PATIENT, "full_name": "Patient 1", "password": "hidden"},
        },
    )

    payload = build_login_options()
    groups = {group["role_key"]: group for group in payload["roles"]}

    assert groups["admin"]["count"] == 1
    assert groups["doctor_ktv"]["users"][0]["username"] == "doctor1"
    assert groups["patient"]["users"][0]["full_name"] == "Patient 1"
    assert "password" not in groups["admin"]["users"][0]


def test_video_detail_matches_evaluations_and_fallback_chart(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.main._load_data",
        lambda name: [
            {
                "patient_username": "patient1",
                "video_name": "v1.mp4",
                "exercise": "Codman",
                "doctor_result": "Gần đúng",
            }
        ]
        if name == "doctor_evaluations"
        else [],
    )
    user = {"username": "patient1", "full_name": "Patient 1", "role_key": "patient"}
    detail = _video_detail(
        {"username": "patient1", "video_name": "v1.mp4", "exercise": "Codman", "accuracy": 72},
        0,
        user,
    )

    assert detail["latest_evaluation"]["doctor_result"] == "Gần đúng"
    assert detail["chart"]["points"][1]["y"] == 72
    assert detail["media"]["file_exists"] is False


def test_video_detail_matches_timestamped_processed_name_to_clean_evaluation() -> None:
    video = {
        "username": "Nguyen Thi Nga",
        "full_name": "Nguyen Thi Nga",
        "video_name": "163003_Nguyen Thi Nga - Bai tap voi gay_ftmp.mp4",
        "exercise": "Bai tap voi gay (Pulley Exercise)",
    }
    evaluations = [
        {
            "patient_username": "Nguyen Thi Nga",
            "video_name": "Nguyen Thi Nga - Bai tap voi gay.mp4",
            "exercise": "Bai tap voi gay (Pulley Exercise)",
            "doctor_result": "Gan dung",
            "time": "08:50 - 15/06/2026",
        }
    ]

    matches = _match_evaluations_for_video(video, evaluations)

    assert matches == evaluations


def test_hydrate_video_artifacts_uses_debug_backup_when_database_record_is_missing_paths(
    monkeypatch, tmp_path
) -> None:
    processed = tmp_path / "processed_1_f.mp4"
    csv_path = tmp_path / "processed_1_f_data.csv"
    frames_path = tmp_path / "f_1.json"
    processed.write_bytes(b"video")
    csv_path.write_text("frame,goc_vai,goc_khuyu\n1,40,160\n", encoding="utf-8")
    frames_path.write_text("[]", encoding="utf-8")

    backup = {
        "username": "Patient A",
        "full_name": "Patient A",
        "video_name": "Patient A - Codman.mp4",
        "exercise": "Codman",
        "video_path": "patient_uploads/patient_a_202606240001.mp4",
        "processed_path": str(processed),
        "df_path": str(csv_path),
        "all_frames_data_path": str(frames_path),
        "metrics": {"do_chinh_xac": 88},
    }
    monkeypatch.setattr("backend.main._find_progress_for_video", lambda *args, **kwargs: None)
    monkeypatch.setattr("backend.main._backup_video_records", lambda: [backup])

    hydrated = _hydrate_video_artifacts(
        {
            "username": "Patient A",
            "full_name": "Patient A",
            "video_name": "Patient A - Codman.mp4",
            "exercise": "Codman",
            "video_path": "patient_uploads/patient_a_202606240001.mp4",
            "accuracy": None,
        }
    )

    assert hydrated["processed_path"] == str(processed)
    assert hydrated["df_path"] == str(csv_path)
    assert hydrated["all_frames_data_path"] == str(frames_path)
    assert hydrated["metrics"]["do_chinh_xac"] == 88
    assert hydrated["accuracy"] == 88
    assert hydrated["_artifact_source"] == "debug_backup"


def test_hydrate_video_artifacts_uses_richer_local_video_record_for_same_slot(
    monkeypatch, tmp_path
) -> None:
    processed = tmp_path / "processed_hanh_nguyen_codman_f.mp4"
    csv_path = tmp_path / "processed_hanh_nguyen_codman_f_data.csv"
    frames_path = tmp_path / "f_hanh_nguyen_codman.json"
    zip_path = tmp_path / "processed_hanh_nguyen_codman_frames.zip"
    processed.write_bytes(b"video")
    csv_path.write_text("frame,goc_vai,goc_khuyu\n1,40,160\n", encoding="utf-8")
    frames_path.write_text("[]", encoding="utf-8")
    zip_path.write_bytes(b"PK\003\004" + b"0" * 64)

    local_record = {
        "username": "Hoàng Hạnh Nguyên",
        "full_name": "Hoàng Hạnh Nguyên",
        "video_name": "160754_Hoàng Hạnh Nguyên - Codman.mp4",
        "exercise": "Bài tập con lắc Codman",
        "video_path": "patient_uploads/hoang_hanh_nguyen_202606240002.mp4",
        "time": "16:47 - 14/06/2026",
        "processed_path": str(processed),
        "df_path": str(csv_path),
        "all_frames_data_path": str(frames_path),
        "frames_zip": str(zip_path),
        "metrics": {"do_chinh_xac": 88.3},
    }
    monkeypatch.setattr("backend.main._find_progress_for_video", lambda *args, **kwargs: None)
    monkeypatch.setattr("backend.main._backup_video_records", lambda: [])
    monkeypatch.setattr("backend.main._load_data", lambda name: [local_record] if name == "video_list" else [])

    hydrated = _hydrate_video_artifacts(
        {
            "username": "Hoàng Hạnh Nguyên",
            "full_name": "Hoàng Hạnh Nguyên",
            "video_name": "Hoàng Hạnh Nguyên - Codman.mp4",
            "exercise": "Bài tập con lắc Codman",
            "video_path": "patient_uploads/hoang_hanh_nguyen_202606240002.mp4",
            "accuracy": 99.5,
            "processed_path": None,
            "df_path": None,
            "all_frames_data_path": None,
        }
    )

    assert hydrated["processed_path"] == str(processed)
    assert hydrated["df_path"] == str(csv_path)
    assert hydrated["all_frames_data_path"] == str(frames_path)
    assert hydrated["frames_zip"] == str(zip_path)
    assert hydrated["accuracy"] == 99.5
    assert hydrated["_artifact_source"] == "local_video_list"
    assert hydrated["_local_video_artifacts"] is True
    assert hydrated["source_video_index"] == 0


def test_frame_phase_groups_follow_app_py_thresholds() -> None:
    assert _phase_for_position(0, 90, "Bài tập con lắc Codman") == ("g1", "G1 · Khởi đầu", 45)
    assert _phase_for_position(30, 90, "Bài tập con lắc Codman") == ("g2", "G2 · Hồi phục", 30)
    assert _phase_for_position(60, 90, "Bài tập con lắc Codman") == ("g3", "G3 · Chuẩn xác", 15)
    assert _phase_for_position(60, 90, "Bài tập với gậy (Pulley Exercise)") == ("overview", "Tổng quan", 30)

    frames = [
        complete_pose_record(phase="g1", goc_vai=90, goc_khuyu=170),
        complete_pose_record(phase="g2", goc_vai=125, goc_khuyu=170),
        complete_pose_record(phase="g3", goc_vai=130, goc_khuyu=170),
    ]
    groups = {item["key"]: item for item in _frame_group_summary(frames, len(frames), "Codman")}

    assert groups["g1"]["threshold"] == 45
    assert groups["g2"]["threshold"] == 30
    assert groups["g3"]["threshold"] == 15
    assert groups["all"]["pass"] == 1
    assert groups["all"]["near"] == 1
    assert groups["all"]["fail"] == 1


def test_evaluation_record_for_video_keeps_legacy_schema() -> None:
    record = _evaluation_record_for_video(
        {"username": "patient1", "full_name": "Patient One", "video_name": "v1.mp4", "exercise": "Codman", "accuracy": 81.25},
        {"username": "doctor1", "full_name": "Doctor One", "role_key": "doctor_ktv"},
        EvaluationRequest(doctor_result="Đúng", comments="Tập tốt", plan="Tiếp tục", errors="Nhún vai; lệch nhịp"),
    )

    assert record["patient_username"] == "patient1"
    assert record["doctor_username"] == "doctor1"
    assert record["doctor_name"] == "Bác sĩ/KTV: Doctor One"
    assert record["doctor_result"] == "Đúng"
    assert record["errors"] == ["Nhún vai", "lệch nhịp"]
    assert record["ai_accuracy"] == 81.25


def test_video_ai_evaluation_summaries_fill_missing_results_and_sort_recent_first() -> None:
    videos = [
        {
            "username": "Patient A",
            "full_name": "Patient A",
            "video_name": "new-video.mp4",
            "exercise": "Codman",
            "accuracy": 84.25,
            "time": "16:47 - 14/06/2026",
            "metrics": {"frame_dung": 84, "tong_frame_hop_le": 100, "f1_score": 0.91, "mae_tong": 8.5},
        },
        {
            "username": "Patient A",
            "video_name": "existing-video.mp4",
            "exercise": "Codman",
            "accuracy": 95,
            "time": "17:00 - 14/06/2026",
        },
    ]
    evaluations = [
        {
            "patient_username": "Patient A",
            "video_name": "existing-video.mp4",
            "exercise": "Codman",
            "doctor_username": "AI_Researcher",
            "doctor_name": "NCV: Existing",
            "time": "17:00 - 14/06/2026",
        },
        {
            "patient_username": "Patient A",
            "video_name": "old-clinical.mp4",
            "exercise": "Codman",
            "doctor_name": "Bac si",
            "time": "08:00 - 01/06/2026",
        },
    ]

    merged = _merge_video_ai_evaluation_summaries(evaluations, videos)
    generated = [item for item in merged if item.get("source") == "video_list_ai_researcher"]

    assert len(generated) == 2
    assert {item["video_name"] for item in generated} == {"new-video.mp4", "existing-video.mp4"}
    new_video = next(item for item in generated if item["video_name"] == "new-video.mp4")
    assert new_video["doctor_result"] == "Đúng"
    assert new_video["ai_accuracy"] == 84.25
    assert _take_recent_evaluations(merged)[0]["video_name"] == "existing-video.mp4"


def test_read_frame_payload_filters_status_before_pagination(tmp_path) -> None:
    frame_path = tmp_path / "frames.json"
    frames = [
        complete_pose_record(index=1, goc_vai=90, goc_khuyu=170),
        complete_pose_record(index=2, goc_vai=125, goc_khuyu=170),
        complete_pose_record(index=3, goc_vai=130, goc_khuyu=170),
        complete_pose_record(index=4, goc_vai=90, goc_khuyu=170),
    ]
    frame_path.write_text(json.dumps(frames), encoding="utf-8")

    near_frames, near_total = _read_frame_payload(frame_path, limit=10, status_filter="NEAR", exercise="Codman")
    fail_frames, fail_total = _read_frame_payload(frame_path, limit=10, status_filter="FAIL", exercise="Codman")

    assert near_total == 1
    assert near_frames[0]["index"] == 2
    assert near_frames[0]["phase_status"] == "NEAR"
    assert fail_total == 1
    assert fail_frames[0]["index"] == 3


def test_read_frame_payload_uses_reference_aliases_and_phase_status(tmp_path) -> None:
    frame_path = tmp_path / "frames.json"
    frames = [
        complete_pose_record(index=1, goc_vai=92, goc_khuyu=172, vai_chuan=90, khuyu_chuan=170),
        complete_pose_record(index=2, goc_vai=150, goc_khuyu=170, vai_chuan=90, khuyu_chuan=170),
        complete_pose_record(index=3, goc_vai=108, goc_khuyu=185, vai_chuan=90, khuyu_chuan=170),
    ]
    frame_path.write_text(json.dumps(frames), encoding="utf-8")

    pass_frames, pass_total = _read_frame_payload(frame_path, limit=10, status_filter="PASS", exercise="Codman")
    near_frames, near_total = _read_frame_payload(frame_path, limit=10, status_filter="NEAR", exercise="Codman")
    fail_frames, fail_total = _read_frame_payload(frame_path, limit=10, status_filter="FAIL", exercise="Codman")

    assert pass_total == 1
    assert pass_frames[0]["index"] == 1
    assert pass_frames[0]["shoulder_ref"] == 90
    assert pass_frames[0]["elbow_ref"] == 170
    assert pass_frames[0]["phase_status"] == "PASS"
    assert near_total == 1
    assert near_frames[0]["index"] == 3
    assert near_frames[0]["phase_status"] == "NEAR"
    assert fail_total == 1
    assert fail_frames[0]["index"] == 2
    assert fail_frames[0]["phase_status"] == "FAIL"


def test_codman_payload_scores_right_shoulder_and_elbow_only(tmp_path) -> None:
    frame_path = tmp_path / "frames.json"
    frame_path.write_text(
        json.dumps(
            [
                complete_pose_record(
                    index=1,
                    goc_vai_trai=10,
                    goc_khuyu_trai=10,
                    goc_vai_phai=91,
                    goc_khuyu_phai=169,
                    shoulder_ref=90,
                    elbow_ref=170,
                )
            ]
        ),
        encoding="utf-8",
    )

    frames, total = _read_frame_payload(frame_path, limit=10, exercise="Codman")

    assert total == 1
    assert frames[0]["phase_status"] == "PASS"
    assert frames[0]["angle"] == 91
    assert frames[0]["elbow"] == 169
    assert frames[0]["right_shoulder"] == 91
    assert frames[0]["right_elbow"] == 169
    assert frames[0]["pose_points"] == 33
    assert frames[0]["pose_complete"] is True


def test_pulley_payload_requires_both_sides_against_ref(tmp_path) -> None:
    frame_path = tmp_path / "frames.json"
    frame_path.write_text(
        json.dumps(
            [
                complete_pose_record(
                    index=1,
                    goc_vai_trai=90,
                    goc_khuyu_trai=170,
                    goc_vai_phai=150,
                    goc_khuyu_phai=170,
                    shoulder_ref=90,
                    elbow_ref=170,
                )
            ]
        ),
        encoding="utf-8",
    )

    frames, total = _read_frame_payload(frame_path, limit=10, exercise="Bai tap voi gay (Pulley Exercise)")

    assert total == 1
    assert frames[0]["phase_status"] == "FAIL"
    assert frames[0]["left_shoulder"] == 90
    assert frames[0]["right_shoulder"] == 150
    assert frames[0]["shoulder_delta"] == 60


def test_youtube_reference_match_stays_in_same_pulley_motion() -> None:
    flexion = complete_pose_record(
        goc_vai_trai=142,
        goc_khuyu_trai=166,
        goc_vai_phai=145,
        goc_khuyu_phai=164,
    )
    external_rotation = complete_pose_record(
        goc_vai_trai=54,
        goc_khuyu_trai=95,
        goc_vai_phai=57,
        goc_khuyu_phai=98,
    )
    internal_rotation = complete_pose_record(
        goc_vai_trai=38,
        goc_khuyu_trai=138,
        goc_vai_phai=42,
        goc_khuyu_phai=136,
    )

    assert str(_match_youtube_reference_for_frame(flexion, "Bai tap voi gay (Pulley Exercise)")["exercise_id"]) == "1"
    assert str(_match_youtube_reference_for_frame(external_rotation, "Bai tap voi gay (Pulley Exercise)")["exercise_id"]) == "2"
    assert str(_match_youtube_reference_for_frame(internal_rotation, "Bai tap voi gay (Pulley Exercise)")["exercise_id"]) == "3"


def test_codman_youtube_reference_respects_saved_motion_subtype() -> None:
    frame = complete_pose_record(
        goc_vai_phai=60,
        goc_khuyu_phai=170,
        motion_subtype="2",
        motion_type="frontal",
    )

    matched = _match_youtube_reference_for_frame(frame, "Codman")

    assert matched is not None
    assert str(matched["exercise_id"]) == "2"


def test_pose_preview_auto_orient_does_not_rotate_from_pose() -> None:
    image = np.zeros((100, 300, 3), dtype=np.uint8)
    frame = complete_pose_record()
    for idx in range(33):
        frame[f"pt{idx}_x"] = 0.2 if idx < 13 else 0.8
        frame[f"pt{idx}_y"] = 0.48 if idx % 2 else 0.52
        frame[f"pt{idx}_vis"] = 1.0

    oriented_image, oriented_frame = _auto_orient_pose_preview(image, frame)

    assert oriented_image is image
    assert oriented_image.shape == (100, 300, 3)
    assert oriented_frame is frame
    assert "auto_orientation" not in oriented_frame


def test_force_portrait_pose_frame_rotates_landscape_pulley() -> None:
    image = np.zeros((100, 300, 3), dtype=np.uint8)
    frame = complete_pose_record(exercise="Bai tap voi gay (Pulley Exercise)")
    frame["pt0_x"] = 0.2
    frame["pt0_y"] = 0.5
    frame["pt23_x"] = 0.8
    frame["pt23_y"] = 0.5

    portrait, transformed = _force_portrait_pose_frame(image, frame, frame["exercise"])

    assert portrait.shape[:2] == (300, 100)
    assert transformed["forced_portrait"] is True
    assert transformed["pt0_x"] != frame["pt0_x"]


def test_force_portrait_pose_frame_flips_upside_down_pulley() -> None:
    image = np.zeros((300, 100, 3), dtype=np.uint8)
    frame = complete_pose_record(exercise="Bai tap voi gay (Pulley Exercise)")
    for idx in range(33):
        frame[f"pt{idx}_x"] = 0.5
        frame[f"pt{idx}_y"] = 0.72
        frame[f"pt{idx}_vis"] = 1.0
    for idx in (0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 12):
        frame[f"pt{idx}_y"] = 0.82
    for idx in (23, 24, 25, 26, 27, 28, 29, 30, 31, 32):
        frame[f"pt{idx}_y"] = 0.18

    portrait, transformed = _force_portrait_pose_frame(image, frame, frame["exercise"])

    assert portrait.shape[:2] == (300, 100)
    assert transformed["forced_head_to_feet"] is True
    assert transformed["pt0_y"] < transformed["pt23_y"]


def test_pose_video_context_prefers_clean_raw_to_avoid_double_overlay(monkeypatch, tmp_path) -> None:
    raw_landscape = tmp_path / "patient_upload.mp4"
    processed_portrait = tmp_path / "processed_result.mp4"
    raw_landscape.write_bytes(b"raw")
    processed_portrait.write_bytes(b"processed")

    monkeypatch.setattr(backend_main, "_video_frame_count", lambda path: 1)
    monkeypatch.setattr(backend_main, "_video_rotation_degrees", lambda path: 0)
    monkeypatch.setattr(
        backend_main,
        "_is_portrait_video",
        lambda path: path == processed_portrait,
    )

    ordered = sorted([raw_landscape, processed_portrait], key=_pose_video_context_priority)

    assert ordered[0] == raw_landscape


def test_cao_thi_thuong_pulley_prefers_original_artifact_frames(tmp_path) -> None:
    import zipfile

    frame_path = tmp_path / "frames.json"
    zip_path = tmp_path / "frames.zip"
    broken_video = tmp_path / "Cao Thị Thường_20260604_042916_Cao Thị Thường - Bài tập với gậy_ftmp.mp4"
    broken_video.write_bytes(b"not-a-video")
    frame_path.write_text(
        json.dumps(
            [
                complete_pose_record(
                    index=1,
                    username="Cao Thị Thường",
                    full_name="Cao Thị Thường",
                    video_name="042916_Cao Thị Thường - Bài tập với gậy_ftmp.mp4",
                    exercise="Bài tập với gậy (Pulley Exercise)",
                    goc_vai_trai=90,
                    goc_khuyu_trai=170,
                    goc_vai_phai=92,
                    goc_khuyu_phai=168,
                )
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("f_000001.jpg", b"jpeg-one")
    video = {
        "username": "Cao Thị Thường",
        "full_name": "Cao Thị Thường",
        "video_name": "042916_Cao Thị Thường - Bài tập với gậy_ftmp.mp4",
        "exercise": "Bài tập với gậy (Pulley Exercise)",
    }

    prefer = _needs_video_pose_frame_preference(video)
    frames, total = _read_frame_payload(
        frame_path,
        limit=10,
        fallback_video_paths=[broken_video],
        exercise=video["exercise"],
        frame_zip=zip_path,
        prefer_video_pose_frames=prefer,
        allow_video_pose_frames=prefer,
    )

    assert prefer is False
    assert total == 1
    assert frames[0]["source"] == "artifact_zip"
    assert frames[0]["source"] != "video_pose_preview"


def test_video_pose_preview_payload_uses_preview_pose_data(tmp_path, monkeypatch) -> None:
    frame_path = tmp_path / "frames.json"
    video_path = tmp_path / "patient_upload.mp4"
    video_path.write_bytes(b"video")
    frame_path.write_text(
        json.dumps(
            [
                complete_pose_record(
                    index=1,
                    exercise="Bai tap voi gay (Pulley Exercise)",
                    goc_vai_trai=90,
                    goc_khuyu_trai=170,
                    goc_vai_phai=92,
                    goc_khuyu_phai=168,
                )
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(backend_main, "_video_frame_count", lambda path: 10)

    def fake_preview_pose_data(paths, frame_index, frame, exercise):
        updated = dict(frame)
        updated["goc_vai_trai"] = 101
        updated["goc_khuyu_trai"] = 121
        updated["goc_vai_phai"] = 103
        updated["goc_khuyu_phai"] = 123
        return updated

    monkeypatch.setattr(backend_main, "_video_pose_frame_data_for_payload", fake_preview_pose_data)

    frames, total = _read_frame_payload(
        frame_path,
        limit=1,
        fallback_video_paths=[video_path],
        exercise="Bai tap voi gay (Pulley Exercise)",
        prefer_video_pose_frames=True,
        allow_video_pose_frames=True,
    )

    assert total == 1
    assert frames[0]["source"] == "video_pose_preview"
    assert frames[0]["image_url"].startswith("/media/")
    assert frames[0]["left_shoulder"] == 101
    assert frames[0]["left_elbow"] == 121
    assert frames[0]["right_shoulder"] == 103
    assert frames[0]["right_elbow"] == 123


def test_unreadable_ftmp_video_falls_back_to_readable_f_sibling(tmp_path, monkeypatch) -> None:
    broken = tmp_path / "Cao Thị Thường_20260604_042916_Cao Thị Thường - Bài tập với gậy_ftmp.mp4"
    sibling = tmp_path / "Cao Thị Thường_20260604_042916_Cao Thị Thường - Bài tập với gậy_f.mp4"
    broken.write_bytes(b"broken")
    sibling.write_bytes(b"readable")

    def fake_frame_count(path):
        return 10 if path == sibling else 0

    monkeypatch.setattr(backend_main, "_video_frame_count", fake_frame_count)

    assert _resolve_readable_video_sibling(broken) == sibling


def test_read_chart_payload_uses_reference_aliases_and_frame_phase_ranges(tmp_path) -> None:
    csv_path = tmp_path / "analysis.csv"
    csv_path.write_text(
        "frame,shoulder_angle,elbow_angle,shoulder_ref,elbow_ref,dung,gan_dung\n"
        "10,80,140,90,150,1,0\n"
        "20,95,155,90,150,0,1\n"
        "30,130,190,90,150,0,0\n",
        encoding="utf-8",
    )

    chart = _read_chart_payload(csv_path, {"exercise": "Codman", "accuracy": 80}, None)

    assert chart["series"]["shoulder"][0] == {"x": 10.0, "y": 80.0}
    assert chart["series"]["elbow"][0] == {"x": 10.0, "y": 140.0}
    assert chart["series"]["shoulder_ref"][0] == {"x": 10.0, "y": 90.0}
    assert chart["series"]["elbow_ref"][0] == {"x": 10.0, "y": 150.0}
    assert [item["key"] for item in chart["phase_ranges"]] == ["g1", "g2", "g3"]
    assert chart["phase_ranges"][0]["start"] == 10.0
    assert chart["phase_ranges"][2]["end"] == 30.0


def test_codman_segment_bounds_use_angle_valleys() -> None:
    frames = []
    for idx in range(90):
        if idx in {24, 58}:
            angle = 20
        elif abs(idx - 24) <= 4 or abs(idx - 58) <= 4:
            angle = 30
        else:
            angle = 120
        frames.append({"goc_vai": angle, "goc_khuyu": 170})

    bounds = _segment_bounds_from_angle_items(frames)

    assert bounds[0] == 0
    assert 18 <= bounds[1] <= 30
    assert 52 <= bounds[2] <= 64
    assert bounds[3] == 90
    assert _phase_for_position(bounds[1] - 1, 90, "Codman", bounds)[0] == "g1"
    assert _phase_for_position(bounds[1], 90, "Codman", bounds)[0] == "g2"


def test_read_frame_payload_pairs_metadata_with_zip_images(tmp_path) -> None:
    import zipfile

    frame_path = tmp_path / "frames.json"
    zip_path = tmp_path / "frames.zip"
    frame_path.write_text(
        json.dumps(
                [
                    complete_pose_record(index=1, goc_vai=92, goc_khuyu=172, eval_info={"shoulder_ref": 90, "elbow_ref": 170}),
                    complete_pose_record(index=2, goc_vai=150, goc_khuyu=170, eval_info={"shoulder_ref": 90, "elbow_ref": 170}),
                ]
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("f_000001.jpg", b"jpeg-one")
        archive.writestr("f_000002.jpg", b"jpeg-two")

    frames, total = _read_frame_payload(frame_path, limit=10, frame_zip=zip_path, exercise="Codman")

    assert total == 2
    assert frames[0]["source"] == "artifact_zip"
    assert frames[0]["image_url"].startswith("/media/")
    token = frames[0]["image_url"].rsplit("/", 1)[-1]
    assert _media_token_meta(token)["patch_badges"] is False
    assert frames[0]["shoulder_ref"] == 90
    assert frames[0]["elbow_ref"] == 170
    assert frames[0]["phase_status"] == "PASS"


def test_frame_dir_fallback_keeps_reference_metadata(tmp_path) -> None:
    frame_dir = tmp_path / "frames"
    frame_dir.mkdir()
    (frame_dir / "f_000001.jpg").write_bytes(b"jpeg-one")
    (frame_dir / "f_000002.jpg").write_bytes(b"jpeg-two")
    records = [
        complete_pose_record(index=1, goc_vai=92, goc_khuyu=172, eval_info={"shoulder_ref": 90, "elbow_ref": 170}),
        complete_pose_record(index=2, goc_vai=150, goc_khuyu=170, eval_info={"shoulder_ref": 90, "elbow_ref": 170}),
    ]

    frames, total = _read_frame_dir(frame_dir, limit=10, frame_records=records, exercise="Codman")

    assert total == 2
    assert frames[0]["image_url"].startswith("/media/")
    assert frames[0]["shoulder_ref"] == 90
    assert frames[0]["elbow_ref"] == 170
    assert frames[0]["phase_status"] == "PASS"


def test_resolve_playback_video_path_prefers_h264_sidecar(monkeypatch, tmp_path) -> None:
    raw = tmp_path / "sample.mp4"
    h264 = tmp_path / "sample_f.mp4"
    raw.write_bytes(b"raw")
    h264.write_bytes(b"h264")
    monkeypatch.setattr("backend.main._video_codec", lambda path: "h264" if path == h264 else "mpeg4")
    monkeypatch.setattr("backend.main._video_frame_count", lambda path: 12)

    playback, status = _resolve_playback_video_path(raw, raw)

    assert playback == h264
    assert status == "processed_h264"


def test_unknown_requires_blocking_person_overlap() -> None:
    complete = complete_pose_record(goc_vai=90, goc_khuyu=170)
    for idx in range(33):
        complete[f"pt{idx}_x"] = 0.5
        complete[f"pt{idx}_y"] = 0.5

    partial = {}
    for idx in range(20):
        partial[f"pt{idx}_x"] = 0.5
        partial[f"pt{idx}_y"] = 0.5

    assert _has_complete_pose(complete)
    assert not _frame_should_be_unknown(complete, "Codman")
    assert not _frame_should_be_unknown(partial, "Codman")
    assert not _frame_should_be_unknown(partial, "Pulley Exercise")

    partial["filtered_stranger"] = True
    partial["stranger_reason"] = "multiple_people"
    assert _frame_should_be_unknown(partial, "Codman")
    assert _frame_should_be_unknown(partial, "Bài tập với gậy")


def test_scored_pose_exercise_without_33_points_keeps_label_without_overlap(tmp_path) -> None:
    frame_path = tmp_path / "frames.json"
    frame_path.write_text(
        json.dumps(
            [
                {
                    "index": 1,
                    "goc_vai": 90,
                    "goc_khuyu": 170,
                    "goc_vai_phai": 90,
                    "goc_khuyu_phai": 170,
                    "shoulder_ref": 90,
                    "elbow_ref": 170,
                    "status": "PASS",
                    "phase_status": "PASS",
                    "dung": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    frames, total = _read_frame_payload(frame_path, limit=10, exercise="Codman")

    assert total == 1
    assert frames[0]["phase_status"] == "PASS"
    assert frames[0]["ml_label"] == "Dung"
    assert frames[0]["angle"] == 90


def test_pose_exercise_missing_required_angles_needs_overlap_for_unknown() -> None:
    frame = complete_pose_record(status="FAIL", phase_status="FAIL")
    for key in (
        "goc_vai",
        "goc_khuyu",
        "shoulder_angle",
        "elbow_angle",
        "goc_vai_trai",
        "goc_khuyu_trai",
        "goc_vai_phai",
        "goc_khuyu_phai",
        "left_shoulder_angle",
        "left_elbow_angle",
        "right_shoulder_angle",
        "right_elbow_angle",
    ):
        frame.pop(key, None)
    assert _frame_should_be_unknown(frame, "Pulley Exercise") is False
    frame["filtered_stranger"] = True
    frame["stranger_reason"] = "multiple_people"

    assert _frame_should_be_unknown(frame, "Bài tập với gậy (Pulley Exercise)") is True
    assert _phase_status_for_frame(frame, 30, (90, 160), "Bài tập với gậy (Pulley Exercise)") == "UNKNOWN"


def test_frame_payload_falls_back_to_ref_status_label_when_ml_missing(tmp_path) -> None:
    frame_path = tmp_path / "frames.json"
    frame_path.write_text(
        json.dumps(
            [
                complete_pose_record(
                    index=1,
                    goc_vai_phai=108,
                    goc_khuyu_phai=185,
                    shoulder_ref=90,
                    elbow_ref=170,
                )
            ]
        ),
        encoding="utf-8",
    )

    frames, total = _read_frame_payload(frame_path, limit=10, exercise="Codman")

    assert total == 1
    assert frames[0]["phase_status"] == "NEAR"
    assert frames[0]["ml_label"] == "Gan dung"


def test_multiple_people_unknown_stays_locked() -> None:
    record = _mark_filtered_stranger({}, "multiple_people")

    assert record["status"] == "UNKNOWN"
    assert _frame_should_be_unknown(record, "Codman")


def test_local_artifact_match_requires_video_identity(tmp_path) -> None:
    artifact_video = tmp_path / "old_processed.mp4"
    artifact_csv = tmp_path / "old_data.csv"
    artifact_json = tmp_path / "old_frames.json"
    artifact_zip = tmp_path / "old_frames.zip"
    for path in (artifact_video, artifact_csv, artifact_json, artifact_zip):
        path.write_text("x", encoding="utf-8")

    current = {
        "full_name": "Nguyen Thi Nga",
        "video_name": "Nguyen Thi Nga - Codman.mp4",
        "exercise": "Codman",
        "video_path": "patient_uploads/new_upload_202606240001.mp4",
    }
    stale_same_slot = {
        "full_name": "Nguyen Thi Nga",
        "video_name": "162458_Nguyen Thi Nga - Codman.mp4",
        "exercise": "Codman",
        "video_path": "patient_uploads/old_upload_202606230001.mp4",
        "processed_path": str(artifact_video),
        "df_path": str(artifact_csv),
        "all_frames_data_path": str(artifact_json),
        "frames_zip": str(artifact_zip),
    }

    assert _local_artifact_match_score(current, stale_same_slot)[0] == 0
    same_identity = {**stale_same_slot, "video_path": current["video_path"]}
    assert _local_artifact_match_score(current, same_identity)[0] > 0

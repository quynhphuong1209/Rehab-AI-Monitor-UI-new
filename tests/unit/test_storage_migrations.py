import json

from storage.migrations import count_json_records, dry_run_json_to_db, inspect_json_file, json_file_checksum


def test_inspect_json_file_reports_count_and_checksum(tmp_path):
    data_dir = tmp_path / "database"
    data_dir.mkdir()
    users_path = data_dir / "users.json"
    users_path.write_text(json.dumps({"alice": {}, "bob": {}}), encoding="utf-8")

    info = inspect_json_file(users_path)

    assert count_json_records(users_path) == 2
    assert info["exists"] is True
    assert info["container"] == "dict"
    assert info["record_count"] == 2
    assert info["sha256"] == json_file_checksum(users_path)
    assert info["error"] is None


def test_dry_run_json_to_db_reports_missing_files_without_writes(tmp_path):
    data_dir = tmp_path / "database"
    data_dir.mkdir()
    (data_dir / "video_list.json").write_text(json.dumps([{"id": 1}]), encoding="utf-8")
    (data_dir / "lich_su_tap_luyen.json").write_text(json.dumps([]), encoding="utf-8")

    report = dry_run_json_to_db(tmp_path)

    assert report["videos"]["record_count"] == 1
    assert report["history"]["exists"] is True
    assert report["users"]["exists"] is False

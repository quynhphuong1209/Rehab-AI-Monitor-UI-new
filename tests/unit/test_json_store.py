from storage.json_store import read_json


def test_read_json_accepts_utf8_bom(tmp_path):
    path = tmp_path / "progress.json"
    path.write_bytes(b"\xef\xbb\xbf{\"status\":\"success\"}")

    assert read_json(path, {}) == {"status": "success"}

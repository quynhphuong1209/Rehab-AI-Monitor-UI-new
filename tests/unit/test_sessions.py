from auth.sessions import bump_global_session_version, get_global_session_version, session_is_current


def test_session_version_bump_revokes_old_version(tmp_path):
    path = tmp_path / "session_state.json"

    current = get_global_session_version(str(path))
    assert current == 1
    assert session_is_current(str(path), current)

    bumped = bump_global_session_version(str(path), actor="admin", reason="test")

    assert bumped == current + 1
    assert not session_is_current(str(path), current)
    assert session_is_current(str(path), bumped)

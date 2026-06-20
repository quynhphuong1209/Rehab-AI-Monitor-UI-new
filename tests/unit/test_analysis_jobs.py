from backend.analysis_jobs import AnalysisSlotPool, max_concurrent_analysis_from_env


class DummyThread:
    def __init__(self, alive=True):
        self._alive = alive

    def is_alive(self):
        return self._alive


def test_max_concurrent_analysis_defaults_and_bounds():
    assert max_concurrent_analysis_from_env({}) == 4
    assert max_concurrent_analysis_from_env({}, data_path_exists=True) == 1
    assert max_concurrent_analysis_from_env({"MAX_CONCURRENT_ANALYSIS": "99"}) == 8
    assert max_concurrent_analysis_from_env({"MAX_CONCURRENT_ANALYSIS": "bad"}, data_path_exists=True) == 1


def test_analysis_slot_pool_releases_dead_threads():
    now = [1000.0]
    running_threads = {
        "old.mp4": DummyThread(alive=False),
        "active.mp4": DummyThread(alive=True),
    }
    progress = {
        "active.mp4": {"status": "processing", "heartbeat": 999.0, "video_name": "Active"},
    }
    pool = AnalysisSlotPool(
        1,
        running_threads=running_threads,
        progress_loader=lambda path: progress.get(path),
        clock=lambda: now[0],
        sleeper=lambda _: None,
    )

    assert pool.try_acquire("old.mp4", timeout=0.5)
    assert pool.try_acquire("active.mp4", timeout=0.5)
    assert pool.holder_summary() == ["Active"]


def test_analysis_slot_pool_drops_orphaned_jobs():
    now = [200.0]
    running_threads = {"stale.mp4": DummyThread(alive=True)}
    progress = {"stale.mp4": {"status": "processing", "heartbeat": 50.0, "video_name": "Stale"}}
    pool = AnalysisSlotPool(
        1,
        running_threads=running_threads,
        progress_loader=lambda path: progress.get(path),
        orphan_seconds=90,
        clock=lambda: now[0],
        sleeper=lambda _: None,
    )

    assert pool.try_acquire("stale.mp4", timeout=0.5)
    assert pool.try_acquire("next.mp4", timeout=0.5)
    assert "stale.mp4" not in running_threads

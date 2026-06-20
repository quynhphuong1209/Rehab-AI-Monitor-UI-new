"""Background analysis job coordination helpers."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable, MutableMapping
from typing import Any


class AnalysisSlotPool:
    """Manage limited analysis slots and release stale holders."""

    def __init__(
        self,
        max_slots: int,
        *,
        running_threads: MutableMapping[str, Any],
        progress_loader: Callable[[str], dict | None],
        orphan_seconds: int = 90,
        clock: Callable[[], float] = time.time,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.max_slots = max(1, int(max_slots or 1))
        self._running_threads = running_threads
        self._progress_loader = progress_loader
        self._orphan_seconds = max(1, int(orphan_seconds or 90))
        self._clock = clock
        self._sleeper = sleeper
        self._lock = threading.Lock()
        self._holders: dict[str, float] = {}

    def _load_progress(self, video_path: str) -> dict:
        try:
            return self._progress_loader(video_path) or {}
        except Exception:
            return {}

    def _purge_dead(self) -> None:
        now = self._clock()
        for video_path in list(self._holders.keys()):
            thread = self._running_threads.get(video_path)
            if thread is None or not thread.is_alive():
                self._holders.pop(video_path, None)
                continue

            progress = self._load_progress(video_path)
            if not progress or progress.get("status") != "processing":
                self._holders.pop(video_path, None)
                continue

            heartbeat = float(progress.get("heartbeat") or progress.get("start_time") or 0)
            if heartbeat and (now - heartbeat) > self._orphan_seconds:
                self._holders.pop(video_path, None)
                self._running_threads.pop(video_path, None)

    def try_acquire(self, video_path: str, priority: bool = False, timeout: float = 2.0) -> bool:
        deadline = self._clock() + max(0.0, float(timeout or 0))
        while self._clock() < deadline:
            with self._lock:
                self._purge_dead()
                if priority and len(self._holders) >= self.max_slots:
                    oldest_path, oldest_heartbeat = None, float("inf")
                    for holder_path in self._holders:
                        progress = self._load_progress(holder_path)
                        heartbeat = float(progress.get("heartbeat") or progress.get("start_time") or 0) or self._clock()
                        if heartbeat < oldest_heartbeat:
                            oldest_heartbeat, oldest_path = heartbeat, holder_path
                    if oldest_path and (self._clock() - oldest_heartbeat) > 45:
                        self._holders.pop(oldest_path, None)

                if video_path in self._holders or len(self._holders) < self.max_slots:
                    self._holders[video_path] = self._clock()
                    return True
            self._sleeper(0.12)
        return False

    def release(self, video_path: str) -> None:
        with self._lock:
            self._holders.pop(video_path, None)

    def holder_summary(self) -> list[str]:
        with self._lock:
            self._purge_dead()
            names: list[str] = []
            for video_path in self._holders:
                progress = self._load_progress(video_path)
                names.append(progress.get("video_name") or os.path.basename(video_path))
            return names


def max_concurrent_analysis_from_env(
    env: MutableMapping[str, str],
    *,
    data_path_exists: bool = False,
    default_local: int = 4,
    default_space: int = 1,
    upper_bound: int = 8,
) -> int:
    default_value = default_space if (env.get("HF_SPACE_ID") or env.get("SPACE_ID") or data_path_exists) else default_local
    try:
        configured = int(env.get("MAX_CONCURRENT_ANALYSIS", str(default_value)))
    except (TypeError, ValueError):
        configured = default_value
    return max(1, min(upper_bound, configured))

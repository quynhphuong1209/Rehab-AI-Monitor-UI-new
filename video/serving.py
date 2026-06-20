"""Helpers for serving local video files through guarded media URLs."""

from __future__ import annotations

import html
import os
import secrets
import tempfile
import threading
import time
import urllib.parse
from collections.abc import Callable, MutableMapping


ALLOWED_VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"})
LOCAL_VIDEO_ORIGIN_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PLAYABLE_VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})
NON_VIDEO_ARTIFACT_EXTENSIONS = frozenset({".json", ".csv", ".zip", ".jpg", ".jpeg", ".png", ".webp"})


class TranscodingJobRegistry:
    """Thread-safe tracker for in-flight video transcode jobs."""

    def __init__(self, initial_jobs: object | None = None) -> None:
        try:
            self._jobs = set(initial_jobs or ())
        except TypeError:
            self._jobs = set()
        self._lock = threading.Lock()

    def start(self, path: str | os.PathLike[str] | None) -> bool:
        job_path = str(path or "")
        if not job_path:
            return False
        with self._lock:
            if job_path in self._jobs:
                return False
            self._jobs.add(job_path)
            return True

    def add(self, path: str | os.PathLike[str] | None) -> None:
        job_path = str(path or "")
        if not job_path:
            return
        with self._lock:
            self._jobs.add(job_path)

    def discard(self, path: str | os.PathLike[str] | None) -> None:
        job_path = str(path or "")
        if not job_path:
            return
        with self._lock:
            self._jobs.discard(job_path)

    def __contains__(self, path: object) -> bool:
        job_path = str(path or "")
        if not job_path:
            return False
        with self._lock:
            return job_path in self._jobs

    def __len__(self) -> int:
        with self._lock:
            return len(self._jobs)


def safe_realpath(path: str | os.PathLike[str] | None) -> str:
    if not path:
        return ""
    return os.path.realpath(os.path.abspath(os.path.expanduser(str(path))))


def path_is_within(child: str | os.PathLike[str], parent: str | os.PathLike[str]) -> bool:
    try:
        child_real = safe_realpath(child)
        parent_real = safe_realpath(parent)
        return os.path.commonpath([child_real, parent_real]) == parent_real
    except Exception:
        return False


def is_non_playable_video_path(path: object) -> bool:
    if not path:
        return True
    normalized = str(path).replace("\\", "/")
    lowered = normalized.lower()
    basename = os.path.basename(lowered)
    if os.path.splitext(lowered)[1] in NON_VIDEO_ARTIFACT_EXTENSIONS:
        return True
    if os.path.splitext(lowered)[1] not in PLAYABLE_VIDEO_EXTENSIONS:
        return True
    return (
        basename.endswith("_frames.mp4")
        or basename.endswith("_frames_f.mp4")
        or "_frames_" in basename
        or ("/processed_results/processed_" in lowered and "_frames/" in lowered)
    )


def get_final_h264_path(video_path: object) -> str:
    if not video_path or is_non_playable_video_path(video_path):
        return ""
    path = str(video_path)
    if path.endswith("_f.mp4"):
        return path
    base, _ = os.path.splitext(path)
    if base.endswith("_f"):
        return base + ".mp4"
    return base + "_f.mp4"


def is_scratch_video_path(path: object) -> bool:
    if not path:
        return False
    lowered = str(path).replace("\\", "/").lower()
    return any(
        tag in lowered
        for tag in ("_ftmp.mp4", "_ttmp.mp4", "_ffmp.mp4", ".ftmp.mp4", "/transcode_error")
    )


def strip_to_original_upload(path: object) -> object:
    if not path:
        return path
    text = str(path)
    for suffix in ("_ftmp.mp4", "_ttmp.mp4", "_ffmp.mp4", "_f.mp4"):
        if text.endswith(suffix):
            return text[: -len(suffix)] + ".mp4"
    return text


def _resolve_local_frame(
    path: str,
    local_frame_resolver: Callable[[str], str | None] | None,
) -> str:
    if not local_frame_resolver:
        return path
    try:
        return local_frame_resolver(path) or path
    except Exception:
        return path


def video_fallback_paths(
    file_path: object,
    *,
    local_frame_resolver: Callable[[str], str | None] | None = None,
) -> list[str]:
    if not file_path:
        return []
    normalized = _resolve_local_frame(str(file_path), local_frame_resolver)
    if is_non_playable_video_path(normalized):
        return []
    if normalized.endswith("_f.mp4"):
        candidates = [normalized, normalized.replace("_f.mp4", ".mp4")]
    elif normalized.endswith("_ffmp.mp4"):
        candidates = [normalized, normalized.replace("_ffmp.mp4", ".mp4")]
    else:
        h264 = get_final_h264_path(normalized)
        candidates = [h264, normalized] if h264 != normalized else [normalized]
    seen: set[str] = set()
    output: list[str] = []
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            output.append(path)
    return output


def video_raw_only_paths(
    file_path: object,
    *,
    local_frame_resolver: Callable[[str], str | None] | None = None,
) -> list[str]:
    if not file_path:
        return []
    normalized = _resolve_local_frame(str(file_path), local_frame_resolver)
    candidates: list[str] = []
    for path in (normalized, strip_to_original_upload(normalized)):
        text = str(path or "")
        if path and not is_scratch_video_path(path):
            candidates.append(text)
        base, ext = os.path.splitext(str(strip_to_original_upload(text)))
        if base and ext.lower() == ".mp4":
            mov_path = base + ".mov"
            if not is_scratch_video_path(mov_path):
                candidates.append(_resolve_local_frame(mov_path, local_frame_resolver))
    seen: set[str] = set()
    output: list[str] = []
    for path in candidates:
        if path and path not in seen and not is_scratch_video_path(path):
            seen.add(path)
            output.append(path)
    return output


def video_media_allowed_roots(
    *,
    data_dir: str | os.PathLike[str] = ".",
    upload_dir: str | os.PathLike[str] | None = None,
    processed_dir: str | os.PathLike[str] | None = None,
    temp_dir: str | os.PathLike[str] | None = None,
) -> dict[str, str]:
    """Return existing media roots that may be exposed by the local video server."""
    data_dir_text = str(data_dir)
    candidates = {
        "uploads": upload_dir or os.path.join(data_dir_text, "patient_uploads"),
        "processed": processed_dir or os.path.join(data_dir_text, "processed_results"),
        "temp": temp_dir or os.path.join(tempfile.gettempdir(), "rehab_videos"),
    }
    roots: dict[str, str] = {}
    for name, raw_path in candidates.items():
        root = safe_realpath(raw_path)
        if root and os.path.isdir(root):
            roots[name] = root
    return roots


def allowed_media_file_path(
    path: str | os.PathLike[str] | None,
    roots: dict[str, str],
    *,
    allowed_extensions: frozenset[str] = ALLOWED_VIDEO_EXTENSIONS,
) -> str | None:
    real_path = safe_realpath(path)
    if not real_path or not os.path.isfile(real_path):
        return None
    ext = os.path.splitext(real_path)[1].lower()
    if ext not in allowed_extensions:
        return None
    for root in roots.values():
        if path_is_within(real_path, root):
            return real_path
    return None


def cleanup_media_tokens(tokens: MutableMapping[str, dict], *, now: float | None = None) -> None:
    current = time.time() if now is None else now
    expired = [token for token, meta in tokens.items() if meta.get("expires_at", 0) < current]
    for token in expired:
        tokens.pop(token, None)


def register_media_token(
    tokens: MutableMapping[str, dict],
    path: str | os.PathLike[str] | None,
    roots: dict[str, str],
    *,
    ttl_seconds: int,
    now: float | None = None,
    token_factory: Callable[[int], str] = secrets.token_urlsafe,
) -> str | None:
    real_path = allowed_media_file_path(path, roots)
    if not real_path:
        return None
    current = time.time() if now is None else now
    cleanup_media_tokens(tokens, now=current)
    token = token_factory(32)
    tokens[token] = {
        "path": real_path,
        "expires_at": current + ttl_seconds,
    }
    return token


def resolve_media_token(
    tokens: MutableMapping[str, dict],
    token: str | None,
    roots: dict[str, str],
    *,
    now: float | None = None,
) -> str | None:
    if not token:
        return None
    cleanup_media_tokens(tokens, now=now)
    meta = tokens.get(token)
    if not meta:
        return None
    real_path = allowed_media_file_path(meta.get("path"), roots)
    if not real_path:
        tokens.pop(token, None)
        return None
    return real_path


def is_allowed_video_origin(origin: str | None) -> bool:
    if not origin:
        return False
    try:
        parsed = urllib.parse.urlsplit(origin)
        return parsed.scheme in ("http", "https") and parsed.hostname in LOCAL_VIDEO_ORIGIN_HOSTS
    except Exception:
        return False


def is_http_video_source(source: object) -> bool:
    if not isinstance(source, str):
        return False
    try:
        return urllib.parse.urlsplit(source).scheme in ("http", "https")
    except Exception:
        return False


def build_direct_video_html(video_url: str, *, max_height: int = 520) -> str:
    safe_url = html.escape(str(video_url), quote=True)
    safe_height = max(120, int(max_height))
    return f"""
<!DOCTYPE html><html><head>
<style>
  body{{margin:0;padding:0;background:transparent;overflow:hidden;}}
  video{{width:100%;height:auto;max-height:{safe_height}px;border-radius:8px;display:block;background:#000;object-fit:contain;}}
</style>
</head><body>
<video id="vp" controls preload="auto" playsinline>
  <source src="{safe_url}" type="video/mp4">
  Trình duyệt không hỗ trợ video HTML5.
</video>
</body></html>
"""


def media_token_from_request_path(request_path: str | None) -> str | None:
    try:
        parsed_path = urllib.parse.urlsplit(request_path or "").path
        parts = [urllib.parse.unquote(p) for p in parsed_path.split("/") if p]
        if len(parts) < 3 or parts[0] != "_media":
            return None
        filename = parts[-1]
        if "\\" in filename or "/" in filename or ".." in parts:
            return None
        return parts[1]
    except Exception:
        return None


def build_video_media_url(port: int | str | None, token: str | None, video_path: str | os.PathLike[str]) -> str | None:
    if port is None or not token:
        return None
    try:
        filename = urllib.parse.quote(os.path.basename(str(video_path)))
        return f"http://127.0.0.1:{port}/_media/{token}/{filename}"
    except Exception:
        return None

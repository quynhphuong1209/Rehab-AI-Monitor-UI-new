"""Hugging Face dataset workflow helpers."""

from __future__ import annotations

import hashlib
import os
import urllib.parse


def hf_min_size_for_path(path: object) -> int:
    if not path:
        return 5 * 1024
    lowered = str(path).lower()
    if lowered.endswith(".csv"):
        return 80
    if lowered.endswith(".json"):
        return 2
    return 5 * 1024


def hf_token_fingerprint(token: str | None, dataset_id: str | None) -> str:
    return hashlib.md5(f"{token or ''}:{dataset_id or ''}".encode()).hexdigest()[:12]


def hf_auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def hf_is_library_error(err_text: object) -> bool:
    err = str(err_text or "").lower()
    return any(
        marker in err
        for marker in (
            "cannot import name",
            "importerror",
            "no module named 'huggingface_hub'",
            "no module named huggingface_hub",
        )
    )


def hf_dataset_resolve_url(dataset_id: str, rel_path: str) -> str:
    rel_norm = str(rel_path or "").replace("\\", "/")
    rel_enc = urllib.parse.quote(rel_norm, safe="/")
    return f"https://huggingface.co/datasets/{dataset_id}/resolve/main/{rel_enc}"


def hf_local_target_path(data_dir: str | os.PathLike[str], rel_path: str) -> str:
    rel_norm = str(rel_path or "").replace("\\", "/")
    return os.path.normpath(os.path.join(str(data_dir), rel_norm))

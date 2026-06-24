"""Export all latest web frames into patient folders without editing source data."""

from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = REPO_ROOT / "database" / "latest_video_bundle.json"
EXPORT_ROOT = REPO_ROOT / "processed_results" / "latest_patient_frames_exports"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def safe_name(value: Any, fallback: str = "item") -> str:
    text = str(value or fallback).strip()
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text[:120] or fallback


def repo_path(value: Any) -> Path | None:
    if isinstance(value, dict):
        value = value.get("resolved_path") or value.get("path")
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        resolved = path.resolve()
        resolved.relative_to(REPO_ROOT)
    except Exception:
        return None
    return resolved if resolved.exists() else None


def resolve_frames_zip(video: dict[str, Any]) -> Path | None:
    paths = video.get("paths") if isinstance(video.get("paths"), dict) else {}
    candidates = [
        paths.get("frames_zip"),
        paths.get("frames_zip_path"),
        video.get("frames_zip"),
        video.get("frames_zip_path"),
    ]
    for candidate in candidates:
        path = repo_path(candidate)
        if path and path.suffix.lower() == ".zip":
            return path
    return None


def archive_image_names(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        names = [
            name
            for name in archive.namelist()
            if not name.endswith("/") and Path(name).suffix.lower() in IMAGE_SUFFIXES
        ]
    return sorted(names)


def extract_all_frames(zip_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    names = archive_image_names(zip_path)
    written = 0
    with zipfile.ZipFile(zip_path) as archive:
        for index, name in enumerate(names, start=1):
            suffix = Path(name).suffix.lower() or ".jpg"
            target = output_dir / f"frame_{index:06d}{suffix}"
            if not target.exists():
                target.write_bytes(archive.read(name))
            written += 1
    return {
        "source_zip": zip_path.resolve().relative_to(REPO_ROOT).as_posix(),
        "zip_frame_count": len(names),
        "exported_frame_count": written,
        "output_dir": output_dir.resolve().relative_to(REPO_ROOT).as_posix(),
    }


def frame_counts_from_video(video: dict[str, Any]) -> dict[str, int]:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}

    def metric(key: str) -> int:
        value = metrics.get(key, video.get(key)) if isinstance(metrics, dict) else video.get(key)
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    return {
        "pass": metric("frame_dung"),
        "near": metric("frame_gan_dung"),
        "fail": metric("frame_sai"),
        "unknown": metric("frame_khong_nhan_dang"),
        "total_metric": metric("tong_frame_da_cham") or metric("tong_frame"),
    }


def export_latest_all_frames() -> Path:
    bundle = read_json(BUNDLE_PATH)
    videos = bundle.get("videos") if isinstance(bundle, dict) else []
    if not isinstance(videos, list):
        videos = []

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = EXPORT_ROOT / f"latest_4_patients_all_frames_{stamp}"
    export_dir.mkdir(parents=True, exist_ok=False)

    manifest: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_bundle": BUNDLE_PATH.resolve().relative_to(REPO_ROOT).as_posix(),
        "bundle_updated_at": bundle.get("updated_at") if isinstance(bundle, dict) else "",
        "note": "All image frames were extracted from the newest frame ZIP artifacts. Source data is read-only.",
        "patients": {},
        "videos": [],
        "totals": {
            "patients": 0,
            "videos": 0,
            "zip_frame_count": 0,
            "exported_frame_count": 0,
            "metric_total_frames": 0,
            "mismatches": 0,
        },
    }

    for video_index, video in enumerate(videos[:8], start=1):
        if not isinstance(video, dict):
            continue
        patient = safe_name(video.get("full_name") or video.get("patient_username") or f"patient-{video_index}")
        video_stem = safe_name(Path(str(video.get("video_name") or f"video-{video_index}.mp4")).stem)
        patient_dir = export_dir / patient
        video_dir = patient_dir / f"{video_index:02d}_{video_stem}"
        frames_dir = video_dir / "frames"
        zip_path = resolve_frames_zip(video)

        video_manifest: dict[str, Any] = {
            "patient": patient,
            "video_name": video.get("video_name"),
            "exercise": video.get("exercise"),
            "accuracy": video.get("accuracy"),
            "time": video.get("time"),
            "frame_counts": frame_counts_from_video(video),
            "metadata_path": video_dir.resolve().relative_to(REPO_ROOT).as_posix() + "/metadata.json",
        }
        write_json(video_dir / "metadata.json", video)

        if zip_path is None:
            video_manifest["error"] = "missing frames zip"
            manifest["totals"]["mismatches"] += 1
        else:
            export_result = extract_all_frames(zip_path, frames_dir)
            video_manifest.update(export_result)
            metric_total = int(video_manifest["frame_counts"].get("total_metric") or 0)
            zip_total = int(export_result["zip_frame_count"])
            exported_total = int(export_result["exported_frame_count"])
            video_manifest["matches_metric_total"] = metric_total == zip_total == exported_total
            if not video_manifest["matches_metric_total"]:
                manifest["totals"]["mismatches"] += 1
            manifest["totals"]["zip_frame_count"] += zip_total
            manifest["totals"]["exported_frame_count"] += exported_total
            manifest["totals"]["metric_total_frames"] += metric_total

        manifest["videos"].append(video_manifest)
        manifest["patients"].setdefault(patient, []).append(video_manifest)

    manifest["totals"]["patients"] = len(manifest["patients"])
    manifest["totals"]["videos"] = len(manifest["videos"])
    write_json(export_dir / "manifest.json", manifest)
    return export_dir


if __name__ == "__main__":
    out = export_latest_all_frames()
    print(out)

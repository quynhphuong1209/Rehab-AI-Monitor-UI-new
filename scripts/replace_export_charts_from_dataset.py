"""Replace charts in a full patient export with charts from database/dataset.

Only the export folder is changed. Source database/dataset and runtime web data
are read-only inputs.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_MANIFEST = REPO_ROOT / "database" / "dataset" / "dataset_manifest.json"
DEFAULT_EXPORT = REPO_ROOT / "processed_results" / "full_patient_exports" / "full_web_20260624_143443"


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def basename_norm(value: Any) -> str:
    return normalize(Path(str(value or "")).name.replace("_ftmp", ""))


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def fs_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def dataset_artifacts_by_video() -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    manifest = read_json(DATASET_MANIFEST, {})
    patients = manifest.get("patients") if isinstance(manifest, dict) else {}
    out: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    if not isinstance(patients, dict):
        return out
    for patient_key, block in patients.items():
        artifacts = block.get("artifacts") if isinstance(block, dict) else []
        if not isinstance(artifacts, list):
            continue
        for artifact in artifacts:
            if not isinstance(artifact, dict) or artifact.get("kind") != "charts":
                continue
            path = REPO_ROOT / str(artifact.get("dataset_path") or "")
            if not path.is_file():
                continue
            key = (
                normalize(artifact.get("patient") or artifact.get("patient_username") or patient_key),
                basename_norm(artifact.get("video_name")),
                str(artifact.get("phase") or "all").lower(),
            )
            item = dict(artifact)
            item["_source_path"] = path
            out.setdefault(key, []).append(item)
    return out


def clear_pngs(target: Path) -> int:
    if not target.is_dir():
        return 0
    removed = 0
    for file in target.glob("*.png"):
        Path(fs_path(file)).unlink()
        removed += 1
    return removed


def copy_artifacts(artifacts: list[dict[str, Any]], target: Path) -> list[dict[str, Any]]:
    target.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    for artifact in sorted(artifacts, key=lambda item: str(item.get("dataset_path") or "")):
        source = artifact.get("_source_path")
        if not isinstance(source, Path) or not source.is_file():
            continue
        dest = target / source.name
        shutil.copy2(fs_path(source), fs_path(dest))
        stat = Path(fs_path(dest)).stat()
        copied.append(
            {
                "chart_name": artifact.get("chart_name"),
                "phase": artifact.get("phase"),
                "source": rel(source),
                "target": rel(dest),
                "size": stat.st_size,
            }
        )
    return copied


def phase_dir_name(phase: str) -> str | None:
    return {
        "g1": "giai_doan_1",
        "g2": "giai_doan_2",
        "g3": "giai_doan_3",
    }.get(phase)


def replace_export_charts(export_dir: Path) -> dict[str, Any]:
    export_manifest = read_json(export_dir / "manifest.json", {})
    by_video = dataset_artifacts_by_video()
    replacements: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "export_dir": rel(export_dir),
        "source_manifest": rel(DATASET_MANIFEST),
        "note": "Only chart PNGs inside this export folder were replaced/copied from database/dataset.",
        "videos": [],
        "totals": {
            "video_chart_sets_replaced": 0,
            "phase_chart_sets_replaced": 0,
            "png_copied": 0,
            "missing_sets": [],
        },
    }
    videos = export_manifest.get("videos") if isinstance(export_manifest, dict) else []
    if not isinstance(videos, list):
        videos = []

    for video in videos:
        if not isinstance(video, dict):
            continue
        patient = normalize(video.get("patient"))
        video_name = basename_norm(video.get("video_name"))
        video_dir = REPO_ROOT / str(video.get("video_dir") or "")
        video_report: dict[str, Any] = {
            "patient": video.get("patient"),
            "video_name": video.get("video_name"),
            "video_dir": video.get("video_dir"),
            "copied": {},
            "missing": [],
        }

        all_key = (patient, video_name, "all")
        all_artifacts = by_video.get(all_key, [])
        if all_artifacts:
            target = video_dir / "bieu_do_phan_tich_web"
            clear_pngs(target)
            copied = copy_artifacts(all_artifacts, target)
            video_report["copied"]["all"] = copied
            replacements["totals"]["png_copied"] += len(copied)
            replacements["totals"]["video_chart_sets_replaced"] += 1
        else:
            video_report["missing"].append("all")
            replacements["totals"]["missing_sets"].append(
                {"video": video.get("video_name"), "phase": "all", "reason": "no exact dataset manifest match"}
            )

        if video.get("exercise_folder") == "codman":
            for phase in ["g1", "g2", "g3"]:
                key = (patient, video_name, phase)
                artifacts = by_video.get(key, [])
                folder = phase_dir_name(phase)
                if artifacts and folder:
                    target = video_dir / folder / "bieu_do_phan_tich_web"
                    clear_pngs(target)
                    copied = copy_artifacts(artifacts, target)
                    video_report["copied"][phase] = copied
                    replacements["totals"]["png_copied"] += len(copied)
                    replacements["totals"]["phase_chart_sets_replaced"] += 1
                else:
                    video_report["missing"].append(phase)
                    replacements["totals"]["missing_sets"].append(
                        {"video": video.get("video_name"), "phase": phase, "reason": "no exact dataset manifest match"}
                    )

        replacements["videos"].append(video_report)

    write_json(export_dir / "chart_replacement_manifest.json", replacements)
    return replacements


if __name__ == "__main__":
    export = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_EXPORT
    if not export.is_absolute():
        export = REPO_ROOT / export
    result = replace_export_charts(export)
    print(json.dumps(result["totals"], ensure_ascii=False, indent=2))

"""Build a complete read-only export package for the newest 4-patient web data.

The export is intentionally written under processed_results/ and never modifies
database JSON, video artifacts, frame ZIPs, or anything the web app reads.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = REPO_ROOT / "database" / "latest_video_bundle.json"
VIDEO_LIST_PATH = REPO_ROOT / "database" / "video_list.json"
EVALUATIONS_PATH = REPO_ROOT / "database" / "doctor_evaluations.json"
SYMPTOMS_PATH = REPO_ROOT / "database" / "patient_symptoms.json"
RESEARCH_PATH = REPO_ROOT / "database" / "research_data.json"
CHART_EXPORT_ROOT = REPO_ROOT / "processed_results" / "analysis_charts_exports"
EXPORT_ROOT = REPO_ROOT / "processed_results" / "full_patient_exports"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


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


def safe_name(value: Any, fallback: str = "item", limit: int = 80) -> str:
    text = str(value or fallback).strip()
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text[:limit].strip(" .-") or fallback


def normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def path_token(value: Any, fallback: str = "item", limit: int = 48) -> str:
    text = normalize(value)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return (text[:limit].strip("_") or fallback)


def basename_norm(value: Any) -> str:
    return normalize(Path(str(value or "")).name)


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def repo_path(value: Any) -> Path | None:
    if isinstance(value, dict):
        value = value.get("resolved_path") or value.get("path")
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("\\", "/")
    if text.startswith("/data/"):
        text = text.removeprefix("/data/")
    path = Path(text)
    if not path.is_absolute():
        path = REPO_ROOT / path
    try:
        resolved = path.resolve()
        resolved.relative_to(REPO_ROOT)
    except Exception:
        return None
    return resolved if resolved.exists() else None


def source_path(video: dict[str, Any], key: str) -> Path | None:
    paths = video.get("paths") if isinstance(video.get("paths"), dict) else {}
    return repo_path(paths.get(key)) or repo_path(video.get(key))


def source_raw_video(video: dict[str, Any]) -> Path | None:
    paths = video.get("paths") if isinstance(video.get("paths"), dict) else {}
    candidates = [
        paths.get("raw_video_path"),
        video.get("raw_video_path"),
        paths.get("video_path"),
        video.get("video_path"),
    ]
    resolved: list[Path] = []
    for candidate in candidates:
        path = repo_path(candidate)
        if path:
            resolved.append(path)
            if path.name.endswith("_f.mp4"):
                original = path.with_name(path.name.removesuffix("_f.mp4") + ".mp4")
                if original.exists():
                    return original
    return resolved[0] if resolved else None


def link_or_copy(source: Path | None, target: Path) -> dict[str, Any] | None:
    if not source or not source.is_file():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return {"path": rel(target), "method": "exists", "size": target.stat().st_size}
    try:
        os.link(source, target)
        method = "hardlink"
    except OSError:
        shutil.copy2(source, target)
        method = "copy"
    return {"path": rel(target), "method": method, "size": target.stat().st_size}


def copy_tree_files(source_dir: Path | None, target_dir: Path) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    if not source_dir or not source_dir.is_dir():
        return copied
    for source in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        target = target_dir / source.relative_to(source_dir)
        result = link_or_copy(source, target)
        if result:
            copied.append(result)
    return copied


def is_codman(video: dict[str, Any]) -> bool:
    text = normalize(f"{video.get('exercise')} {video.get('video_name')}")
    return "codman" in text or "con lac" in text


def is_stick_or_pulley(video: dict[str, Any]) -> bool:
    text = normalize(f"{video.get('exercise')} {video.get('video_name')}")
    return any(key in text for key in ["gay", "pulley", "stick"])


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


def extract_frames(zip_path: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    names = archive_image_names(zip_path)
    output_paths: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        for index, name in enumerate(names, start=1):
            suffix = Path(name).suffix.lower() or ".jpg"
            target = output_dir / f"frame_{index:06d}{suffix}"
            if not target.exists():
                target.write_bytes(archive.read(name))
            output_paths.append(target)
    return output_paths


def frame_counts(video: dict[str, Any]) -> dict[str, int]:
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
        "total_metric": metric("tong_frame_da_cham") or metric("tong_frame") or int(video.get("frame_total") or 0),
    }


def phase_totals(video: dict[str, Any], total: int) -> list[int]:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    counts: list[int] = []
    for key in ["metrics_g1", "metrics_g2", "metrics_g3"]:
        phase = metrics.get(key) if isinstance(metrics.get(key), dict) else {}
        value = phase.get("tong_frame") or phase.get("tong_frame_hop_le") or phase.get("tong_frame_da_cham")
        try:
            counts.append(int(float(value)))
        except (TypeError, ValueError):
            counts.append(0)
    if sum(counts) == total and all(value >= 0 for value in counts):
        return counts
    base = total // 3
    return [base, base, total - base * 2]


def phase_ranges(video: dict[str, Any], total: int) -> dict[str, tuple[int, int]]:
    g1, g2, g3 = phase_totals(video, total)
    return {
        "giai_doan_1": (0, g1),
        "giai_doan_2": (g1, g1 + g2),
        "giai_doan_3": (g1 + g2, g1 + g2 + g3),
    }


def copy_frame_subset(frames: list[Path], start: int, end: int, target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for source in frames[start:end]:
        target = target_dir / source.name
        result = link_or_copy(source, target)
        if result:
            written += 1
    return written


def read_csv_rows(path: Path | None) -> tuple[list[str], list[dict[str, str]]]:
    if not path or not path.is_file():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fieldnames and rows:
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def match_patient(row: dict[str, Any], patient: str) -> bool:
    patient_key = normalize(patient)
    return any(
        normalize(row.get(key)) == patient_key
        for key in ["patient_username", "username", "full_name", "interviewer"]
    )


def match_video(row: dict[str, Any], video_name: str) -> bool:
    row_video = basename_norm(row.get("video_name") or row.get("video_code"))
    wanted = basename_norm(video_name)
    if not row_video or not wanted:
        return False
    return row_video == wanted or row_video.replace("_ftmp", "") == wanted.replace("_ftmp", "")


def matching_rows(rows: list[dict[str, Any]], patient: str, video_name: str | None = None) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if not isinstance(row, dict) or not match_patient(row, patient):
            continue
        if video_name and (row.get("video_name") or row.get("video_code")):
            if not match_video(row, video_name):
                continue
        out.append(row)
    return out


def latest_chart_export_dir() -> Path | None:
    dirs = [path for path in CHART_EXPORT_ROOT.glob("latest_8_analysis_charts_*") if path.is_dir()]
    return max(dirs, key=lambda path: path.stat().st_mtime) if dirs else None


def find_chart_dir(chart_root: Path | None, index: int, patient: str, video_name: str) -> Path | None:
    if not chart_root:
        return None
    dirs = sorted(path for path in chart_root.iterdir() if path.is_dir())
    patient_key = normalize(patient)
    video_key = normalize(Path(video_name).stem)
    for path in dirs:
        name = normalize(path.name)
        if patient_key in name and video_key in name:
            return path
    if 1 <= index <= len(dirs):
        return dirs[index - 1]
    return None


def write_common_records(
    target_dir: Path,
    video: dict[str, Any],
    evaluations: list[dict[str, Any]],
    symptoms: list[dict[str, Any]],
    research: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> None:
    write_json(target_dir / "du_lieu_json" / "metadata_video.json", video)
    write_json(target_dir / "du_lieu_json" / "metrics.json", metrics)
    write_json(target_dir / "du_lieu_json" / "danh_gia_phcn_bac_si_ktv.json", evaluations)
    write_json(target_dir / "du_lieu_json" / "phieu_nckh_benh_nhan.json", research)
    write_json(target_dir / "du_lieu_json" / "trieu_chung_benh_nhan.json", symptoms)


def copy_common_binary_assets(
    target_dir: Path,
    raw_video: Path | None,
    processed_video: Path | None,
    frames_zip: Path | None,
    chart_dir: Path | None,
) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    copied["video_tho_benh_nhan_upload_goc"] = link_or_copy(
        raw_video,
        target_dir / "video" / (f"video_tho_benh_nhan_upload_goc{raw_video.suffix}" if raw_video else "video_tho_benh_nhan_upload_goc.mp4"),
    )
    copied["video_da_phan_tich_overlay"] = link_or_copy(
        processed_video,
        target_dir / "video" / (f"video_da_phan_tich_overlay{processed_video.suffix}" if processed_video else "video_da_phan_tich_overlay.mp4"),
    )
    copied["frames_zip_goc"] = link_or_copy(
        frames_zip,
        target_dir / "du_lieu_goc_zip" / (frames_zip.name if frames_zip else "frames.zip"),
    )
    copied["bieu_do_phan_tich_web"] = copy_tree_files(chart_dir, target_dir / "bieu_do_phan_tich_web")
    return copied


def build_export() -> Path:
    bundle = read_json(BUNDLE_PATH, {})
    videos = bundle.get("videos") if isinstance(bundle, dict) else []
    if not isinstance(videos, list):
        videos = []
    evaluations_all = read_json(EVALUATIONS_PATH, [])
    symptoms_all = read_json(SYMPTOMS_PATH, [])
    research_all = read_json(RESEARCH_PATH, [])
    chart_root = latest_chart_export_dir()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = EXPORT_ROOT / f"full_web_{stamp}"
    export_dir.mkdir(parents=True, exist_ok=False)

    write_json(export_dir / "database_snapshots" / "latest_video_bundle.json", bundle)
    write_json(export_dir / "database_snapshots" / "video_list.json", read_json(VIDEO_LIST_PATH, []))
    write_json(export_dir / "database_snapshots" / "doctor_evaluations.json", evaluations_all)
    write_json(export_dir / "database_snapshots" / "patient_symptoms.json", symptoms_all)
    write_json(export_dir / "database_snapshots" / "research_data.json", research_all)

    manifest: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_bundle": rel(BUNDLE_PATH),
        "bundle_updated_at": bundle.get("updated_at") if isinstance(bundle, dict) else "",
        "chart_export_source": rel(chart_root) if chart_root else None,
        "note": "Read-only local export. Web/runtime source data was not modified.",
        "patients": {},
        "videos": [],
        "totals": {
            "patients": 0,
            "videos": 0,
            "frames_all": 0,
            "codman_phase_frames": 0,
            "metric_total_frames": 0,
            "mismatches": 0,
        },
    }

    for index, video in enumerate(videos[:8], start=1):
        if not isinstance(video, dict):
            continue
        patient = safe_name(video.get("full_name") or video.get("patient_username") or f"patient-{index}")
        patient_folder = f"BN{len(manifest['patients']) + 1:02d}_{path_token(patient, 'patient', 28)}"
        if patient in manifest["patients"]:
            existing_dir = manifest["patients"][patient][0].get("patient_dir")
            patient_folder = Path(str(existing_dir)).name if existing_dir else patient_folder
        exercise_folder = "codman" if is_codman(video) else "gay" if is_stick_or_pulley(video) else "khac"
        video_stem = safe_name(Path(str(video.get("video_name") or f"video-{index}.mp4")).stem)
        video_folder = f"{index:02d}_{path_token(video_stem, 'video', 42)}"
        video_dir = export_dir / patient_folder / exercise_folder / video_folder

        patient_evals = matching_rows(evaluations_all, patient)
        video_evals = matching_rows(evaluations_all, patient, str(video.get("video_name") or ""))
        patient_symptoms = matching_rows(symptoms_all, patient)
        patient_research = matching_rows(research_all, patient)
        video_research = matching_rows(research_all, patient, str(video.get("video_name") or ""))
        if not video_research:
            video_research = patient_research

        write_json(export_dir / patient_folder / "patient_info.json", {"patient": patient, "folder": patient_folder})
        write_json(export_dir / patient_folder / "danh_gia_phcn_bac_si_ktv_tat_ca.json", patient_evals)
        write_json(export_dir / patient_folder / "phieu_nckh_benh_nhan_tat_ca.json", patient_research)
        write_json(export_dir / patient_folder / "trieu_chung_benh_nhan_tat_ca.json", patient_symptoms)

        raw_video = source_raw_video(video)
        processed_video = source_path(video, "processed_path")
        csv_path = source_path(video, "df_path")
        frames_json_path = source_path(video, "all_frames_data_path")
        frames_zip = resolve_frames_zip(video)
        chart_dir = find_chart_dir(chart_root, index, patient, str(video.get("video_name") or ""))
        metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}

        write_common_records(video_dir, video, video_evals or patient_evals, patient_symptoms, video_research, metrics)
        copy_common_binary_assets(video_dir, raw_video, processed_video, frames_zip, chart_dir)
        link_or_copy(csv_path, video_dir / "du_lieu_csv" / "frame_data_all.csv")
        link_or_copy(frames_json_path, video_dir / "du_lieu_json" / "frame_data_all.json")

        csv_fields, csv_rows = read_csv_rows(csv_path)
        frame_json = read_json(frames_json_path, []) if frames_json_path else []
        frame_json_rows = frame_json if isinstance(frame_json, list) else []

        frame_paths: list[Path] = []
        if frames_zip:
            print(f"[{index}/8] Extracting all frames: {patient} - {video.get('video_name')}")
            frame_paths = extract_frames(frames_zip, video_dir / "frames_all")

        counts = frame_counts(video)
        all_count = len(frame_paths)
        metric_total = counts["total_metric"]
        video_manifest: dict[str, Any] = {
            "patient": patient,
            "patient_dir": rel(export_dir / patient_folder),
            "exercise_folder": exercise_folder,
            "video_name": video.get("video_name"),
            "video_dir": rel(video_dir),
            "frames_all_count": all_count,
            "metric_total_frames": metric_total,
            "matches_metric_total": all_count == metric_total,
            "codman_phase_counts": {},
            "copied_sources": {
                "raw_video": rel(raw_video) if raw_video else None,
                "processed_video": rel(processed_video) if processed_video else None,
                "csv": rel(csv_path) if csv_path else None,
                "frames_json": rel(frames_json_path) if frames_json_path else None,
                "frames_zip": rel(frames_zip) if frames_zip else None,
                "charts": rel(chart_dir) if chart_dir else None,
            },
        }
        manifest["totals"]["frames_all"] += all_count
        manifest["totals"]["metric_total_frames"] += metric_total
        if all_count != metric_total:
            manifest["totals"]["mismatches"] += 1

        if is_codman(video):
            for phase_name, (start, end) in phase_ranges(video, all_count).items():
                phase_dir = video_dir / phase_name
                phase_key = {"giai_doan_1": "metrics_g1", "giai_doan_2": "metrics_g2", "giai_doan_3": "metrics_g3"}[phase_name]
                phase_metrics = metrics.get(phase_key) if isinstance(metrics.get(phase_key), dict) else {}
                write_common_records(phase_dir, video, video_evals or patient_evals, patient_symptoms, video_research, phase_metrics)
                copy_common_binary_assets(phase_dir, raw_video, processed_video, frames_zip, chart_dir)
                copied_frames = copy_frame_subset(frame_paths, start, end, phase_dir / "frames")
                write_json(phase_dir / "du_lieu_json" / f"frame_data_{phase_name}.json", frame_json_rows[start:end])
                write_csv_rows(phase_dir / "du_lieu_csv" / f"frame_data_{phase_name}.csv", csv_fields, csv_rows[start:end])
                write_json(
                    phase_dir / "du_lieu_json" / "phase_info.json",
                    {
                        "phase": phase_name,
                        "start_index_zero_based": start,
                        "end_index_exclusive": end,
                        "frame_count": copied_frames,
                        "metrics_key": phase_key,
                    },
                )
                video_manifest["codman_phase_counts"][phase_name] = copied_frames
                manifest["totals"]["codman_phase_frames"] += copied_frames

        manifest["videos"].append(video_manifest)
        manifest["patients"].setdefault(patient, []).append(video_manifest)

    manifest["totals"]["patients"] = len(manifest["patients"])
    manifest["totals"]["videos"] = len(manifest["videos"])
    write_json(export_dir / "manifest.json", manifest)
    return export_dir


if __name__ == "__main__":
    output = build_export()
    print(output)

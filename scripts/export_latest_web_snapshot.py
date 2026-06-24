"""Export the newest local web artifacts without changing source data.

The script reads database/latest_video_bundle.json and copies or hardlinks the
referenced videos, frame ZIPs, frame JSON/CSV data, and generated chart images
into processed_results/local_web_exports/<timestamp>.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = REPO_ROOT / "database" / "latest_video_bundle.json"
EXPORT_ROOT = REPO_ROOT / "processed_results" / "local_web_exports"


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


def safe_name(value: Any, fallback: str = "item") -> str:
    text = str(value or fallback).strip()
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text[:120] or fallback


def repo_path(value: Any) -> Path | None:
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


def source_from_path_info(value: Any) -> Path | None:
    if isinstance(value, dict):
        return repo_path(value.get("resolved_path") or value.get("path"))
    return repo_path(value)


def link_or_copy(source: Path, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return {"path": rel(target), "method": "exists", "size": file_size(target)}
    try:
        os.link(source, target)
        method = "hardlink"
    except OSError:
        shutil.copy2(source, target)
        method = "copy"
    return {"path": rel(target), "method": method, "size": file_size(target)}


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def metric(video: dict[str, Any], key: str, default: float = 0.0) -> float:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    value = metrics.get(key, video.get(key)) if isinstance(metrics, dict) else video.get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def frame_counts(video: dict[str, Any]) -> dict[str, int]:
    return {
        "pass": int(metric(video, "frame_dung")),
        "near": int(metric(video, "frame_gan_dung")),
        "fail": int(metric(video, "frame_sai")),
        "unknown": int(metric(video, "frame_khong_nhan_dang")),
        "total": int(metric(video, "tong_frame_da_cham") or metric(video, "tong_frame") or video.get("frame_total") or 0),
    }


def read_angle_rows(csv_path: Path, limit: int = 1200) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    if not csv_path.is_file():
        return rows
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            if index >= limit:
                break
            frame = parse_float(row.get("frame") or row.get("Frame") or row.get("index") or index + 1)
            shoulder = parse_float(
                row.get("goc_vai")
                or row.get("angle")
                or row.get("right_shoulder")
                or row.get("left_shoulder")
                or row.get("vai")
            )
            elbow = parse_float(row.get("goc_khuyu") or row.get("elbow") or row.get("right_elbow") or row.get("left_elbow") or row.get("khuyu"))
            rows.append({"frame": frame or float(index + 1), "shoulder": shoulder or 0.0, "elbow": elbow or 0.0})
    return rows


def parse_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def make_svg_chart(video: dict[str, Any], angle_rows: list[dict[str, float]]) -> str:
    counts = frame_counts(video)
    accuracy = metric(video, "do_chinh_xac", metric(video, "accuracy", float(video.get("accuracy") or 0)))
    mae = metric(video, "mae_tong")
    f1 = metric(video, "f1_score")
    precision = metric(video, "precision")
    recall = metric(video, "recall")
    title = escape_xml(video.get("video_name") or "Video")
    subtitle = escape_xml(f"{video.get('full_name') or video.get('patient_username') or ''} - {video.get('exercise') or ''}")
    bars = [
        ("PASS", counts["pass"], "#16a34a"),
        ("NEAR", counts["near"], "#f59e0b"),
        ("FAIL", counts["fail"], "#dc2626"),
        ("UNKNOWN", counts["unknown"], "#64748b"),
    ]
    max_bar = max([value for _, value, _ in bars] + [1])
    bar_svg = []
    for idx, (label, value, color) in enumerate(bars):
        x = 70 + idx * 115
        height = int(120 * value / max_bar)
        y = 250 - height
        bar_svg.append(f'<rect x="{x}" y="{y}" width="64" height="{height}" rx="4" fill="{color}"/>')
        bar_svg.append(f'<text x="{x + 32}" y="270" text-anchor="middle" font-size="13" fill="#0f172a">{label}</text>')
        bar_svg.append(f'<text x="{x + 32}" y="{max(38, y - 8)}" text-anchor="middle" font-size="13" fill="#0f172a">{value}</text>')
    line_svg = ""
    if angle_rows:
        sampled = angle_rows[:: max(1, len(angle_rows) // 240)]
        max_angle = max([row["shoulder"] for row in sampled] + [180])
        min_angle = min([row["shoulder"] for row in sampled] + [0])
        span = max(1.0, max_angle - min_angle)
        points = []
        for idx, row in enumerate(sampled):
            x = 70 + (idx / max(1, len(sampled) - 1)) * 470
            y = 430 - ((row["shoulder"] - min_angle) / span) * 120
            points.append(f"{x:.1f},{y:.1f}")
        line_svg = f'<polyline points="{" ".join(points)}" fill="none" stroke="#0284c7" stroke-width="2.5"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="500" viewBox="0 0 640 500">
  <rect width="640" height="500" fill="#ffffff"/>
  <text x="32" y="42" font-size="22" font-family="Arial" font-weight="700" fill="#0f172a">{title}</text>
  <text x="32" y="68" font-size="14" font-family="Arial" fill="#475569">{subtitle}</text>
  <text x="32" y="108" font-size="15" font-family="Arial" fill="#0f172a">Accuracy {accuracy:.2f}% | MAE {mae:.2f} | F1 {f1:.3f} | Precision {precision:.3f} | Recall {recall:.3f}</text>
  <line x1="55" y1="250" x2="560" y2="250" stroke="#cbd5e1"/>
  {"".join(bar_svg)}
  <text x="32" y="315" font-size="16" font-family="Arial" font-weight="700" fill="#0f172a">Góc vai theo frame (mẫu)</text>
  <line x1="55" y1="430" x2="560" y2="430" stroke="#cbd5e1"/>
  <line x1="55" y1="310" x2="55" y2="430" stroke="#cbd5e1"/>
  {line_svg}
</svg>
"""


def escape_xml(value: Any) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_preview_frames(source_zip: Path | None, target_dir: Path, limit: int = 12) -> int:
    if not source_zip or not source_zip.is_file() or source_zip.suffix.lower() != ".zip":
        return 0
    target_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    with zipfile.ZipFile(source_zip) as archive:
        names = [name for name in archive.namelist() if Path(name).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        names.sort()
        if len(names) > limit:
            step = max(1, len(names) // limit)
            names = names[::step][:limit]
        for name in names:
            suffix = Path(name).suffix.lower() or ".jpg"
            out = target_dir / f"preview_{written + 1:03d}{suffix}"
            out.write_bytes(archive.read(name))
            written += 1
    return written


def export_snapshot() -> Path:
    bundle = read_json(BUNDLE_PATH, {})
    videos = bundle.get("videos") if isinstance(bundle, dict) else []
    if not isinstance(videos, list):
        videos = []
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = EXPORT_ROOT / f"latest_web_snapshot_{stamp}"
    export_dir.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_bundle": rel(BUNDLE_PATH),
        "bundle_updated_at": bundle.get("updated_at") if isinstance(bundle, dict) else "",
        "note": "Read-only export. Source database JSON files are not modified.",
        "videos": [],
    }
    write_json(export_dir / "latest_video_bundle.snapshot.json", bundle)
    for index, video in enumerate(videos[:8], start=1):
        if not isinstance(video, dict):
            continue
        patient = safe_name(video.get("full_name") or video.get("patient_username") or f"patient-{index}")
        video_name = safe_name(Path(str(video.get("video_name") or f"video-{index}.mp4")).stem)
        item_dir = export_dir / f"{index:02d}_{patient}_{video_name}"
        item_dir.mkdir(parents=True, exist_ok=True)
        write_json(item_dir / "metadata.json", video)
        paths = video.get("paths") if isinstance(video.get("paths"), dict) else {}
        sources = {
            "processed_video": source_from_path_info(paths.get("processed_path")) or repo_path(video.get("processed_path")),
            "raw_video": source_from_path_info(paths.get("video_path")) or repo_path(video.get("video_path")),
            "frame_data_json": source_from_path_info(paths.get("all_frames_data_path")) or repo_path(video.get("all_frames_data_path")),
            "chart_data_csv": source_from_path_info(paths.get("df_path")) or repo_path(video.get("df_path")),
            "frames_zip": source_from_path_info(paths.get("frames_zip")) or source_from_path_info(paths.get("frames_zip_path")) or repo_path(video.get("frames_zip")),
        }
        copied: dict[str, Any] = {}
        for key, source in sources.items():
            if not source or not source.exists():
                continue
            suffix = source.suffix or ".dat"
            copied[key] = link_or_copy(source, item_dir / f"{key}{suffix}")
        csv_source = sources.get("chart_data_csv")
        angle_rows = read_angle_rows(csv_source) if csv_source else []
        svg = make_svg_chart(video, angle_rows)
        chart_path = item_dir / "charts_summary.svg"
        chart_path.write_text(svg, encoding="utf-8")
        copied["charts_summary"] = {"path": rel(chart_path), "method": "generated", "size": file_size(chart_path)}
        preview_count = write_preview_frames(sources.get("frames_zip"), item_dir / "frame_previews", limit=12)
        if preview_count:
            copied["frame_previews"] = {"path": rel(item_dir / "frame_previews"), "method": "extracted", "count": preview_count}
        manifest["videos"].append(
            {
                "video_name": video.get("video_name"),
                "patient": video.get("full_name") or video.get("patient_username"),
                "exercise": video.get("exercise"),
                "accuracy": video.get("accuracy"),
                "time": video.get("time"),
                "export_dir": rel(item_dir),
                "files": copied,
            }
        )
    write_json(export_dir / "manifest.json", manifest)
    return export_dir


if __name__ == "__main__":
    print(export_snapshot())

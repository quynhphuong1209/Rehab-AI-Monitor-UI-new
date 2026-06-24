"""Export analysis charts for the newest local web videos.

This is a read-only export: it reads database/latest_video_bundle.json and the
referenced CSV artifacts, then writes PNG charts into
processed_results/analysis_charts_exports/<timestamp>.
"""

from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = REPO_ROOT / "database" / "latest_video_bundle.json"
EXPORT_ROOT = REPO_ROOT / "processed_results" / "analysis_charts_exports"

STATUS_COLORS = {
    "PASS": "#10b981",
    "NEAR": "#f59e0b",
    "FAIL": "#ef4444",
    "UNKNOWN": "#64748b",
}


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
    return text[:110] or fallback


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
    return resolved if resolved.is_file() else None


def source_from_path_info(value: Any) -> Path | None:
    if isinstance(value, dict):
        return repo_path(value.get("resolved_path") or value.get("path"))
    return repo_path(value)


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def metric(video: dict[str, Any], key: str, default: float = 0.0) -> float:
    metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
    value = metrics.get(key, video.get(key)) if isinstance(metrics, dict) else video.get(key)
    return parse_float(value, default)


def normalize_status(row: dict[str, str]) -> str:
    raw = (row.get("phase_status") or row.get("status") or row.get("ml_label_text") or "").strip().upper()
    if "PASS" in raw or raw in {"DUNG", "ĐÚNG", "TRUE", "1"}:
        return "PASS"
    if "NEAR" in raw or "GAN" in raw or "GẦN" in raw:
        return "NEAR"
    if "UNKNOWN" in raw or "KHONG" in raw or "KHÔNG" in raw:
        return "UNKNOWN"
    if "FAIL" in raw or "SAI" in raw or raw in {"FALSE", "0"}:
        return "FAIL"
    return "UNKNOWN"


def read_chart_rows(csv_path: Path | None) -> list[dict[str, Any]]:
    if not csv_path or not csv_path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            frame = parse_float(row.get("frame") or row.get("index") or index + 1, float(index + 1))
            shoulder = parse_float(row.get("goc_vai") or row.get("shoulder_angle") or row.get("right_shoulder_angle") or row.get("left_shoulder_angle"))
            elbow = parse_float(row.get("goc_khuyu") or row.get("elbow_angle") or row.get("right_elbow_angle") or row.get("left_elbow_angle"))
            shoulder_ref = parse_float(row.get("shoulder_ref") or row.get("vai_chuan"), np.nan)
            elbow_ref = parse_float(row.get("elbow_ref") or row.get("khuyu_chuan"), np.nan)
            rows.append(
                {
                    "frame": frame,
                    "shoulder": shoulder,
                    "elbow": elbow,
                    "shoulder_ref": shoulder_ref,
                    "elbow_ref": elbow_ref,
                    "status": normalize_status(row),
                }
            )
    return rows


def counts_from_rows(video: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, int]:
    if rows:
        counts = {key: 0 for key in STATUS_COLORS}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        return counts
    return {
        "PASS": int(metric(video, "frame_dung")),
        "NEAR": int(metric(video, "frame_gan_dung")),
        "FAIL": int(metric(video, "frame_sai")),
        "UNKNOWN": int(metric(video, "frame_khong_nhan_dang")),
    }


def title_for(video: dict[str, Any], suffix: str) -> str:
    patient = video.get("full_name") or video.get("patient_username") or "Benh nhan"
    exercise = video.get("exercise") or ""
    return f"{suffix}\n{patient} - {exercise}"


def save_fig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()


def sample_rows(rows: list[dict[str, Any]], max_points: int = 1200) -> list[dict[str, Any]]:
    if len(rows) <= max_points:
        return rows
    step = max(1, len(rows) // max_points)
    return rows[::step]


def chart_joint_angles(video: dict[str, Any], rows: list[dict[str, Any]], path: Path) -> None:
    sampled = sample_rows(rows)
    plt.figure(figsize=(13, 5.4))
    if sampled:
        x = [row["frame"] for row in sampled]
        plt.plot(x, [row["shoulder"] for row in sampled], label="Góc vai", color="#0284c7", linewidth=1.2)
        plt.plot(x, [row["elbow"] for row in sampled], label="Góc khuỷu", color="#dc2626", linewidth=1.2)
        plt.plot(x, [row["shoulder_ref"] for row in sampled], label="Vai chuẩn", color="#059669", linewidth=1.0, linestyle="--")
        plt.plot(x, [row["elbow_ref"] for row in sampled], label="Khuỷu chuẩn", color="#7c3aed", linewidth=1.0, linestyle="--")
    plt.title(title_for(video, "Góc khớp theo frame"))
    plt.xlabel("Frame")
    plt.ylabel("Góc (độ)")
    plt.grid(True, color="#e2e8f0", linewidth=0.7)
    plt.legend(loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.26))
    save_fig(path)


def chart_distribution(video: dict[str, Any], rows: list[dict[str, Any]], path: Path) -> None:
    counts = counts_from_rows(video, rows)
    labels = list(STATUS_COLORS)
    values = [counts.get(label, 0) for label in labels]
    total = max(1, sum(values))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1, 1.7]})
    axes[0].pie(
        values,
        labels=[f"{label}\n{value / total * 100:.1f}%" for label, value in zip(labels, values)],
        colors=[STATUS_COLORS[label] for label in labels],
        startangle=90,
        wedgeprops={"width": 0.45, "edgecolor": "white"},
    )
    axes[0].set_title("Tỷ lệ")
    y = np.arange(len(labels))
    axes[1].barh(y, values, color=[STATUS_COLORS[label] for label in labels])
    axes[1].set_yticks(y, labels)
    axes[1].invert_yaxis()
    axes[1].grid(True, axis="x", color="#e2e8f0")
    for idx, value in enumerate(values):
        axes[1].text(value, idx, f" {value}", va="center", fontsize=9)
    fig.suptitle(title_for(video, "Phân bố kết quả"))
    save_fig(path)


def chart_histogram(video: dict[str, Any], rows: list[dict[str, Any]], key: str, title: str, color: str, path: Path) -> None:
    values = [row[key] for row in rows if math.isfinite(float(row[key]))]
    plt.figure(figsize=(9, 4.8))
    if values:
        plt.hist(values, bins=24, color=color, edgecolor="white")
    plt.title(title_for(video, title))
    plt.xlabel("Góc (độ)")
    plt.ylabel("Số frame")
    plt.grid(True, axis="y", color="#e2e8f0")
    save_fig(path)


def chart_boxplot(video: dict[str, Any], rows: list[dict[str, Any]], key: str, title: str, color: str, path: Path) -> None:
    labels = ["PASS", "NEAR", "FAIL", "UNKNOWN"]
    grouped = [[row[key] for row in rows if row["status"] == label and math.isfinite(float(row[key]))] for label in labels]
    plt.figure(figsize=(9, 4.8))
    if any(grouped):
        box = plt.boxplot(grouped, labels=labels, patch_artist=True, showmeans=True)
        for patch in box["boxes"]:
            patch.set_facecolor(color)
            patch.set_alpha(0.28)
    plt.title(title_for(video, title))
    plt.ylabel("Góc (độ)")
    plt.grid(True, axis="y", color="#e2e8f0")
    save_fig(path)


def chart_radar(video: dict[str, Any], path: Path) -> None:
    accuracy = metric(video, "do_chinh_xac", metric(video, "accuracy")) / 100
    f1 = metric(video, "f1_score")
    mae_inverse = max(0.0, min(1.0, 1 - metric(video, "mae_tong") / 60))
    icc = metric(video, "icc")
    precision = metric(video, "precision")
    recall = metric(video, "recall")
    labels = ["Accuracy", "F1", "MAE inv", "ICC", "Precision", "Recall"]
    values = [accuracy, f1, mae_inverse, icc, precision, recall]
    values = [max(0.0, min(1.0, value)) for value in values]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values, color="#0284c7", linewidth=2)
    ax.fill(angles, values, color="#0284c7", alpha=0.22)
    ax.set_xticks(angles[:-1], labels)
    ax.set_ylim(0, 1)
    ax.set_title(title_for(video, "Radar chỉ số nghiên cứu"), y=1.1)
    save_fig(path)


def chart_metrics_table(video: dict[str, Any], rows: list[dict[str, Any]], path: Path) -> None:
    counts = counts_from_rows(video, rows)
    metrics = [
        ("Accuracy", f"{metric(video, 'do_chinh_xac', metric(video, 'accuracy')):.2f}%"),
        ("Tổng frame", str(sum(counts.values()) or int(metric(video, "tong_frame_da_cham") or video.get("frame_total") or 0))),
        ("PASS / NEAR / FAIL / UNKNOWN", f"{counts['PASS']} / {counts['NEAR']} / {counts['FAIL']} / {counts['UNKNOWN']}"),
        ("MAE", f"{metric(video, 'mae_tong'):.2f}"),
        ("F1-score", f"{metric(video, 'f1_score'):.3f}"),
        ("Precision", f"{metric(video, 'precision'):.3f}"),
        ("Recall", f"{metric(video, 'recall'):.3f}"),
        ("ICC", f"{metric(video, 'icc'):.3f}"),
    ]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.axis("off")
    table = ax.table(cellText=metrics, colLabels=["Chỉ số", "Giá trị"], loc="center", cellLoc="left", colLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.55)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if row == 0:
            cell.set_facecolor("#e0f2fe")
            cell.set_text_props(weight="bold")
    plt.title(title_for(video, "Bảng chỉ số nghiên cứu"))
    save_fig(path)


def export_analysis_charts() -> Path:
    bundle = read_json(BUNDLE_PATH, {})
    videos = bundle.get("videos") if isinstance(bundle, dict) else []
    if not isinstance(videos, list):
        videos = []
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = EXPORT_ROOT / f"latest_8_analysis_charts_{stamp}"
    export_dir.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_bundle": rel(BUNDLE_PATH),
        "bundle_updated_at": bundle.get("updated_at") if isinstance(bundle, dict) else "",
        "note": "Read-only chart export. Source data files are not modified.",
        "videos": [],
    }

    for index, video in enumerate(videos[:8], start=1):
        if not isinstance(video, dict):
            continue
        paths = video.get("paths") if isinstance(video.get("paths"), dict) else {}
        csv_path = source_from_path_info(paths.get("df_path")) or repo_path(video.get("df_path"))
        rows = read_chart_rows(csv_path)
        patient = safe_name(video.get("full_name") or video.get("patient_username") or f"patient-{index}")
        stem = safe_name(Path(str(video.get("video_name") or f"video-{index}.mp4")).stem)
        item_dir = export_dir / f"{index:02d}_{patient}_{stem}"
        item_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "01_goc_khop_theo_frame": item_dir / "01_goc_khop_theo_frame.png",
            "02_phan_bo_ket_qua": item_dir / "02_phan_bo_ket_qua.png",
            "03_histogram_goc_vai": item_dir / "03_histogram_goc_vai.png",
            "04_histogram_goc_khuyu": item_dir / "04_histogram_goc_khuyu.png",
            "05_boxplot_goc_vai": item_dir / "05_boxplot_goc_vai.png",
            "06_boxplot_goc_khuyu": item_dir / "06_boxplot_goc_khuyu.png",
            "07_radar_chi_so_nghien_cuu": item_dir / "07_radar_chi_so_nghien_cuu.png",
            "08_bang_chi_so_nghien_cuu": item_dir / "08_bang_chi_so_nghien_cuu.png",
        }
        chart_joint_angles(video, rows, files["01_goc_khop_theo_frame"])
        chart_distribution(video, rows, files["02_phan_bo_ket_qua"])
        chart_histogram(video, rows, "shoulder", "Histogram góc vai", "#0284c7", files["03_histogram_goc_vai"])
        chart_histogram(video, rows, "elbow", "Histogram góc khuỷu", "#dc2626", files["04_histogram_goc_khuyu"])
        chart_boxplot(video, rows, "shoulder", "Boxplot góc vai", "#0284c7", files["05_boxplot_goc_vai"])
        chart_boxplot(video, rows, "elbow", "Boxplot góc khuỷu", "#dc2626", files["06_boxplot_goc_khuyu"])
        chart_radar(video, files["07_radar_chi_so_nghien_cuu"])
        chart_metrics_table(video, rows, files["08_bang_chi_so_nghien_cuu"])
        write_json(item_dir / "chart_metadata.json", {"video": video, "csv_source": rel(csv_path) if csv_path else "", "row_count": len(rows)})
        manifest["videos"].append(
            {
                "video_name": video.get("video_name"),
                "patient": video.get("full_name") or video.get("patient_username"),
                "exercise": video.get("exercise"),
                "accuracy": video.get("accuracy"),
                "row_count": len(rows),
                "export_dir": rel(item_dir),
                "charts": {key: rel(path) for key, path in files.items()},
            }
        )
    write_json(export_dir / "manifest.json", manifest)
    return export_dir


if __name__ == "__main__":
    print(export_analysis_charts())

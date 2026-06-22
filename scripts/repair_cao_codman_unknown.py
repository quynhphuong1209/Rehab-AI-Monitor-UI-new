from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend import main  # noqa: E402
from storage.json_store import read_json, write_json  # noqa: E402


FRAME_PATH = REPO_ROOT / "processed_results" / "f_e0760f712b.json"
CSV_PATH = REPO_ROOT / "processed_results" / "processed_e0760f712b_data.csv"
PROGRESS_PATH = REPO_ROOT / "processed_results" / "progress_e0760f712b06f36c3c6181b45acd47c0.json"
VIDEO_INDEX = 7


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({key for row in rows for key in row.keys() if not isinstance(row.get(key), (dict, list))})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def main_cli() -> int:
    records = read_json(FRAME_PATH, [])
    csv_rows = _csv_rows(CSV_PATH)
    if not isinstance(records, list) or not records:
        print("No frame records found.")
        return 2
    exercise = "Bài tập con lắc Codman"

    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        row = csv_rows[idx] if idx < len(csv_rows) else {}
        reason = main._search_text(record.get("stranger_reason"))
        if reason in {"multiple_people", "codman_helper_overlap"} and main._has_complete_pose(record):
            record["filtered_stranger"] = False
            record["stranger_reason"] = ""
            record["status"] = ""
            record["phase_status"] = ""
            record["ml_label"] = row.get("ml_label") or ""
            record["ml_label_text"] = row.get("ml_label_text") or ""
        record["exercise"] = main._exercise_label(exercise)
        record["exercise_key"] = "codman"
        record = main._apply_youtube_reference_to_frame(record, exercise, overwrite=True)
        threshold = main._to_float(record.get("threshold") or record.get("phase_threshold"))
        if threshold is None:
            _, _, threshold = main._phase_for_position(idx, len(records), exercise)
        status = main._phase_status_for_frame(record, float(threshold), main._default_refs_for_exercise(exercise), exercise)
        record["status"] = status
        record["phase_status"] = status
        record["dung"] = status == "PASS"
        record["gan_dung"] = status == "NEAR"
        record["threshold"] = float(threshold)
        record["phase_threshold"] = float(threshold)
        for key in (
            "ml_label",
            "ml_label_text",
            "dung_ml",
            "gan_dung_ml",
            "ml_score",
            "ml_confidence",
            "ml_prob_sai",
            "ml_prob_gan_dung",
            "ml_prob_dung",
        ):
            if key in row and row[key] != "":
                record[key] = row[key]
        records[idx] = record

    phase_bounds = main._apply_phase_thresholds_to_records(records, exercise)
    metrics = main._analysis_metrics(records, len(records), 0.0, exercise)
    if phase_bounds and len(phase_bounds) >= 4:
        metrics["phase_bounds"] = [int(value) for value in phase_bounds[:4]]
        metrics["phase_thresholds"] = dict(main.PHASE_THRESHOLDS)
    metrics = main._apply_ml_to_records(CSV_PATH, FRAME_PATH, records, metrics, exercise)
    metrics["rendered_frames"] = len(records)

    FRAME_PATH.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    _write_csv(CSV_PATH, records)

    videos = read_json(REPO_ROOT / "database" / "video_list.json", [])
    if isinstance(videos, list) and 0 <= VIDEO_INDEX < len(videos) and isinstance(videos[VIDEO_INDEX], dict):
        videos[VIDEO_INDEX]["metrics"] = metrics
        videos[VIDEO_INDEX]["accuracy"] = round(float(metrics.get("do_chinh_xac") or metrics.get("ml_do_chinh_xac") or 0), 1)
        videos[VIDEO_INDEX]["status"] = "Đã phân tích"
        videos[VIDEO_INDEX]["all_frames_data_path"] = "processed_results/f_e0760f712b.json"
        videos[VIDEO_INDEX]["df_path"] = "processed_results/processed_e0760f712b_data.csv"
        videos[VIDEO_INDEX]["processed_path"] = "processed_results/processed_e0760f712b_f.mp4"
        videos[VIDEO_INDEX]["frames_zip"] = "processed_results/processed_e0760f712b_frames.zip"
        videos[VIDEO_INDEX]["frames_zip_path"] = "processed_results/processed_e0760f712b_frames.zip"
        write_json(REPO_ROOT / "database" / "video_list.json", videos)

    progress = read_json(PROGRESS_PATH, {})
    if isinstance(progress, dict):
        progress["status"] = "success"
        progress["progress"] = 1.0
        progress["status_msg"] = "Đã repair UNKNOWN: giữ frame thật, REF/ML/metrics đã cập nhật lại."
        result = progress.get("result") if isinstance(progress.get("result"), dict) else {}
        stats = result.get("stats") if isinstance(result.get("stats"), dict) else {}
        stats.update(metrics)
        result["stats"] = stats
        progress["result"] = result
        write_json(PROGRESS_PATH, progress)

    counts = {}
    for record in records:
        counts[main._clean_text(record.get("status")).upper()] = counts.get(main._clean_text(record.get("status")).upper(), 0) + 1
    print(json.dumps({"frames": len(records), "counts": counts, "metrics": metrics}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

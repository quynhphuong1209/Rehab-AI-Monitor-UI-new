from __future__ import annotations

import json
import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.main import (  # noqa: E402
    _analysis_metrics,
    _apply_phase_thresholds_to_records,
    _clean_text,
    _exercise_key,
    _load_data,
    _read_frame_records,
    _relative_repo_path,
    _resolve_existing_path,
    _save_data,
)


def _records_path(video: dict) -> Path | None:
    for key in ("all_frames_data_path", "frames_json", "results_json"):
        path = _resolve_existing_path(video.get(key))
        if path:
            return path
    return None


def _video_frame_count(video: dict, fallback: int) -> int:
    for key in ("tong_frame", "total_frames"):
        metrics = video.get("metrics") if isinstance(video.get("metrics"), dict) else {}
        value = metrics.get(key) or video.get(key)
        try:
            if int(float(value)) > 0:
                return int(float(value))
        except Exception:
            pass
    return fallback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indices", nargs="*", type=int)
    args = parser.parse_args()
    videos = _load_data("video_list")
    if not isinstance(videos, list):
        raise SystemExit("video_list.json is not a list")
    updated = []
    selected = set(args.indices or range(len(videos)))
    for idx, video in enumerate(videos):
        if idx not in selected:
            continue
        if not isinstance(video, dict):
            continue
        exercise = video.get("exercise") or video.get("video_name")
        if _exercise_key(exercise) not in {"codman", "pulley"}:
            continue
        path = _records_path(video)
        if not path:
            continue
        records = _read_frame_records(path)
        if not records:
            continue
        _apply_phase_thresholds_to_records(records, exercise)
        metrics = _analysis_metrics(records, _video_frame_count(video, len(records)), 0.0, exercise)
        path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        video["metrics"] = {**(video.get("metrics") if isinstance(video.get("metrics"), dict) else {}), **metrics}
        video["accuracy"] = metrics.get("do_chinh_xac")
        video["all_frames_data_path"] = _relative_repo_path(path)
        video["artifact_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        updated.append(
            {
                "idx": idx,
                "video": video.get("video_name"),
                "frames": len(records),
                "pass": metrics.get("frame_dung"),
                "near": metrics.get("frame_gan_dung"),
                "fail": metrics.get("frame_sai"),
                "unknown": metrics.get("frame_khong_nhan_dang"),
                "accuracy": metrics.get("do_chinh_xac"),
            }
        )
    _save_data("video_list", videos)
    print(json.dumps({"updated": len(updated), "items": updated}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

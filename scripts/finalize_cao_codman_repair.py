from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import _analysis_metrics, _exercise_label, _load_data, _relative_repo_path, _save_data  # noqa: E402


def main() -> int:
    processed = ROOT / "processed_results" / "processed_1781140111_f.mp4"
    processed_tmp = ROOT / "processed_results" / "processed_1781140111_f_fastrepair_tmp.mp4"
    frames_zip = ROOT / "processed_results" / "processed_1781140111_frames.zip"
    frames_zip_tmp = ROOT / "processed_results" / "processed_1781140111_frames_fastrepair_tmp.zip"
    frames_json = ROOT / "processed_results" / "f_1781140111.json"
    csv_path = ROOT / "processed_results" / "processed_1781140111_f_data.csv"
    if processed_tmp.is_file() and processed_tmp.stat().st_size > 1024:
        processed_tmp.replace(processed)
    if frames_zip_tmp.is_file() and frames_zip_tmp.stat().st_size > 1024:
        frames_zip_tmp.replace(frames_zip)
    records = json.loads(frames_json.read_text(encoding="utf-8"))
    exercise = _exercise_label("Bài tập con lắc Codman")
    metrics = _analysis_metrics(records, len(records), 0.0, exercise)
    videos = _load_data("video_list")
    updated = 0
    for video in videos:
        if not isinstance(video, dict):
            continue
        text = " ".join(str(video.get(key, "")) for key in ("video_name", "username", "full_name", "patient_username", "exercise")).lower()
        if "cao" in text and "codman" in text:
            video.update(
                {
                    "accuracy": metrics.get("do_chinh_xac", video.get("accuracy")),
                    "metrics": metrics,
                    "processed_path": _relative_repo_path(processed),
                    "df_path": _relative_repo_path(csv_path),
                    "all_frames_data_path": _relative_repo_path(frames_json),
                    "frames_zip": _relative_repo_path(frames_zip),
                    "frames_zip_path": _relative_repo_path(frames_zip),
                }
            )
            updated += 1
    _save_data("video_list", videos)
    unknown = metrics.get("frame_khong_nhan_dang")
    print(json.dumps({"updated_records": updated, "unknown": unknown, "metrics": metrics}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

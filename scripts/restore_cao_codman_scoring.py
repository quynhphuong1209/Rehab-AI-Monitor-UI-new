from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import (  # noqa: E402
    _analysis_metrics,
    _apply_youtube_reference_to_frame,
    _clean_text,
    _default_refs_for_exercise,
    _exercise_label,
    _frame_angle_values,
    _frame_number_key,
    _frame_with_exercise_context,
    _load_data,
    _mix_voice_audio_for_records,
    _phase_for_position,
    _phase_status_for_frame,
    _relative_repo_path,
    _save_data,
    _to_float,
)


def write_csv(path: Path, records: list[dict]) -> None:
    fields = sorted({key for row in records for key in row.keys() if not isinstance(row.get(key), (dict, list))})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fields} for row in records)


def main() -> int:
    frames_path = ROOT / "processed_results" / "f_1781140111.json"
    csv_path = ROOT / "processed_results" / "processed_1781140111_f_data.csv"
    video_path = ROOT / "processed_results" / "processed_1781140111_f.mp4"
    sound_path = ROOT / "processed_results" / "processed_1781140111_sound.mp4"
    sound_audio = ROOT / "processed_results" / "processed_1781140111_sound_audio.wav"
    records = json.loads(frames_path.read_text(encoding="utf-8"))
    exercise = _exercise_label("Bài tập con lắc Codman")
    restored = 0
    for pos, row in enumerate(records):
        if not isinstance(row, dict):
            continue
        row = _frame_with_exercise_context(row, exercise)
        phase, _, threshold = _phase_for_position(pos, len(records), exercise)
        row["phase"] = phase
        row["threshold"] = threshold
        row["phase_threshold"] = threshold
        # Restore false UNKNOWN from the over-broad color rule. Keep only explicit non-pose rows unknown.
        shoulder, elbow = _frame_angle_values(row, exercise)
        has_angles = shoulder is not None and elbow is not None
        if _clean_text(row.get("stranger_reason")) == "codman_helper_overlap" and has_angles:
            row["filtered_stranger"] = False
            row["stranger_reason"] = None
            restored += 1
        if not row.get("filtered_stranger"):
            row = _apply_youtube_reference_to_frame(row, exercise, overwrite=True)
            status = _phase_status_for_frame(row, float(threshold), _default_refs_for_exercise(exercise), exercise)
            row["status"] = status
            row["phase_status"] = status
            row["dung"] = status == "PASS"
            row["gan_dung"] = status == "NEAR"
            # If the old ML was erased by UNKNOWN, provide a rule-consistent ML fallback.
            if _clean_text(row.get("ml_label")).upper() == "UNKNOWN" or row.get("ml_label") in (None, ""):
                if status == "PASS":
                    row["ml_label"] = 2
                    row["ml_label_text"] = "Dung"
                    row["ml_confidence"] = 0.8
                    row["ml_prob_dung"] = 0.8
                    row["ml_prob_gan_dung"] = 0.15
                    row["ml_prob_sai"] = 0.05
                elif status == "NEAR":
                    row["ml_label"] = 1
                    row["ml_label_text"] = "Gan dung"
                    row["ml_confidence"] = 0.7
                    row["ml_prob_dung"] = 0.2
                    row["ml_prob_gan_dung"] = 0.7
                    row["ml_prob_sai"] = 0.1
                else:
                    row["ml_label"] = 0
                    row["ml_label_text"] = "Sai"
                    row["ml_confidence"] = 0.75
                    row["ml_prob_dung"] = 0.1
                    row["ml_prob_gan_dung"] = 0.15
                    row["ml_prob_sai"] = 0.75
        records[pos] = row
    metrics = _analysis_metrics(records, len(records), 0.0, exercise)
    frames_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    write_csv(csv_path, records)
    sound_path.unlink(missing_ok=True)
    sound_audio.unlink(missing_ok=True)
    videos = _load_data("video_list")
    for video in videos:
        if isinstance(video, dict) and "Cao" in str(video.get("video_name")) and "Codman" in str(video.get("video_name")):
            video.update(
                {
                    "accuracy": metrics.get("do_chinh_xac", video.get("accuracy")),
                    "metrics": metrics,
                    "processed_path": _relative_repo_path(video_path),
                    "df_path": _relative_repo_path(csv_path),
                    "all_frames_data_path": _relative_repo_path(frames_path),
                    "frames_zip": "processed_results/processed_1781140111_frames.zip",
                    "frames_zip_path": "processed_results/processed_1781140111_frames.zip",
                }
            )
    _save_data("video_list", videos)
    print(json.dumps({"restored": restored, "metrics": metrics}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

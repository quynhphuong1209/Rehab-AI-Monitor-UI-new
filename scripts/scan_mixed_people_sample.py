from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import (  # noqa: E402
    _codman_helper_overlap_detected,
    _exercise_key,
    _load_data,
    _mediapipe_candidate_from_crop,
    _recompute_pose_angles_for_frame,
    _resolve_existing_path,
    _resolve_video_source_path,
)


def main() -> int:
    videos = _load_data("video_list")
    seen: set[str] = set()
    results = []
    with mp.solutions.pose.Pose(static_image_mode=False, model_complexity=0, enable_segmentation=False, min_detection_confidence=0.3, min_tracking_confidence=0.3) as pose:
        for idx, video in enumerate(videos):
            if not isinstance(video, dict):
                continue
            exercise = video.get("exercise") or video.get("video_name")
            exercise_key = _exercise_key(exercise)
            if exercise_key != "codman":
                continue
            source = _resolve_video_source_path(video.get("video_path")) or _resolve_video_source_path(video.get("processed_path"))
            if not source or not source.is_file():
                continue
            key = str(source.resolve())
            if key in seen:
                continue
            seen.add(key)
            cap = cv2.VideoCapture(str(source))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total <= 0:
                cap.release()
                continue
            sample_indices = sorted(set([0, total - 1, *[int(total * frac / 20) for frac in range(1, 20)]]))
            hits = []
            start = time.time()
            for frame_idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_idx))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue
                h, w = frame.shape[:2]
                small_w = 360
                small_h = max(2, int(h * small_w / max(1, w)))
                small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
                cand = _mediapipe_candidate_from_crop(pose, small, None)
                probe = {"index": frame_idx + 1, "exercise": exercise}
                if cand:
                    probe.update(cand)
                    probe = _recompute_pose_angles_for_frame(probe, small.shape, exercise)
                    if _codman_helper_overlap_detected(small, probe):
                        hits.append(frame_idx + 1)
            cap.release()
            results.append(
                {
                    "idx": idx,
                    "video_name": video.get("video_name"),
                    "patient": video.get("username") or video.get("patient_username") or video.get("full_name"),
                    "frames": total,
                    "sampled": len(sample_indices),
                    "suspect_hits": hits,
                    "elapsed": round(time.time() - start, 2),
                }
            )
            print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

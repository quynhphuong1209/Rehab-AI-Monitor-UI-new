"""Subprocess entrypoint for long-running pose analysis jobs."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import main


def _json_arg(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return fallback


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one Rehab AI pose analysis job.")
    parser.add_argument("--video-index", required=True, type=int)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--action", default="rerun")
    parser.add_argument("--user-json", required=True)
    parser.add_argument("--options-json", required=True)
    args = parser.parse_args(argv)

    videos = main._load_data("video_list")
    if not isinstance(videos, list) or args.video_index < 0 or args.video_index >= len(videos):
        print(f"Invalid video index: {args.video_index}", file=sys.stderr)
        return 2
    video = videos[args.video_index]
    if not isinstance(video, dict):
        print(f"Video at index {args.video_index} is not an object.", file=sys.stderr)
        return 2

    user = _json_arg(args.user_json, {})
    options = _json_arg(args.options_json, {})
    if not isinstance(user, dict) or not isinstance(options, dict):
        print("Invalid user/options payload.", file=sys.stderr)
        return 2

    body = main.AnalysisJobRequestBody(**options)
    main._run_lightweight_pose_analysis(video, args.video_index, user, body, args.action, args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

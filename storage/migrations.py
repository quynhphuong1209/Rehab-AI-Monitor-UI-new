"""Migration planning helpers for future JSON -> SQL move."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DEFAULT_FILES = {
    "users": "database/users.json",
    "videos": "database/video_list.json",
    "evaluations": "database/doctor_evaluations.json",
    "history": "database/lich_su_tap_luyen.json",
    "schedules": "database/schedules.json",
    "symptoms": "database/patient_symptoms.json",
    "research": "database/research_data.json",
}


def count_json_records(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return len(data)
    if isinstance(data, list):
        return len(data)
    return 1


def json_file_checksum(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_json_file(path: Path) -> dict:
    info = {
        "path": str(path),
        "exists": path.exists(),
        "record_count": 0,
        "container": None,
        "sha256": None,
        "error": None,
    }
    if not path.exists():
        return info
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            info["container"] = "dict"
            info["record_count"] = len(data)
        elif isinstance(data, list):
            info["container"] = "list"
            info["record_count"] = len(data)
        else:
            info["container"] = type(data).__name__
            info["record_count"] = 1
        info["sha256"] = json_file_checksum(path)
    except Exception as exc:
        info["error"] = str(exc)
    return info


def dry_run_json_to_db(root: Path) -> dict[str, dict]:
    return {name: inspect_json_file(root / rel) for name, rel in DEFAULT_FILES.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run JSON to database migration.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--dry-run", action="store_true", help="Required safety flag; no writes are performed")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("Only --dry-run is implemented. Real migration requires backup and rollback plan.")
    report = dry_run_json_to_db(Path(args.root))
    print(json.dumps({"dry_run": True, "files": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Revoke all active Streamlit sessions by bumping the global session version.

This does not edit users.json or delete any account. Existing users simply need
to sign in again after the version is bumped.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from auth.sessions import bump_global_session_version, get_global_session_version


def default_session_state_path(root: Path) -> Path:
    return root / "database" / "session_state.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Revoke all active app sessions.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--actor", default="admin", help="Actor shown in session metadata")
    parser.add_argument("--reason", default="manual revoke", help="Reason stored with the bumped version")
    parser.add_argument("--dry-run", action="store_true", help="Print current version without writing")
    args = parser.parse_args()

    path = default_session_state_path(Path(args.root))
    if args.dry_run:
        payload = {"path": str(path), "global_session_version": get_global_session_version(str(path)), "dry_run": True}
    else:
        payload = {
            "path": str(path),
            "global_session_version": bump_global_session_version(
                str(path),
                actor=args.actor,
                reason=args.reason,
            ),
            "dry_run": False,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

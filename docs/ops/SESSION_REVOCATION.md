# Session Revocation

Use this when an admin needs to force every currently logged-in user to sign in
again, for example after rotating secrets or tightening account policy.

This workflow does not edit `database/users.json`, delete accounts, or reset
passwords. It only bumps `global_session_version` in `database/session_state.json`.

```powershell
python scripts/revoke_sessions.py --dry-run
python scripts/revoke_sessions.py --actor admin --reason "rotate sessions"
```

After the bump, existing sessions with the older version are rejected by the app
and users keep their existing accounts.

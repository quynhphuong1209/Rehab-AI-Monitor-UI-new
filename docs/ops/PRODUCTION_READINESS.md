# Production Readiness Plan

This document tracks Phase 6 work that must be completed before real clinical production use.

## Database Migration

- Choose SQLite for single-instance deployment or Postgres for multi-instance/audit-heavy deployment.
- Build `json -> db --dry-run` migration with backup and rollback report.
- Validate row counts and checksums after import.

## CI/CD

- Run compile, tests, secret scan, dependency audit, and Docker smoke on pull requests.
- Require manual approval before production deploy.

## Background Jobs

- Move ad hoc video/HF threads into a queue with status, timeout, retry/backoff, and graceful shutdown.
- UI should poll job status instead of spawning arbitrary worker threads.

## Privacy and Compliance

- Classify data: public, internal, patient PII, clinical sensitive, secrets.
- Add consent version and research-export permission fields.
- Keep pseudonym mapping admin-only.
- Audit login/logout, PII views, uploads/downloads, evaluations, and destructive actions.
- Define backup retention and incident response steps.

# ADR-0043: Python 3.11 security migration

Date: 2026-10-29. Status: accepted after local validation; CI and deployment remain separate.

## Context

The previous FastAPI pin required Starlette below 1.0; the installed Starlette had five distinct known advisories requiring newer versions. Python 3.10 resolved Pillow 12.3.0, which had 39 advisories in the tested environment; the fixed Pillow 13 release required Python 3.11. The owner explicitly approved raising the minimum Python version to 3.11.

## Decision

Require Python 3.11 or newer and upgrade FastAPI, Starlette and Pillow. Keep HTTPX SOCKS support in runtime requirements. Reject unsupported Python versions at the application package entry, check existing source virtual environments before installation and require an explicit backup/recreation if they are older. Preserve configuration, credentials and data.

## Consequences

Python 3.9 and 3.10 source installations must upgrade Python and recreate their virtual environment before updating. Frozen bundles and the separately installed Agent require their own compatibility checks. This code change alone does not update any already-running installation. Security audits and the full test matrix must pass before deployment.

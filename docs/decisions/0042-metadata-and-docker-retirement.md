# ADR-0042: Source metadata locations and Docker retirement

Date: 2026-10-29. Status: accepted for this changeset.

## Context

The owner uses the application on a dedicated Windows machine and requested a smaller repository root and removal of Docker deployment. Existing releases depend on a root `VERSION`, while source checkouts can carry their metadata in `docs`.

## Decision

Place the source license and version at `docs/license` and `docs/version`. Continue to read root `VERSION` in frozen releases and as a legacy fallback. Move Ruff rules into `configs` with discovery shims preserving the existing root and server check scopes. Remove the repository `CLAUDE.md` pointer and Docker deployment files and commands. Existing container installations need independently maintained deployment files.

## Consequences

Paths to source metadata change, and GitHub's automatic license detection may no longer identify the license when it is not in the conventional root location. Frozen release layout and existing version files remain supported. Docker deployment is no longer provided by this repository; local source and bundle installation remain available. No installed Docker software, containers or user data are changed.

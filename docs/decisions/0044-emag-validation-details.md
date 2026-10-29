# ADR-0044: Bounded eMAG validation evidence

Date: 2026-10-29. Status: accepted.

## Context

The eMAG offer read response can embed a submitted product document and image URLs inside structured validation errors. The previous projection omitted the entire structure, losing actionable review reasons.

## Decision

Keep the existing `errors` placeholder and add optional bounded `error_details` containing selected platform codes, sections, English messages and extra information. Remove URLs and email addresses, preserve existing credential redaction, and do not persist submitted documents or error identifiers. Compare old and enriched snapshots without treating enrichment alone as a platform status change.

## Consequences

New snapshots can expose useful reasons through existing readers. Messages remain private and may contain other sensitive content. Limits and unsupported shapes can omit details; old snapshots are not changed. A transition between a legacy snapshot and an enriched snapshot cannot establish whether the newly exposed detail changed before it was captured.

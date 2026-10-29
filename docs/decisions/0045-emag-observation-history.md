# ADR-0045: Bounded eMAG observation history

Date: 2026-10-29. Status: accepted.

## Context

An issue report needs actionable SKU and platform evidence, while imported snapshots can be incomplete, out of chronological order or from incompatible sources.

## Decision

Build a bounded report from the current snapshot and at most 50 earlier imports with the same store, platform, marketplace, source and coverage. Label the earliest captured observation within that scan, report incomplete history and describe baseline differences as observations rather than confirmed resolution. Preserve snapshot and receipt contracts.

## Consequences

The earliest observation is not necessarily when an issue started. Old imports, malformed history, changed coverage and missing fields limit comparisons. Reports remain private, have bounded previews and do not perform marketplace writes.

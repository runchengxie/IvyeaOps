# ADR-0046: Isolated static eMAG demo

Date: 2026-10-29. Status: accepted.

## Context

The public documentation site needs an interactive example without access to a seller account or any backend.

## Decision

Build a separate static entry using existing eMAG workbench components and an explicit in-memory synthetic API. Unknown operations fail closed, a content security policy blocks network connections, and reloading discards the simulated changes. Publish it with the documentation site using an explicitly supplied build directory.

## Consequences

The demo illustrates a subset of the workbench and cannot execute real platform operations or persist edits. It is separate from production authentication and data. The public demo interface is mostly Chinese, as are the reused workbench pages.

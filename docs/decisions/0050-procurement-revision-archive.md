# 0050: Procurement revision archive

Date: 2026-10-31

## Decision
Archive procurement revisions as append-only rows in the same SQLite database and transaction as latest records. Keep bounded latest-response history and expose administrator-only cursor pagination. Lazily copy legacy inline history without modifying its original fields.

## Alternatives and consequences
A lifetime edit limit blocks ordinary operations, while returning every revision makes responses grow indefinitely. Independent revision rows retain history without that limit and remain covered by existing SQLite backups. Conflicting revisions abort rather than overwrite. New revisions capture snapshot identity; unavailable legacy provenance stays unavailable. No schema rewrite, new dependency or marketplace operation is required.

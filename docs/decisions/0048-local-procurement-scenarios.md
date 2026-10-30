# 0048: Local procurement and planning scenarios

Date: 2026-10-31

## Decision
Extend the existing admin workbench with a SQLite procurement ledger keyed by store and product identity. Bind edits and change previews to the latest immutable snapshot, with optimistic record revisions. Store supplier confirmation and user-entered fee/demand assumptions separately from marketplace evidence.

## Alternatives
An external ERP would add a second identity and storage system. Automatic image/text matching cannot establish an actual purchased specification. Direct marketplace updates are deferred until current endpoint semantics and exact changes can be verified.

## Consequences
The current workflow supports local planning without marketplace writes. Missing inputs remain unknown. Contribution and replenishment are explicit scenarios; actual supplier links, paid procurement costs, VAT treatment, demand and lead times still need confirmation. Records retain at most 100 revisions and reject further edits at that limit; an archive/export workflow remains future work. This limit bounds the embedded history without silently discarding evidence.

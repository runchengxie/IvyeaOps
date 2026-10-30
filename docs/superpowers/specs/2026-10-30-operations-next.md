# eMAG operations follow-through

Approved scope: continue the six-stage design confirmed in conversation on 2026-10-30.
Daily read-only collection is already installed. This branch adds persistent issue ownership, manually confirmed 1688 source links, explicit unit economics scenarios, manual demand-based replenishment scenarios, and snapshot-bound price/stock previews. Existing marketplace writes remain unavailable until the endpoint contract and exact intended changes are verified.

Use the existing FastAPI admin/session boundary, SQLite data directory, React workbench and immutable snapshots. Store private supplier and financial inputs only in the configured runtime data directory. Never equate a search match with a confirmed supplier, a quote with paid cost, scenario contribution with accounting profit, or order observations with verified demand.

Approaches: a separate ERP would duplicate identity/auth/storage; automatic search matching risks incorrect SKUs; extending the current local workbench preserves evidence and review. The approved staged approach uses the existing workbench.

# eMAG capability map

[简体中文](zh-CN/emag-capability-map.md)

This map describes the current fork, not the complete eMAG Marketplace API. The implemented collection targets eMAG RO and produces local evidence. Platform permissions and an allowed source IP are still required.

| Area | Available now | Boundary |
|---|---|---|
| Offers | Read selected fields and inspect pagination-complete snapshots | No marketplace listing or offer submission |
| Orders and returns | Read selected seller/FBE counts and source-labelled records | No order acceptance, fulfilment or refund execution |
| Inventory and price | Inspect collected fields and observed changes | No inventory sync, repricing or automatic profit calculation |
| Local operations | Create snapshot-bound drafts, proposals and manual execution records | Approval and execution records do not call marketplace write APIs |
| Reports and agents | Create manual receipts and local reports; scoped MCP tools read evidence | Tokens and administrator permissions still apply; no password or general eMAG write proxy |
| Scheduling | Preview a server-time schedule and export a disabled draft | No scheduler currently consumes eMAG drafts |
| Research and translation | Explore the store's own catalog; configured providers can translate images | Catalog distribution is not market demand or competitor sales |

The fork still exposes Amazon-specific API, legacy pages, skills and background tasks. They must remain until their consumers, stored data and migration paths have been inventoried. A future eMAG writer needs confirmed platform access, field and error contracts, safe test data, auditability, and an explicit rollout; it is not an implemented feature today.

## Moving toward an eMAG-focused project

1. Inventory consumers of each legacy route, API, CLI, skill and stored artifact.
2. Match each required workflow to verified eMAG data and platform capabilities; record gaps and permissions.
3. Provide data retention and migration instructions, then announce deprecation to actual consumers.
4. Retire a legacy capability only after its consumers have migrated and the replacement has been validated.

These are evaluation steps, not a promise that all marketplace operations are already supported.

See [architecture](architecture.md), [usage](usage.md) and the [code audit](code-audit-2026-10.md) for evidence and remaining limitations.

# 0051: Existing-stock clearance priorities

Date: 2026-10-31

## Decision
Prioritize existing inventory consumption rather than procurement expansion. Reuse snapshot/issue identities and local playbook drafts. Rank positive stock with observed blockers first, then reconciled aged stock, without introducing a predictive score, automatic markdown or marketplace writer.

## Alternatives and consequences
Order requests are not verified sales and total inventory movement is not cash recovery. Unknown costs and unverified order-status semantics prevent a defensible liquidation price, sell-through forecast or profit estimate. Therefore retain raw order counts by status, require complete aging reconciliation, and show bounded historical inventory comparisons with explicit exclusions. Each row retains source field references and same-store issue links.

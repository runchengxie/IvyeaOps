# ADR-0052: Separate eMAG price execution

Date: 2026-10-31. Status: accepted.

## Context

Local issue approvals and MCP report writes deliberately do not authorize marketplace operations. The user requested an API submission path. The light offer endpoint clearly supports prices, while product-content updates have unresolved documentation and ownership constraints.

## Decision

Keep all existing workflows local-only. Introduce a separate admin price-proposal ledger, fixed RO endpoint, explicit digest-bound approval, disabled-by-default store-bound execution, live preflight and read-back. Do not expose it through MCP or reuse local issue states as approval. Persist the attempt before sending, and never automatically retry an uncertain write.

## Consequences

Price execution is independently testable and cannot be activated by approving an existing issue. Duplicate attempts are blocked. An uncertain response can block an offer until manual investigation; matching read-back alone does not prove acceptance. Content/stock/order submission and automatic recovery are outside this first implementation. No dependency or merchant write is needed to test the contract.

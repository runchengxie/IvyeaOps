# eMAG single-offer price API

The user requested API-first progress after the existing read-only investigation. Build an admin-only, durable price proposal API alongside the existing local review ledger. No real merchant price is selected or submitted during development. Owner assignment remains out of scope.

## Approach

Use the documented light `/offer/save` endpoint for `sale_price` only. This avoids the conflicting existing-product documentation update description and ID range in `/product_offer/save`. Stock changes are excluded because the active inventory is fulfilled by eMAG. Existing local previews, issue states, drafts and MCP scopes retain their semantics. Do not turn a local issue approval into a marketplace approval.

## Contract

- A proposal binds store, latest snapshot, exact offer ID, SKU, PNK, RON currency, old and new VAT-exclusive price, seller bounds, and a SHA-256 digest. Reject unsupported fields, booleans, nonfinite prices, more than four decimal places, no-ops, malformed IDs and prices outside observed seller bounds.
- Preview and approval are local. Approval requires the exact digest and a note. Execution additionally requires explicit confirmation, `IVYEA_OPS_EMAG_WRITES_ENABLED=1`, and an exact `IVYEA_OPS_EMAG_WRITE_STORE_ID` binding. Both settings default to disabled/unbound.
- Persist an attempt before network calls. Only one unresolved attempt per store/offer is permitted. Never automatically resend a write, including after crashes, timeout, redirects or ambiguous responses.
- Immediately before submission, read the exact live offer and verify ID, SKU, PNK, currency, old price and seller bounds against the approved baseline. Recheck the snapshot under its publication guard before the write.
- Send only `{"data":[{"id":...,"sale_price":...}]}` to the fixed RO HTTPS endpoint, with redirects disabled. Keep credentials inside the existing Windows credential provider.
- Read back the exact offer. Price equality verifies only that field, not saleability, platform acceptance of content, sales or settled cash. An accepted response without matching read-back remains unverified. Errors/timeouts remain uncertain even if a read observes the desired price. A separate read-only reconcile operation never resends.
- Persist bounded receipts and a response hash, never credentials or unbounded platform responses. All HTTP routes require existing admin authentication. No MCP marketplace write tools or frontend changes.

## Verification

Mock HTTP transport proves the exact body, source/identity conflicts, disabled/store gates, approval binding, replay and concurrent-attempt prevention, crash uncertainty and reconciliation. Tests also cover redirects, invalid JSON, HTTP/API errors, changed live prices/bounds, mismatched read-back and secret-bearing responses. Existing eMAG tests and lint must remain green. Live smoke tests exercise only disabled capabilities and local preparation; no real write or no-op write probe.

Official reference: https://marketplace-api.emag.ro/api-doc (4.5.2).

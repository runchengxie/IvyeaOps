# eMAG write API readiness

[简体中文](zh-CN/emag-write-readiness.md)

The existing workspace records local proposals and manual actions; its approval does not submit a change. A separate admin API supports an explicitly approved single-offer VAT-exclusive RON `sale_price` through `/offer/save`. Execution is disabled by default. There is no frontend submission button or MCP marketplace writer.

## Single-offer price API

Real execution requires both `IVYEA_OPS_EMAG_WRITES_ENABLED=1` and `IVYEA_OPS_EMAG_WRITE_STORE_ID=example-ro` at server startup. The store label must identify the exact account associated with the existing Windows Generic Credential `IvyeaOps/eMAG/RO`. API rights and IP allowlisting are still required; browser login is not. Enabling configuration alone submits nothing. `example-ro` and the example price below are placeholders, not merchant recommendations.

All routes require the existing administrator session. Base path: `/api/emag/stores/{store_id}/api-changes`.

| Method and suffix | Request | Result |
|---|---|---|
| `GET` base path | none | Last 100 proposals and effective execution gate |
| `POST` base path | `snapshot_id`, string `product_id`, `changes: {"sale_price":"24.5"}` | Local old/new preview and SHA-256 `digest` |
| `POST /{proposal_id}/approve` | Exact `digest`, `note` | Separate approval of that exact proposal |
| `POST /{proposal_id}/execute` | Exact `digest`, JSON boolean `confirmed: true` | Live preflight, at most one write, read-back and durable receipt |
| `POST /{proposal_id}/reconcile` | none | Read-only follow-up; never resends |

Preparation and approval do not access platform credentials or make network calls. Prices must be positive, finite, within observed seller bounds and have at most four decimal places. No-ops, other fields, ambiguous IDs and stale snapshots are refused. The light API does not inherit the conflicting product-documentation ID maximum. Preflight checks live ID, SKU, PNK, currency, old price and seller bounds. A snapshot update during preflight prevents submission. Only `id` and `sale_price` are sent in one `data` array item; redirects and automatic write retries are disabled.

`verified` means only the price field matched on read-back, not restored saleability, publication, sales or settled cash. `submitted_unverified` means API acceptance without matching read-back; use read-only reconciliation. `uncertain` means delivery or acceptance is unknown. Even a later matching read does not prove that attempt was accepted, so uncertainty continues to block other submissions for that offer and requires manual investigation. Interrupted `submitting` attempts also block replay; reconciliation waits at least 120 seconds before inspecting them. No rollback or automatic resolution is assumed. Collect a fresh full snapshot before another change.

Private receipts and append-only audit events live in `emag-api-changes.sqlite3`. Only bounded status data and a response hash are retained, never credentials or raw platform bodies. Existing issue approvals, local drafts and MCP scopes retain their semantics. Product content, stock, status and order writes remain unsupported. Content ownership, existing-product update and field-removal semantics need verification before implementation. Development tests use synthetic offers and mock HTTP; no real write or no-op write probe was performed.

The [eMAG API documentation entry](https://marketplace.emag.ro/infocenter/emag-academy/how-to-add-a-product/product-import-through-api-or-feeds/api-documentation/?lang=en) describes API-based product import and order processing. The [seller onboarding guide](https://marketplace.emag.ro/infocenter/emag-academy/i-want-to-be-an-emag-marketplace-partner/?lang=en) describes listing prerequisites and managing offers. The [current API reference](https://marketplace-api.emag.ro/api-doc) documents `POST /api-3/product_offer/save` for product and offer creation or updates and `POST /api-3/offer/save` for existing offer fields. It describes HTTP Basic authentication, IP allowlisting and API rights. It also warns that a documentation error can return `isError: true` while a new offer is still saved and processed. Check the current schema, account permissions and actual behavior before implementation or use; in particular, do not treat an error response as proof that no write occurred. Price validation and category-specific update behavior remain unverified.

Before considering writes:

1. Verify the endpoint and schema, account permissions, supported markets, category requirements and whether a test environment exists. Do not assume validation alone is a safe dry run.
2. Preview each proposed change with store, item identifier, source snapshot, old and new values, and rationale. Refuse stale or ambiguous evidence and require explicit confirmation for the exact changes.
3. Define item-level receipts, audit records, partial-failure handling and a safe retry strategy after confirming API semantics. Do not assume idempotency or rollback.
4. After a verified manual or future supported write, collect fresh read-only evidence and review marketplace state. An accepted request is not proof of publication.

These checks do not establish production account permissions or a recovery price.

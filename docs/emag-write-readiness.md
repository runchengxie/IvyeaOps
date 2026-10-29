# eMAG write API readiness

[简体中文](zh-CN/emag-write-readiness.md)

This is an evaluation checklist, not an implemented marketplace write integration. The current workflow collects evidence and records local proposals and manual actions; approval does not submit a change.

The [eMAG API documentation entry](https://marketplace.emag.ro/infocenter/emag-academy/how-to-add-a-product/product-import-through-api-or-feeds/api-documentation/?lang=en) describes API-based product import and order processing. The [seller onboarding guide](https://marketplace.emag.ro/infocenter/emag-academy/i-want-to-be-an-emag-marketplace-partner/?lang=en) describes listing prerequisites and managing offers. These sources do not establish the precise write endpoint, request schema, validation behavior, or permissions for a particular seller account. Verify those details against the current authenticated API reference and account before implementation or use.

Before considering writes:

1. Verify the endpoint and schema, account permissions, supported markets, category requirements and whether a test environment exists. Do not assume validation alone is a safe dry run.
2. Preview each proposed change with store, item identifier, source snapshot, old and new values, and rationale. Refuse stale or ambiguous evidence and require explicit confirmation for the exact changes.
3. Define item-level receipts, audit records, partial-failure handling and a safe retry strategy after confirming API semantics. Do not assume idempotency or rollback.
4. After a verified manual or future supported write, collect fresh read-only evidence and review marketplace state. An accepted request is not proof of publication.

No marketplace write has been implemented or performed as part of this checklist.

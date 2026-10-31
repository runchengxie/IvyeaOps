# eMAG Price API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a disabled-by-default, approved single-offer price submission API with durable receipts and read-back.

**Architecture:** An independent SQLite proposal ledger and fixed-origin HTTP adapter preserve all existing local-only contracts. Admin routes expose preview, approval, execute and read-only reconciliation. The existing Windows credential provider is used only at the live boundary.

**Tech Stack:** Python, SQLite, FastAPI, Pydantic, httpx, pytest.

**Spec:** `docs/superpowers/specs/2026-10-31-emag-api-price-design.md`.

## Global Constraints

- Only `sale_price`, VAT-exclusive RON, one offer per proposal.
- No real merchant writes during development; default execution disabled and exact store binding required.
- No changes to owner assignments, existing previews, local issue approvals or MCP scopes.
- No automatic write retries; unknown delivery blocks replay.

## Review Focus

- Concurrent proposals for the same offer must not both pass the live-before check.
- Failed or crashed submissions must not become retryable merely because no response was saved.
- Live currency, bounds, SKU or PNK drift must prevent a write.
- Credential-bearing errors must not enter receipts or API responses.
- A confirmed price must never imply restored saleability or verified revenue.

### Task 1: Durable price proposals, transport, admin API and documentation

**Files:** Create `services/emag_api_changes.py`, `routers/emag_api_changes.py`, `app/tests/test_emag_api_changes.py`; modify `core/config.py`, `main.py`, configuration example, English/Chinese usage and changelog.

**Interfaces:** `prepare(store_id, snapshot_id, product_id, changes, actor)`, `approve(store_id, proposal_id, digest, note, actor)`, `execute(..., client, auth)`, `reconcile(..., client, auth)`, `listing(store_id)`; execution and reconciliation return persisted receipts. Admin routes call a fixed credential boundary; test transports inject no real credentials.

- [x] Write failing tests for proposal validation/digests, stale approval, execution gates, live identity/bounds checks, exact request body, replay, uncertainty, reconciliation and HTTP admin boundaries.
- [x] Run tests and observe failure because the new service/router is absent.
- [x] Implement the ledger, fixed-origin transport, configuration gates and admin routes.
- [x] Verify focused tests, existing eMAG tests and lint; document usage and unchanged local-only semantics.
- [ ] Commit, obtain independent whole-branch review, fix important findings, run CI, merge and deploy under standing user authorization.

## Execution record

Implementation follows the user's instruction to proceed with the API work. No concrete production price change is approved by that development request.

Independent review found literal SKU/PNK normalization and pre-POST crash status defects. Five reproductions failed before fixes: identifiers now preserve literal whitespace and the attempted-write marker atomically records uncertain delivery. Additional pre-review tests fixed environment-proxy preservation and concurrent read-back revision conflicts. Live account rights and binding remain operator-verification requirements; external changes cannot be atomically excluded without a platform compare-and-set contract. Uncertain attempts remain manually investigated, and price read-back never proves saleability or cash.

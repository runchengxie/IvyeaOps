# Operations follow-through Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task by task.

**Goal:** Deliver usable source, cost, replenishment, ownership and change-preview workflows.
**Architecture:** Extend the authenticated eMAG API with a versioned SQLite commercial ledger and pure Decimal calculators. Reuse snapshot identities and existing operations ledger.
**Tech Stack:** FastAPI, SQLite, React, TypeScript.
**Spec:** ../specs/2026-10-30-operations-next.md

## Global Constraints
- No marketplace writes; preview must state execution is unavailable.
- Persist private records only under settings.data_dir.
- Require snapshot and revision checks for local changes.
- Missing costs and stock remain unknown; no implicit zeros.

## Review Focus
- Reject ambiguous products, stale snapshots and conflicting revisions.
- Reject nonfinite, negative or boolean numeric inputs.
- Supplier links must be HTTPS detail.1688.com offers without credentials.
- Missing costs prevent profit outputs; currency conversion is explicit.
- Replenishment inputs are labelled scenarios and include inbound/reserved stock.

### Task 1: Commercial ledger and scenario calculations
Files: app/services/emag_commerce.py; app/tests/test_emag_commerce.py
- [x] Write failing tests for ledger persistence/isolation, source validation, stale/concurrent edits, missing costs, Decimal economics, stock/demand calculations and preview rejection.
- [x] Run tests and observe expected failures.
- [x] Implement view(store_id), save(store_id, snapshot_id, product_id, revision, inputs, actor), calculate(inputs, offer), preview(snapshot, offer, changes).
- [x] Run targeted tests, then backend suite and lint.

### Task 2: Ownership and authenticated API
Files: app/services/emag_operations.py; app/routers/emag_operations.py; corresponding tests.
- [x] Test persistent ownership across snapshots without carrying approvals forward.
- [x] Add revision-checked ownership storage and commerce GET/POST endpoints.
- [x] Verify admin access and bound actor.

### Task 3: Workbench and evidence
Files: client workbench commerce component, EmagWorkspace.tsx, docs and changelog.
- [x] Add product selection, supplier confirmation, explicit cost and replenishment inputs, and nonexecuting change previews.
- [x] Run frontend typecheck/i18n/build and real App harness verification.
- [x] Document scenario limitations and missing actual procurement data.

### Task 4: Review and integration
- [x] Review whole branch, fix important findings, run required checks.
- [ ] Commit, push, PR, merge when checks pass, deploy to identified local service and verify.


## Execution ledger

- 2026-10-31: Existing operations baseline: 5 passed.
- Backend scenarios and ownership follow RED/GREEN tests. Latest targeted run: 33 passed.
- Frontend: typecheck passed; i18n contract 8 passed; production build passed with existing large-chunk warnings.
- Real App harness in isolated Chrome: supplier inputs, save request, owner mutation and computed 1280px layout verified. Synthetic fixtures only.
- Whole-branch independent review: two important stock findings fixed with regressions (reserved backlog and invalid stock evidence).
- Decision: quote matching stays explicitly manual because no confirmed procurement SKU links have been provided. Automatic matching could associate the wrong specification.
- Deferred minor: embedded revision history is bounded at 100 edits; updates then stop explicitly. Archive/export remains unimplemented.
- Full backend regression: 1371 passed, 1 skipped, 19 warnings (429.70 seconds); latest added boundary tests: 33 targeted passed. No marketplace writer is implemented or invoked.

# Stock clearance implementation plan

Approved objective: consume existing inventory; no procurement/replenishment expansion or marketplace writes.
Design: deterministic snapshot-backed liquidation priority, explicit reasons and field references. Positive stock with tracked sales blockers comes first, then reconciled stock older than 180 days, then other positive stock; unknown and zero stock remain separate. No financial recovery, price floor or verified sales claim is computed from missing costs or unverified order-status semantics.

- [x] RED/GREEN tests for zero/unknown, blockers, age-band reconciliation, deterministic ranking and source references.
- [x] Add bounded weekly stock-observation comparison with compatible baseline; disappearance is not a sale.
- [x] Integrate clearance view in management dashboard and playbook; expose observed order counts by raw status only.
- [x] Verify real snapshot privately, backend tests, frontend checks and real App harness.
- [ ] Independent review, PR/CI, merge, deployment and safe cleanup.


Verification: 43 related backend tests passed; ruff and maintained docs checks passed. Frontend typecheck, 8 i18n tests and build passed; real App harness in isolated Chrome verified stock filters, same-store issue links, plan handoff and computed layout. Independent review's malformed optional-summary finding was fixed with RED/GREEN coverage; incomplete-baseline wording was corrected. Existing large-chunk and dependency deprecation warnings remain; no dependency or lockfile changes. Daily audit reports now include the same bounded clearance summary. Private real-snapshot verification was performed without committing seller data.

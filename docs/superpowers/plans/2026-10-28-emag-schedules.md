# eMAG scheduling preparation

User continues all-sidebar adaptation and previously selected manual runs, no schedule registration. Existing scheduler is an Agent prompt scheduler, not the deterministic eMAG CLI. Keep existing tasks untouched and available at an explicit Agent tab; default to eMAG preparation.

Frontend-only plan: admin imported-store/latest receipt view; CLI command with store, 1–29 day window and explicit offline replay mode; read-only server cron/timezone preview; local JSON plan download with enabled=false/registered=false, explicitly not consumed by a scheduler. No new execution endpoint, OS task, cron registration, model setup, credentials or actual collection. Non-admin never reads private evidence. Existing new Agent form defaults disabled, list/history failures remain errors rather than empty state, and preview must succeed before save. Existing enabled tasks are not toggled.

Verify default and explicit Agent tab/history, complete/no-source/error/receipt cases, no non-admin private reads, stale preview suppression, downloaded plan semantics and absence of schedule mutations, generic default disabled and error states. Real App harness desktop/mobile, typecheck/build, reused cron contract tests, independent review, live read-only check, then PR/merge/cleanup under standing authorization.

## Verification ledger

- Real App RED before implementation (missing default eMAG heading), GREEN after: receipt, server-time preview, JSON enabled=false/registered=false, offline argv, no schedule registration/run calls, source/receipt/preview failures, stale preview ignored, zero ordinary-user private reads, default-disabled Agent form, URL/back, list/history error states, 1440/390px no page errors/overflow.
- Existing scheduling/cron/backend contract tests: 25 passed. Independent `review_emag_publish` review: no important findings. No backend contracts/dependencies changed.
- Updated stale original schedule tour to describe eMAG manual preparation; harness skips the one-time tour for functional tests. No actual task created, enabled, changed or run.

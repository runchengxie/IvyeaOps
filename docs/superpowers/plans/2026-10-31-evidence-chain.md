# Field-bound eMAG diagnostic evidence plan

> Use superpowers:executing-plans inline.

Goal: make the existing deterministic workflow produce auditable field-bound handoffs.
Architecture: additive contract/schema fields plus a separate verifier, reused by job reports and approval transitions.
Spec: ../specs/2026-10-31-evidence-chain.md

- [x] RED/GREEN tests for zero/missing, source/entity mismatch, wrong field value, dependency forgery and old schema loading.
- [x] Add default-inference Evidence fields and schema_version=1 with old-file compatibility.
- [x] Generate bounded deterministic issue findings; verify observed fields and recognized rule dependencies.
- [x] Bind proposal diagnosis and revalidate on approval; add report evidence and diagnostics API.
- [x] Existing consumers and acceptance chain: 79 tests passed, ruff passed.
- [x] Independent review, then strengthen store-audit Skill and rerun pressure case.
- [x] Add bounded return VOC and local Listing claim warnings with tests.
- [ ] Run regression, integrate through PR and verify local runtime.

Ruling: only deterministic review actions are decision-grade in this first version; derived/estimate types without registered verifiers fail closed. This avoids making arbitrary calculations appear validated.


Execution evidence: independent review found field-domain and action-dependency bypasses; RED/GREEN regressions now reject both. Report gate metadata explicitly distinguishes checked output from all store findings. Skill pressure baseline permitted snapshot-only prose; strengthened protocol passes same-offer/current-version scenario. VOC review found identifier conflicts and malformed optional data; both fixed with regressions. Real App isolated Chrome verified VOC source references and persisted Listing warning display.

Latest verification: full backend run 1386 passed, 1 skipped, 19 warnings; subsequent added edge-case tests and consumers 88 passed. Frontend typecheck/build passed; real App harness verified VOC references and Listing warning display. Existing large-chunk and dependency-deprecation warnings remain. No dependencies added or lockfile changed. Integration remains pending CI.

# eMAG read-only collector implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement these tasks.

**Goal:** Publish reusable read-only eMAG RO collection alongside the existing external-agent MCP tools.

**Architecture:** A CLI obtains one Windows generic credential or explicit interactive input, calls only product_offer/read, and imports complete evidence through store_artifacts. Partial results never replace complete snapshots. No seller-specific defaults or business fixtures are published.

**Tech Stack:** Python, existing httpx, Windows ctypes, pytest.

**Spec:** User-authorized extraction of the local collector into reusable code and publication to their fork. Store data, credentials, local authentication bypass and machine configuration remain private.

## Constraints and review focus

- Fixed HTTPS RO endpoint; no redirects, retries or marketplace writes.
- Explicit store ID; exact credential target; no credential enumeration or logging.
- Stop on network/business/schema/duplicate errors and pagination cap; incomplete run exits nonzero.
- Missing inventory is unknown, not zero; price/status checks do not prove storefront availability.
- Local artifacts inherit the configured data directory and its existing size limits.

## Tasks

- [x] Test pagination, incomplete responses, redirects, redaction, unknown inventory and snapshot/report binding with synthetic records.
- [x] Extract services/emag_readonly.py and services/windows_credentials.py; add app/emag_cli.py with describe and prompt modes.
- [x] Add operator documentation, changelog and ADR; replace store-specific synthetic test labels.
- [x] Run focused tests and backend suite, review changes and publishable commit history; validate the CLI against real API without publishing results.
- [ ] Commit, push feature branch to origin, create a PR against fork main, verify remote SHA and PR URL.

## Validation outcome

49 focused tests passed. A live read-only CLI collection successfully imported a snapshot and report, and a restarted backend passed the standard MCP SDK read/save/read-back smoke test. No production data is included in this change.

The full backend suite is not green. Bare pytest collects `app/services/settings_test.py::test_value` as a test and errors because fixture `key` does not exist. A broader attempt showed additional failures and was interrupted before a complete diagnostic report; those failures have not been attributed to this change or fixed. Publish as a draft PR, not a merge-ready change. Existing anyio deprecation warnings remain.

Independent review found missing validation-status coverage; unknown counters and malformed-status regressions now cover it. Publishable diff and previously unpublished history were checked for local store/account/path markers and data/env files.

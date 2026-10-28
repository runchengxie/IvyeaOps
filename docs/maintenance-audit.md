# Documentation, test and localization audit

Audit date: 2026-10-28. English is canonical for the maintained public entry docs. The six priority `zh-CN` documents follow the same facts. Historical ADRs, research notes and detailed inherited guides are supplementary material, not evidence of a current implemented capability.

## Repository and authorization

The audit began on `feat/repository-cleanup`, based on `a9e793793a45bfd86aca6f8d2027334643227443`. The worktree already contained this session's authorized documentation/script/source-layout changes. They were retained. The user explicitly chose `src/client` and `src/server`, core eMAG navigation and collapsed advanced tools.

`origin` is `runchengxie/IvyeaOps`; `upstream` is `Hector-xue/IvyeaOps`. There was one main worktree, no `.gitmodules`, no gitlinks and no submodule status entries. There is no submodule SHA or missing checkout to audit. No submodule was initialized and no other repository was modified.

IvyeaAgent is an installed external dependency, locally version 1.16.9. Its CLI/HTTP adapter is consumed by this repository. Release workflows resolve an Agent ref separately, so the installed version does not pin every future package. Provider/model execution was not exercised by this audit.

## Corrections grounded in implementation

| Finding | Correction/evidence |
|---|---|
| Root docs described an Amazon-first product and advertised upstream packages as if they contained fork changes | Rewrote README and priority English docs, then `docs/zh-CN`; distinguished fork source from upstream archives |
| Source layout and frozen package paths were conflated | `app/core/layout.py` resolves source code under `src` while keeping frozen package layout; runtime/static/theme/script contracts passed |
| Git does not migrate ignored legacy `.env` files | Runtime fallback plus no-clobber installer copy; tests cover existing/new config and failed publication with no partial destination |
| Installed systemd units may still reference old `server` | `scripts/check-layout.sh` blocks automatic install/update for that detected unit and points to explicit migration steps |
| Removing BOM broke Chinese scripts in Windows PowerShell 5.1 | Restored compatible encoding and parsed the entry chain with actual `powershell.exe` |
| Original stop script killed by image/port broadly | It now checks this install's executable/command before stopping a specific PID. No real stop operation was executed |
| Turkish and Italian shared one language object | Split the entries; all eight existing locale IDs are exposed |
| Chinese Agent resources lacked 31 English keys and retained one unused key | Synchronized canonical English keys, types and interpolation tokens; removed the stale Chinese-only key |
| English plugin text implied an unverified maintenance guarantee | Changed it to describe the catalog label and synchronized Chinese |
| Error-text gate used URL pathname as a Windows filesystem path | Used `fileURLToPath`, retained the same detection rules and exemptions, and changed test diagnostics to English |
| Two eMAG pages rendered backend `detail` arrays directly | Used existing `errText`; synthetic 422 reproduced the failure before the fix and renders text afterward |
| Environment sample referenced removed GBrain setup and a missing settings route | Removed the obsolete example and corrected settings/configuration guidance |

## Executed verification

| Check | Observed result |
|---|---|
| Full backend regression after source/configuration migration | 1289 passed, 1 skipped, 19 warnings in 607.26 s |
| Related eMAG workspace tests including Accept-Language equivalence | 10 passed |
| Locale key/type/interpolation contracts | 8 passed after observed failures before synchronization |
| Runtime/layout/config migration/PowerShell and documented snapshot contracts | 16 passed |
| Windows PowerShell 5.1 parser and Bash syntax | Passed without running installation/update/stop actions |
| Backend ruff | Passed on the final source and verification scripts |
| Frontend typecheck and production build | Passed on the final tree; build completed in 22.86 s with the existing large-chunk warning |
| Maintained local document links | Passed for 17 entry documents; external URLs and heading anchors are outside this check |
| Existing error-text gate | Passed after Windows path and unsafe detail-read fixes |
| Real App harness | Core/advanced catalog, global search, primary entries, pins, keyboard, both shells and mobile passed; no page errors |
| Public optional browser smoke | Synthetic 422 handling, catalog navigation and locale fallback/equivalent structured evidence passed |
| Restarted authorized local service | `/console`, store listing and current workspace returned HTTP 200; read-only checks only |
| Manual CLI contract | `app.emag_job_cli --help`, `app.emag_workflow_cli --help`, and offer CLI `--help`/`--describe` ran and matched documented flags |
| Installed Python dependency compatibility | `uv pip check` checked 89 packages and passed |
| npm dependency security audit | Failed: 24 reported vulnerabilities, including 9 high, 10 moderate and 5 low; no critical findings |

The skipped full-suite case was the POSIX-permission check on Windows. Conditional Chrome, optional MCP and zstd tests remain valid; they were not deleted to improve counts. There is no configured coverage threshold, dedicated security-scanner CI gate or dependency-audit gate. Their absence is not a passing result.

The local runtime was Python 3.12.13 and Node.js 24.22.1 on Windows. Installers accept Node.js 18+, while CI uses Node.js 22.

The npm mirror returned an unsupported audit-endpoint 404. A retry with `--registry=https://registry.npmjs.org` produced the vulnerability report. The lockfile blob is unchanged from the base (`cc21d1025cd8f8e9f07a11d9789c66274be29ae0`), so these are recorded as an existing dependency baseline. High-severity entries include axios, browserslist, follow-redirects, form-data, js-yaml, nanoid, postcss, source-map-js and vite. No `audit fix`, dependency upgrade or ignore expansion was performed. Dependency remediation needs its own compatibility validation, especially where the suggested Vite fix is a major version change.

## Reproduce

Use [operations.md](operations.md) for the standard commands. For isolated UI verification, install `src/server/requirements-browser-test.txt` in a test environment, start `npm run dev:harness` from `src/client`, then run:

```powershell
src/server/.venv/Scripts/python.exe scripts/verify-workbench-ui.py
```

Use the Unix venv executable on Unix. The script requires a synthetic loopback harness marker before attempting fixture mutations. It never uses an existing browser profile. An available system Edge is detected on Windows; otherwise provide `--browser-executable` or install a Playwright test browser. Missing tooling is an execution failure, not silently counted as success.

## Limits and unresolved inconsistencies

- Main workbench text is largely Chinese. Only the Agent subtree has i18next. Supported saved IDs are `en`, `ko`, `zh-CN`, `ja`, `ru`, `de`, `tr`, `it`. The default is `zh-CN`, missing translation fallback is `en`, and unsupported saved preferences reset to the default. `en-US` resolves English resources in i18next but is not a saved language-list ID.
- The eMAG quality page's missing-stock count does not include every malformed/negative value that the backend classifies unknown. This product discrepancy is reported, not hidden by a changed test expectation.
- Platform filter timezone interpretation, invoice service periods, costs and uncollected inventory fields remain explicit evidence limits.
- Docker builds, binary packaging, Linux systemd changes, cross-platform execution of the entire matrix, private vulnerability reporting configuration and full provider/model runs were not executed here.
- The initial full run encountered a stale-module ImportError while code was being changed during execution. The fresh final process completed successfully. This is not presented as a product defect or a passing initial run.
- Internal historical documents are not all translated. Their original decisions are retained rather than rewritten to imply current support. No full-workbench i18n architecture was introduced.

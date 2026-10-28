# Backend test conventions

Use the active commands and evidence in [operations](operations.md) and [maintenance-audit](maintenance-audit.md). Earlier test counts were historical and have been removed from this current runbook rather than presented as today's result.

`src/server/conftest.py` isolates test state, home directories, data paths, skill seeding and background startup. Add shared isolation there instead of writing tests against production state. The suites are `src/server/tests` and `src/server/app/tests`, matching CI's split.

Use synthetic snapshots, store labels and credentials. Tests that change application globals should restore them or run in a subprocess. Preserve real HTTP/component contracts instead of replacing an entire feature with a hand-written imitation.

Windows coverage includes static JS/MJS MIME handling, drive/UNC project names, local subprocess/terminal behavior, explicit UTF-8 and actual Windows PowerShell 5.1 parsing. POSIX permission checks remain conditionally skipped on Windows. Optional Chrome/MCP/zstd checks explain missing prerequisites instead of silently passing.

The application writes PSD through its own writer and Pillow. `psd-tools` was removed as unused. Installing the current requirements does not automatically remove an old unused package from an existing environment. See [ADR-0038](decisions/0038-drop-unused-psd-tools.md).

New test comments and diagnostics are English unless validating localized output. Do not change expected results to conceal product failures. Report the baseline, regression and environment limitations separately.

# Contributing

Read [AGENTS.md](../AGENTS.md) before editing. The fork's source is in `src/client` and `src/server`; private state belongs outside tracked files.

English is the canonical language for maintained public documentation. Synchronize the priority `zh-CN` documents after checking the implementation. Keep API fields, CLI arguments, configuration keys, artifact meanings and stable identifiers unchanged across translations. New or modified test comments and diagnostics should be English unless testing localized output.

Use the commands in [operations](operations.md) and the dependency files under `src/server`. Do not delete valid tests, widen ignores, lower thresholds or change expected results to hide defects. Report pre-existing failures and environment limitations separately from regressions.

Inspect branch, remotes, worktrees and submodules before changing them. Do not initialize missing submodules or upgrade gitlinks as part of a documentation audit. Preserve existing work. Follow the session's publishing authorization and use PRs for protected branches. Explain the problem, resulting behavior and actual validation in the PR.

Changes are licensed under [AGPL-3.0](../LICENSE). Preserve upstream attribution.

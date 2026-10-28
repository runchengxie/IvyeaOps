# Repository layout

Source code lives in `src/client` and `src/server`. Management scripts use English names under `scripts`; maintained docs use kebab-case under `docs`. Root README.md, LICENSE, AGENTS.md, CLAUDE.md and tool configuration names remain conventional entry points. `.github/CONTRIBUTING.md` and `.github/SECURITY.md` link to their canonical document bodies.

See [installation](installation.md) for source/bundle differences, safe environment migration, systemd migration and Windows/Unix commands. See [configuration](configuration.md) for settings precedence. Private `data` remains outside `src` and outside commits.

The sidebar keeps task/automation and eMAG daily pages visible. “All tools” defaults to eMAG daily operations. System terminal, monitoring, external Agents, freight and user management are grouped as advanced tools. Search covers all permitted categories. Pinning, direct routes and keyboard navigation remain available. Hiding navigation does not change backend permission checks.

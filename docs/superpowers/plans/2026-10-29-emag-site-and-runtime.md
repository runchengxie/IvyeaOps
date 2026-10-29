# eMAG site and runtime follow-up implementation plan

**Goal:** Publish a project and documentation site grounded in the current English and zh-CN documents, improve evidence-backed maintenance, and prepare a reversible local runtime upgrade.

**Architecture:** A small static build reads an explicit public-document allowlist and resolves local links to either published pages or the repository. GitHub Actions validates the build on pull requests and publishes only after a main-branch change. The eMAG capability inventory distinguishes implemented read-only features from unsupported writes and retained legacy features.

**Constraints:** Do not publish store evidence, credentials, or plans as delivered features. Preserve API and artifact contracts, ignored data, and prior security/test baselines. Verify ownership and backup before touching the local service. Node/Python and frozen layouts remain as documented.

**Tasks:**
- [x] Add evidence-backed English and zh-CN capability maps.
- [x] Test and implement a deterministic static documentation build and link handling.
- [x] Add PR validation and a scoped GitHub Pages deployment workflow.
- [x] Pin the default Agent release across installation, CI and release builds.
- [ ] Verify the local runtime upgrade plan, dependencies, credentials and rollback before applying any authorized change.
- [ ] Run appropriate local/remote checks, review, merge and clean only task branches.

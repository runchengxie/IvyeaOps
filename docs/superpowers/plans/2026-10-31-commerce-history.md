# Procurement history continuation

Approved continuation of the previously deferred 100-edit history limit.
Design: archive revisions in a separate table of the same SQLite file. Preserve legacy history on the next successful edit, retain the most recent 100 entries in the existing response, and offer exclusive-cursor history pagination under the existing administrator boundary. No dependencies or UI changes.

- [x] Observe RED tests for 105 edits and legacy migration.
- [x] Implement transactional archive, conflict rejection and bounded history endpoint.
- [x] Targeted tests: 29 passed; ruff passed.
- [ ] Independent review and relevant final verification.
- [ ] PR, CI, merge, runtime verification and cleanup.

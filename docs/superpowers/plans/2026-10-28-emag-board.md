# eMAG operations board implementation plan

User approved the local eMAG focus design. Implement a single-store RO board on the existing fork, with admin-only local workflow records and immutable snapshot evidence. Do not add marketplace write endpoints.

1. Add synthetic tests for snapshot-scoped issue identities, sequential transitions, optimistic concurrency, stale evidence rejection and review against a newer snapshot.
2. Implement SQLite workflow records and admin REST endpoints; reuse the existing eMAG summary and store snapshots. Never carry approved/executed status into a new snapshot.
3. Add a real React route and navigation entry, evidence limitations, priority issues and explicit manual-record forms. Keep existing boards accessible.
4. Run backend regressions, typecheck/build, real UI validation, independent code review and local service restart. Record results privately; publish generic code only.

State sequence: pending → proposed → approved → executed → reviewed. Every transition requires a note and matching revision. Approved/executed records require the original snapshot still be latest; reviewed requires a different latest snapshot and records whether that specific issue remains. It is a review record, not an assertion the issue is resolved. Actor comes from authenticated admin identity. No API credential is exposed to the browser.

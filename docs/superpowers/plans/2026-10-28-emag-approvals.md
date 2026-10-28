# eMAG approvals adaptation

Continue the authorized sidebar adaptation using existing backend contracts. Add an admin-only local eMAG proposal queue, separate from existing general Agent permission requests. Reuse store listing, version-bound boards and CAS transition POST; only current-snapshot `proposed` issues are approvable. Require human note, display actual proposal/context/source, disable stale records after conflicts, clear selection on refresh, and surface partial-store failures without claiming an empty queue. Old-version proposals are counted as reference only. No automatic approvals, execution, rejection-state invention, credential access, schedules or real marketplace writes.

Preserve generic Agent permission ownership/session flow. Correct the page's misleading failure handling: transport failures are not expiration, and HTTP success without `ok` is not acceptance. Link eMAG context to exact store; add query selection to existing inspection page. Non-admin users never call private eMAG APIs.

Files: new EmagApprovalQueue.tsx, Approvals.tsx composition and safe result handling, EmagOperations.tsx store deep link, synthetic harness scenarios, changelog and workspace documentation. Verify actual component tree at desktop/mobile, payload/version/note, store link, stale and network failures, partial/empty and non-admin states; typecheck/build, independent review, live read-only inspection, PR/merge/cleanup.

## Verification ledger

- Actual App harness RED: missing local eMAG approval heading before implementation. GREEN: synthetic approval sends exact snapshot/revision/note, no actor override; conflict disables approval until reload; network failure never marks success; refresh clears selection; partial/source failures do not claim empty queue; ordinary user sends zero eMAG private reads; explicit store context selected over first store; generic Agent `ok=false` and transport failures are not accepted/expired, while 409 is expired. Desktop/mobile: no page errors or document overflow.
- Reused backend contract tests: 19 passed (local state/source/CAS/admin actor, generic owner/pending/decision persistence). No backend source or dependency changes; no full backend rerun needed for frontend-only composition.
- Independent reviewer `review_emag_publish`: no important findings after checking real permission and transition contracts, version checks, async cleanup and error semantics. Tests use synthetic operations; no actual store proposal or Agent request approved.

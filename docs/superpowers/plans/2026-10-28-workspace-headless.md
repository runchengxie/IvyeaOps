# eMAG workspace and headless workflow

User authorizes adapting all feasible sidebar functions and API-first recommendations; explicitly requests manual runs only, no scheduled task registration.

## Approved scope and choices

Reuse authenticated eMAG snapshots for dashboard, internal-catalog research, evidence-based playbook, local Listing drafts and data-quality analysis. Do not send PNKs to Amazon ASIN endpoints. Preserve original platform pages at explicit legacy routes; update persistent-board rendering as well as route elements. Own-catalog distributions are not market-wide demand or competitor research.

Console gets explicit RO/RON/PNK evidence context; knowledge templates and image translation gain eMAG languages/use cases. Terminal, external agents, monitoring and users remain generic with accurate eMAG scope guidance. Freight needs actual RO destination quotes and is not inferred from unrelated lanes. News exposes official source links, not rebranded Amazon feeds.

Add a snapshot-bound admin draft ledger (research/listing/playbook), and a manual headless CLI: optional read-only collection → explicit snapshot comparison → deterministic report → atomic receipt. Serialize per-store runs, retain failed-run evidence, distinguish offline replay from fresh collection, do not overwrite prior evidence on collection failure. Expose receipt reading via read-scoped MCP. Add CLI for manual workflow records with explicit versions/revisions; no automatic approvals and no marketplace writer.

## Implementation and checks

1. Synthetic tests for draft source binding/stale rejection, job lock/failure/delta semantics and read-only MCP status.
2. Admin workspace endpoints, draft storage, headless runner and CLI.
3. Real eMAG React business boards, all navigation/keep-alive consumers, generic-module context and RO/BG/HU image languages.
4. Documentation with module capability matrix, full backend tests, typecheck/build, isolated real-component harness and live local API validation. Review, merge and cleanup under standing authorization. No registration of scheduled tasks or real seller writes.

## Execution ledger

- Source-binding/replay/failure tests observed RED (missing modules), then GREEN. Admin actor/strict input, MCP read-only and per-store collector lock verified.
- Final review: independent reviewer `review_emag_publish`; no critical findings. Fixed CLI lock traceback (regression RED→GREEN); fixed receipt oversize with 64KB/200-change explicit preview (regression RED→GREEN). Complete source snapshots remain immutable and referenced.
- Minor deferred: quality page's stock-unknown count currently covers missing fields only; malformed/negative numeric stock is additionally classified unknown by backend summary. Existing missing-field display does not capture those malformed inputs.
- Five real React routes verified at 1440/390px with no document overflow/page errors; refresh clears unsaved draft, keep-alive navigation uses eMAG pages. Isolated test browser uses synthetic fixtures, never user's profile.
- Actual manual offline replay completed without credentials/network. First fresh attempt failed safely during collection; resource-level read-only diagnostic subsequently completed all endpoints, and one end-to-end retry completed fresh collection, delta, report and receipt. No platform writes or schedule registration.
- Full initial suite: 1271 passed, 1 skipped, 1 existing Windows locale failure. Fixed that test's UTF-8 reads explicitly; isolated RED→GREEN. Final full run uses the completed fixes.
- Final full backend regression: 1274 passed, 1 skipped (571.25s). Production build passed; generic-module contexts/news rendered with no page errors. Lint follow-up removes two unused existing imports, uses equivalent dict literals, and explicitly permits terminal output only for named CLI files.

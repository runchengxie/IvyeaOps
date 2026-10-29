# Usage, CLI and evidence contracts

[简体中文](zh-CN/usage.md)

## Daily workflow

1. Collect or explicitly import an eMAG RO snapshot.
2. Inspect source time, coverage and limitations before using the business pages.
3. Investigate issues and record a proposal locally.
4. An administrator can approve a current-source proposal with a note and revision check.
5. Record any actual manual execution separately, then collect a newer snapshot for review.

The cockpit and research pages use own-store evidence. Catalog distribution is not market demand or share. Listing drafts are local text, not submitted listings. Costs are missing until supplied, so profit and recommended selling prices are not computed.

The page labelled Approvals separates local eMAG records from general Agent permission requests. Accepting an Agent request may resume a command or file write. An eMAG local approval does not perform that action.

## CLI

From `src/server`, using the installed venv:

```powershell
.venv/Scripts/python.exe -m app.emag_job_cli --store-id example-ro --from-latest
.venv/Scripts/python.exe -m app.emag_job_cli --store-id example-ro --days 29
.venv/Scripts/python.exe -m app.emag_workflow_cli --store-id example-ro
```

On Unix, use `.venv/bin/python` instead. `example-ro` is a placeholder, not an account lookup. `app.emag_cli` collects offer evidence, `app.emag_business_cli` collects the combined selected evidence, and `app.emag_job_cli` adds comparison, report and receipt handling.

`app.emag_cli --describe` describes collection without reading credentials or calling eMAG. `--prompt` accepts hidden interactive credentials on supported terminal platforms. The combined business/job collection path uses the saved Windows credential; offline `--from-latest` needs no credential.

For supported structured validation errors, new collections retain up to eight compact `error_details` entries per status: `code`, `section`, the platform's `en_GB` message and optional `extra_info`. Text is limited to 256 characters per field; URLs and email addresses are replaced. `error_details_truncated` indicates omitted or shortened entries. The full submitted product document and error identifiers are not retained. Other sensitive content may remain in platform messages, so snapshots remain private. Older snapshots keep their original placeholder and are not retroactively enriched.

Job exits: 0 means the report/receipt stage completed, 1 means a recorded stage failed, 2 means an invalid/unavailable job entry, storage problem or busy lock. Check the receipt rather than treating an old successful run as the current result. Forceful termination can leave no new receipt.

For a manual local transition, supply `--snapshot-id`, `--issue-id`, `--state`, `--revision`, `--note`. Review additionally requires the explicitly inspected newer `--review-snapshot-id`. State order is `pending` → `proposed` → `approved` → `executed` → `reviewed`. There is no automatic approval or rejection/rework transition.

## Artifacts

Snapshots and reports live below `store-artifacts` in the data directory. Each artifact is limited to 2 MB. Reports bind an existing `snapshot_id` and include its source evidence. Store/report identifiers allow 1–80 ASCII letters, digits, underscores or hyphens, beginning with a letter or digit. `captured_at` requires a timezone.

Minimal synthetic import example, not real store evidence:

```json
{
  "store_id": "example-ro",
  "platform": "emag",
  "marketplace": "RO",
  "captured_at": "2026-10-28T00:00:00Z",
  "source": "synthetic-example",
  "coverage": ["offers"],
  "limitations": ["Synthetic example, not verified store data"],
  "data": {"offers": []}
}
```

Save it as a local file and run `python -m app.store_cli import-snapshot FILE` from the installed backend environment. `read-snapshot STORE_ID` and `read-report REPORT_ID` read stored artifacts. The snapshot read tool returns the import's `snapshot_id`; latest means the latest import, not necessarily the newest collection timestamp.

Run receipts are in `store-artifacts/jobs/<store>/`. Modes are `fresh_collection` and `existing_snapshot`. A receipt records stage, status, source/baseline IDs, report ID and timestamps. The change preview is limited to 200 entries and 64 KB, with `change_count` and `changes_truncated`. Full referenced snapshots remain the evidence for omitted changes.

Missing stock is not zero. Numeric 10 and string `10.00` compare as the same value. An absent product is an observation, not confirmed delisting. Invoice amounts preserve reported signs/currencies and do not establish payment, cost or profit. Return requests are not proof of refunds.

## APIs and MCP

Administrator REST routes under `/api/emag` include store listing, boards, workspace, drafts, local issue transitions and job receipt reads. The browser does not expose a credential-read or job-run endpoint. Browser mutations retain session/Origin checks.

| MCP tool | Scope | Effect |
|---|---|---|
| `ivyea_store_snapshot` | `read` | Read imported evidence |
| `ivyea_emag_job_status` | `read` | Read latest recorded manual run |
| `ivyea_report_read` | `read` | Read saved local report |
| `ivyea_report_save` | `write` | Save a local source-bound report |

MCP uses bearer tokens at `/api/mcp`; session login does not replace the token. These tools do not modify a marketplace. Generic Amazon keyword tools remain Amazon-specific.

## Schedule preparation

`/schedules` previews a future cron in server timezone and exports a JSON draft with `enabled=false`, `registered=false`, `scheduler_connected=false`. No current scheduler consumes it. `/schedules?tab=agent` is the existing model-dependent prompt scheduler. Do not infer automatic eMAG execution from a draft or from a manual run receipt.

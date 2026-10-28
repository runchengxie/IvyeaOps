# External Agent and MCP access

The MCP endpoint is `http://127.0.0.1:8001/api/mcp`. Clients need Streamable HTTP support and a bearer token. Normal browser session authentication and MCP token authentication are separate. The published application does not include the private loopback login adapter used during local exploration.

Administrator token management is under `/api/mcp-admin/tokens`. Read tools require read scope; saving a local report requires write scope. The token value is returned at issuance and should not be committed. Reading evidence discloses it to the client, so its data handling matters.

| Tool | Scope | Contract |
|---|---|---|
| `ivyea_health` | read | Version and integration state |
| `ivyea_store_snapshot` | read | Latest imported store snapshot, with source/time/limits |
| `ivyea_emag_job_status` | read | Latest recorded manual job receipt |
| `ivyea_report_read` | read | Saved local report by report ID |
| `ivyea_report_save` | write | Local report bound to an explicitly read snapshot ID |

These tools do not fetch eMAG credentials or modify a marketplace. Missing evidence returns an error. Generic keyword tools still need their original platform data sources. Knowledge features still depend on their Agent integration, so imported-evidence access does not make every feature model-independent.

From `src/server`, use `python -m app.store_cli import-snapshot FILE`, `read-snapshot STORE_ID` or `read-report REPORT_ID` with the installed environment. See the validated synthetic JSON example in [usage](usage.md). The CLI and HTTP service must use the same `IVYEA_OPS_DATA_DIR`. Latest means the latest import, not necessarily the newest `captured_at`.

The HTTP service can remain running while the browser is closed. It is the full FastAPI service, not a separate MCP-only executable. Client-specific configuration formats must be checked against that client's version; this audit did not verify every external Harness. The repository skill at `skills/emag/store-audit/SKILL.md` is a guide, not an automatic global installation.

The standard SDK contract test is `app/tests/test_mcp_sdk.py`; it uses local ASGI transport and synthetic evidence, not a store or model. See [operations](operations.md) for test dependencies and [architecture](architecture.md) for boundaries.

# eMAG capabilities landing page

Follow-up to the approved all-sidebar eMAG adaptation: the capabilities market was omitted from the previous change. Reuse React, existing admin evidence APIs and routes; no new connector, marketplace writes, schedule, model setup or skill installation.

Default to a dedicated eMAG capability tab. Separate shipped local capabilities from external community skills and original-platform data sources. Link to actual workspaces, show imported-source availability and latest manual receipt with clear unknown/error/stale-source states. Never infer a working API credential from an imported snapshot. Display manual CLI/MCP contracts without executing commands or exposing credentials. Non-admin visitors receive descriptions only and do not request private APIs.

Preserve all explicit existing tab deep links and make URL/history the tab state. Add clear scope labels for community/skills/MCP/auth. Verify in the real App harness, default landing, existing deep links, tab/back navigation, disabled non-admin reads, receipt failures and 1440/390px layout. Build/typecheck, independent review, PR/merge/cleanup under standing authorization.

## Execution ledger

- Actual App harness observed RED before implementation: default eMAG heading missing. GREEN after implementation: default tab, source/job status, URL/back navigation, original tab deep links, no-source/source-failure/no-job/job-failure states, non-admin zero private eMAG reads, desktop/mobile no document overflow and zero page errors.
- Independent read-only review by `review_emag_publish`: no important findings; source errors, actor visibility, async cleanup and URL fallback inspected.
- No backend contracts, dependencies or real store data changed. No credential validation, community installation, scheduled task or marketplace write performed.

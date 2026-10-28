# Troubleshooting

## Source page is missing after a directory update

Build from `src/client`, then restart the specific backend if its code changed. Verify the backend's runtime/code root rather than assuming the old `client`/`server` source locations. Frozen packages retain their old internal layout. Check [installation](installation.md) before migrating a service unit.

## Existing login/configuration appears missing

Keep both copies until inspected. New source uses `src/server/.env` and falls back to legacy `server/.env` when needed. The installer never overwrites an existing new environment file with the old one. Check `IVYEA_OPS_DATA_DIR` and the process environment too. Do not generate replacement credentials merely to make startup succeed.

## Browser login works but eMAG collection fails

Browser login does not prove API permission or IP allowlisting. The saved Windows credential must be the Generic Credential target `IvyeaOps/eMAG/RO`. `app.emag_cli --describe` describes fixed offer requests without reading credentials. Network failures and incomplete pagination must not be treated as a fresh complete snapshot.

## Old run is shown after a failed or interrupted job

Inspect run ID, mode, stage, finish time and source/report IDs. A crash before receipt publication can leave the previous receipt. Offline replay is not fresh collection. Read the full limitations before interpreting stock, invoice or return observations.

## State change reports a conflict

Reload the source and record revision. Local approvals require a current snapshot and the next allowed transition. Review requires an explicitly inspected newer latest snapshot. Do not bypass the conflict check or silently approve a different source version.

## UI validation produces an error

FastAPI 422 detail can be an object array. The frontend must use `errText` before rendering it. The error-text gate and synthetic browser test protect this contract. A transport failure is not an accepted or expired Agent permission decision.

## Dependency audit cannot run

Some registry mirrors do not implement npm's security endpoint. A process-local `--registry=https://registry.npmjs.org` retry can distinguish that limitation from a vulnerability result. Record the actual exit status. Do not run `audit fix` or change package versions as a workaround for a documentation check.

## Language appears partially translated

The main workbench does not have a global language switch. The Agent subtree defaults to `zh-CN` and falls back to `en`; other listed locales load lazily. Its English saved resource ID is `en`. See the audit for the verified supported list and remaining limitations.

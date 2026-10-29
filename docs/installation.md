# Installation and source-layout migration

[简体中文](zh-CN/installation.md)

## Requirements and build types

Installers accept Python 3.11+ and Node.js 20+; CI builds use Node.js 22. This audit ran locally on Windows with Python 3.12.13 and Node.js 24.22.1. The CI server test matrix covers Linux and Windows; macOS CI is temporarily disabled. A configured job is not evidence that it ran for a particular commit.

The backend runtime requirements, test requirements and optional MCP test requirements are separate files under `src/server`. Installers, CI and release builds default to the IvyeaAgent tag in `configs/ivyea-agent.ref`, currently `v1.16.9`. An explicit `IVYEA_AGENT_REF` overrides the default. Existing installations and local or bundled Agent sources may use a different version; a Git tag is not immutable. Do not assume the fork has a published binary release.

Windows source install and launch:

```powershell
powershell -NoProfile -File scripts/manage.ps1 -Action install -Target source
powershell -NoProfile -File scripts/manage.ps1 -Action start -Target source
```

The English double-click launchers are under `scripts/`. `install.bat` selects a bundled installation only when `IvyeaOpsServer.exe` exists at the install root. `start.bat` opens a foreground process. `start-hidden.vbs` starts in the background. `start-lan.bat` is an explicit source LAN mode and does not automatically change firewall rules.

Linux/macOS source install and launch:

```bash
bash scripts/manage.sh install
bash scripts/manage.sh start
```

Installers may install dependencies, build the frontend and offer optional components. They are not validation commands. The Unix server runs in the foreground; use Ctrl+C to stop it, or manage your installed systemd service.

## Existing source installations

Python 3.9 and 3.10 are no longer supported. Install Python 3.11 or newer, stop the application, and move an older `src/server/.venv` to a backup location before running the installer again. The installer refuses to reuse an older environment; preserve `src/server/.env`, credentials and the data directory. Review custom service paths before restarting.

The tracked source directories moved from `client`/`server` to `src/client`/`src/server`. Git does not move ignored files in other checkouts. The runtime falls back to legacy `server/.env` when the new environment file is missing. The installer copies the old file only when the new file does not exist. It retains the old copy and does not overwrite an existing new configuration.

Recreate or reuse the virtual environment through the new installer. A venv from another machine or location is not a portable artifact. Keep `data` and your configured `IVYEA_OPS_DATA_DIR` unchanged. Check custom shortcuts, service units and deployment paths.

If systemd still reports `<repository>/server` as WorkingDirectory, installation/update stops instead of restarting that incompatible unit. Inspect `systemctl cat ivyea-ops.service`, back up your unit and preserve its custom user, port and flags. Change WorkingDirectory and PYTHONPATH to `<repository>/src/server`, and its Python executable to `<repository>/src/server/.venv/bin/python`. Run `sudo systemctl daemon-reload`, install the new environment, verify it, then restart the service. Do not replace a customized unit with a default template blindly.

Frozen Windows/macOS packages retain their existing internal `client`/`server` layout. `scripts/update-bundle.bat` is for bundled Windows builds. Do not install an upstream archive over a custom fork without a compatible release and a backup.

## Manual development commands

```bash
cd src/client
npm ci
npm run typecheck
npm run test:i18n
npm run build
```

From `src/server`, create/activate the platform's venv, install `requirements.txt`, `requirements-test.txt` and `requirements-mcp-test.txt`, then run `python -m pytest`. Build the frontend before using the production FastAPI UI. Vite development uses port 5174, backend port 8001, and the isolated component harness uses 5199.

The repository no longer supplies Docker deployment files or a Docker setup command. Existing container deployments need their own maintained configuration. Systemd changes and binary release assembly were not executed by the local documentation audit unless explicitly listed in its evidence table.

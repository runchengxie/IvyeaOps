# Windows installation

Use the canonical [installation guide](installation.md) or its [zh-CN version](zh-CN/installation.md).

English launchers now live under `scripts`. `install.bat` dispatches source or bundled installation, `start.bat` runs in the foreground, and `start-hidden.vbs` starts in the background. `stop.bat` uses the Windows action interface. `update-bundle.bat` is for frozen Windows bundles, not an arbitrary source checkout.

Source configuration is `src/server/.env`; frozen packages retain `server/.env`. Existing legacy source configuration is preserved through the documented fallback/no-clobber migration. Do not copy an upstream archive over an eMAG fork without checking compatibility.

`start-lan.bat` explicitly binds the source server to LAN interfaces and sets its allowed origins. It does not automatically add firewall rules. The standard application still uses session authentication. A private development adapter is not part of the installer.

Windows PowerShell 5.1 entry scripts containing non-ASCII text require compatible encoding. The audit parsed them with actual `powershell.exe`; it did not run the installers, change firewall rules or enable startup tasks.

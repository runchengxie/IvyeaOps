@echo off
set PYTHONUTF8=1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage.ps1" -Action start -Foreground -Lan %*
if errorlevel 1 pause

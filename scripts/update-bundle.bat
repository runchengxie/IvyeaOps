@echo off
set PYTHONUTF8=1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage.ps1" -Action update -Target bundle -Gui %*
if errorlevel 1 pause

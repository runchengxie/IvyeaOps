# Foreground source/bundle launcher; LAN sharing is an explicit source-only mode.
param([ValidateSet('source','bundle')][string]$Target='source',[switch]$Lan)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$RepoRoot=Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8='1'
if($Target -eq 'bundle'){
    if($Lan){throw 'LAN console mode requires a source checkout.'}
    & (Join-Path $RepoRoot 'IvyeaOpsServer.exe')
    exit $LASTEXITCODE
}
$ServerDir=Join-Path $RepoRoot 'src/server'
$python=Join-Path $ServerDir '.venv/Scripts/python.exe'
if(-not(Test-Path -LiteralPath $python)){throw 'Run scripts/install.bat first.'}
$bindHost='127.0.0.1'
if($Lan){
    $adapter=Get-NetIPConfiguration|Where-Object {$_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up'}|Select-Object -First 1
    if(-not $adapter){throw 'No active LAN adapter with a default gateway.'}
    $lanAddress=($adapter.IPv4Address|Select-Object -First 1).IPAddress
    $bindHost='0.0.0.0';$env:IVYEA_OPS_HOST=$bindHost
    $env:IVYEA_OPS_ALLOWED_ORIGINS="http://127.0.0.1:8001,http://localhost:8001,http://${lanAddress}:8001"
    Write-Host "LAN sharing: http://${lanAddress}:8001 . If needed, allow TCP 8001 in Windows Firewall."
}
# No automatic firewall/UAC changes. The explicit foreground window owns the run.
Push-Location $ServerDir
try{& $python -m uvicorn app.main:app --host $bindHost --port 8001;$taskExit=$LASTEXITCODE}finally{Pop-Location}
exit $taskExit

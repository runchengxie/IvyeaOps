# Stop only processes whose executable/command identifies this checkout.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$RepoRoot=Split-Path -Parent $PSScriptRoot
$PidFile=Join-Path $RepoRoot 'data/ivyeaops.pid'
$BundleExe=Join-Path $RepoRoot 'IvyeaOpsServer.exe'
function Test-OwnedProcess($process){
    if(-not $process){return $false}
    if($process.ExecutablePath -and $process.ExecutablePath -ieq $BundleExe){return $true}
    $line=[string]$process.CommandLine
    $sourcePython=Join-Path $RepoRoot 'src/server/.venv/Scripts/python.exe'
    $localLauncher=Join-Path $RepoRoot 'data/run-local.py'
    $identified=$line.IndexOf($sourcePython,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $line.IndexOf($localLauncher,[StringComparison]::OrdinalIgnoreCase) -ge 0
    return $identified -and $line -match '(uvicorn|app\.main|run-local\.py)' -and $process.Name -match '^python(w)?\.exe$'
}
$candidates=@()
if(Test-Path -LiteralPath $PidFile){
    $saved=(Get-Content -LiteralPath $PidFile -Raw).Trim()
    if($saved -match '^\d+$'){
        $savedProcess=Get-CimInstance Win32_Process -Filter "ProcessId=$saved"
        if($savedProcess){$candidates+=,$savedProcess}else{Remove-Item -LiteralPath $PidFile}
    }
}
$listener=Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue|Select-Object -First 1
if($listener){$candidates+=,(Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)")}
$candidates+=@(Get-CimInstance Win32_Process -Filter "Name='IvyeaOpsServer.exe'"|Where-Object {$_.ExecutablePath -ieq $BundleExe})
$stopped=@()
foreach($process in $candidates|Where-Object {$_}|Sort-Object ProcessId -Unique){
    if(Test-OwnedProcess $process){Stop-Process -Id $process.ProcessId;$stopped+= $process.ProcessId}
}
if($stopped.Count -and (Test-Path -LiteralPath $PidFile)){Remove-Item -LiteralPath $PidFile}
if($stopped.Count){Write-Host "Stopped verified workspace processes: $($stopped -join ', ')"}
else{Write-Host 'No verified workspace process stopped. Unrelated listeners/PIDs are left untouched.'}

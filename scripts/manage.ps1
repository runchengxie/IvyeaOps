# Unified Windows entry point. -DryRun resolves commands without side effects.
param(
    [ValidateSet('install','start','stop','update')][string]$Action='start',
    [ValidateSet('auto','source','bundle')][string]$Target='auto',
    [switch]$Foreground,[switch]$Lan,[switch]$Gui,[switch]$DryRun
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$RepoRoot=Split-Path -Parent $PSScriptRoot
if($Target -eq 'auto'){$Target=if(Test-Path -LiteralPath (Join-Path $RepoRoot 'IvyeaOpsServer.exe')){'bundle'}else{'source'}}
$entry='';$entryArgs=@()
switch($Action){
    'install' {$entry=if($Target -eq 'bundle'){'install-exe.ps1'}else{'install.ps1'}}
    'start' {
        if($Foreground -or $Lan){$entry='start-console.ps1';$entryArgs=@('-Target',$Target);if($Lan){$entryArgs+='-Lan'}}
        else{$entry='start-hidden.ps1';$entryArgs=@('-Target',$Target)}
    }
    'stop' {$entry='stop-hidden.ps1'}
    'update' {if($Target -ne 'bundle'){throw 'This Windows update entry supports bundled builds only. Source checkouts use the in-app updater or a reviewed git update.'};$entry='update-exe.ps1'}
}
if($Gui -and $Action -in @('stop','update')){$entry='windows-action-gui.ps1';$entryArgs=@('-Mode',$Action)}
$script=Join-Path $PSScriptRoot $entry
if(-not(Test-Path -LiteralPath $script)){throw "Missing action script: $entry"}
if($DryRun){@{action=$Action;target=$Target;script=$script;arguments=$entryArgs;executed=$false}|ConvertTo-Json -Compress;exit 0}
& $script @entryArgs
if(-not $?){exit 1}

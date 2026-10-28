Set Shell = CreateObject("WScript.Shell")
Set Fso = CreateObject("Scripting.FileSystemObject")
ScriptPath = Fso.BuildPath(Fso.GetParentFolderName(WScript.ScriptFullName), "manage.ps1")
Shell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File " & Chr(34) & ScriptPath & Chr(34) & " -Action start", 0, False

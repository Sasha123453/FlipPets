param(
  [Parameter(Mandatory=$true)][string]$Serial,
  [ValidateSet('Diagnose','Install','Start','Supervise','Status','Stop')][string]$Action='Diagnose',
  [string]$Adb='C:\platform-tools\adb.exe'
)
$ErrorActionPreference='Stop'
if (!(Test-Path -LiteralPath $Adb)) { $Adb=(Get-Command adb -ErrorAction Stop).Source }
function Invoke-Phone {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
  $taskResult=& $Adb -s $Serial @Arguments 2>&1
  if ($LASTEXITCODE -ne 0) { throw ($taskResult -join "`n") }
  return ($taskResult -join "`n")
}
if ((Invoke-Phone get-state).Trim() -ne 'device') { throw 'Selected device is not ready or USB access was not authorised.' }
switch ($Action) {
  Install {
    $taskApk=Join-Path $PSScriptRoot 'FlipPets.apk'
    $expected=((Get-Content -LiteralPath (Join-Path $PSScriptRoot 'FlipPets.sha256.txt')) -split '\s+')[0]
    if ((Get-FileHash -LiteralPath $taskApk -Algorithm SHA256).Hash -ne $expected) { throw 'APK hash mismatch.' }
    Invoke-Phone install --no-incremental -r $taskApk
  }
  default {
    Invoke-Phone push (Join-Path $PSScriptRoot 'flip-pets-control.sh') /data/local/tmp/flip-pets-control.sh | Write-Host
    $taskText=Invoke-Phone shell sh /data/local/tmp/flip-pets-control.sh $Action.ToLowerInvariant()
    $taskText | Write-Host
    if ($Action -eq 'Diagnose') {
      $taskPath=Join-Path $PSScriptRoot 'phone-diagnostics.txt'
      $taskText | Set-Content -LiteralPath $taskPath -Encoding utf8
      Write-Host "Saved: $taskPath"
    }
  }
}

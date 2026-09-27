$ErrorActionPreference = "Continue"
$adb = "C:\Users\Kaiser\AppData\Local\Android\Sdk\platform-tools\adb.exe"
$probe = "E:\AI\宠物管理\scripts\android_acceptance\cdp_probe.cjs"

function Ensure-Device {
  param([int]$retries = 6)
  for ($i = 0; $i -lt $retries; $i++) {
    & $adb kill-server 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    & $adb start-server 2>&1 | Out-Null
    Start-Sleep -Seconds 3
    $state = (& $adb devices 2>&1 | Select-String "emulator-5556\s+device")
    if ($state) { return $true }
    Start-Sleep -Seconds 5
  }
  return $false
}

function Get-AppPid {
  $out = (& $adb -s emulator-5556 shell pidof com.petaccess.map 2>&1 | Out-String).Trim()
  if ($out -match "^\d+$") { return $out }
  return ""
}

if (-not (Ensure-Device)) { Write-Output "FATAL no device"; exit 1 }

# ensure app running
$appPid = Get-AppPid
if (-not $appPid) {
  & $adb -s emulator-5556 shell am start -n com.petaccess.map/.MainActivity 2>&1 | Out-Null
  Start-Sleep -Seconds 12
  $appPid = Get-AppPid
}
Write-Output "APP_PID=$appPid"

# one shot forward + probes; re-establish forward before each probe to survive churn
foreach ($step in @("home", "search", "nav")) {
  $port = 9240
  & $adb -s emulator-5556 forward --remove tcp:$port 2>&1 | Out-Null
  & $adb -s emulator-5556 forward tcp:$port localabstract:webview_devtools_remote_$appPid 2>&1 | Out-Null
  Start-Sleep -Seconds 1
  node $probe $port $step 2>&1 | Select-Object -Last 1
  # if node failed, refresh forward once and retry
  if ($LASTEXITCODE -ne 0) {
    & $adb -s emulator-5556 forward --remove tcp:$port 2>&1 | Out-Null
    & $adb -s emulator-5556 forward tcp:$port localabstract:webview_devtools_remote_$appPid 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    node $probe $port $step 2>&1 | Select-Object -Last 1
  }
}

# final screenshots: Home, Search
$shots = "E:\AI\宠物管理\artifacts\ui-audit\android"
foreach ($pair in @(@("home-m3-final", "#/"), @("search-m3-final", "#/search"))) {
  $name = $pair[0]; $hash = $pair[1]
  & $adb -s emulator-5556 shell "am start -n com.petaccess.map/.MainActivity" 2>&1 | Out-Null
  Start-Sleep -Seconds 4
  & $adb -s emulator-5556 shell "input keyevent 82" 2>&1 | Out-Null
  $out = Join-Path $shots "$name.png"
  cmd /c "`"$adb`" -s emulator-5556 exec-out screencap -p > `"$out`" 2>nul"
  $len = (Get-Item $out -ErrorAction SilentlyContinue).Length
  Write-Output "SHOT $name bytes=$len"
}
Write-Output "ANDROID_FAST_DONE"
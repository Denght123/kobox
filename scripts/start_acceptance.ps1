param(
  [int]$FrontendPort = 5173,
  [int]$BackendPort = 8001
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Root ".tmp\run"
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Stop-PortProcess {
  param([int]$Port)

  $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Where-Object { $_.OwningProcess -and $_.State -eq "Listen" }

  foreach ($connection in $connections) {
    Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
  }
}

Stop-PortProcess -Port $FrontendPort
Stop-PortProcess -Port $BackendPort

Push-Location $BackendDir
try {
  $env:DATABASE_URL = "sqlite:///./kobox.db"
  $env:AUTO_CREATE_TABLES = "true"
  $env:SEED_ON_STARTUP = "true"
  $env:ADMIN_STATS_TOKEN = "local-dev-admin-stats-token"
  alembic upgrade head
}
finally {
  Pop-Location
}

$backendLog = Join-Path $RunDir "backend-$BackendPort.log"
$frontendLog = Join-Path $RunDir "frontend-$FrontendPort.log"

$backendCommand = @"
`$env:DATABASE_URL='sqlite:///./kobox.db'
`$env:AUTO_CREATE_TABLES='true'
`$env:SEED_ON_STARTUP='true'
`$env:ADMIN_STATS_TOKEN='local-dev-admin-stats-token'
cd "$BackendDir"
python -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort *> "$backendLog"
"@

$frontendCommand = @"
cd "$FrontendDir"
npm run dev -- --host 127.0.0.1 --port $FrontendPort *> "$frontendLog"
"@

$backendProcess = Start-Process -FilePath powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand -PassThru
$frontendProcess = Start-Process -FilePath powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand -PassThru

Start-Sleep -Seconds 4

$backendReady = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health/ready" -UseBasicParsing -TimeoutSec 15
$frontendReady = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort/" -UseBasicParsing -TimeoutSec 15

[PSCustomObject]@{
  FrontendUrl = "http://127.0.0.1:$FrontendPort/"
  BackendUrl = "http://127.0.0.1:$BackendPort/"
  BackendHealth = $backendReady.Content
  FrontendStatus = $frontendReady.StatusCode
  BackendProcessId = $backendProcess.Id
  FrontendProcessId = $frontendProcess.Id
  BackendLog = $backendLog
  FrontendLog = $frontendLog
}

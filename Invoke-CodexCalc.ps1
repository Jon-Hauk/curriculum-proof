# One Codex calculation pass. Refuses to start a second pass while one is running.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Codex = Join-Path $env:LOCALAPPDATA "Programs\OpenAI\Codex\bin\codex.exe"
$OutDir = Join-Path $Root "runs\codex"
$Lock = Join-Path $OutDir "running.lock"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (Test-Path $Lock) {
  Write-Output "ALREADY_RUNNING $Lock"
  exit 2
}
if (-not (Test-Path $Codex)) {
  Write-Output "CODEX_MISSING $Codex"
  exit 3
}
Set-Content -Path $Lock -Value $PID -Encoding ascii
try {
  Get-Content -Raw (Join-Path $Root "CODEX-JOB.md") | & $Codex exec `
    --skip-git-repo-check `
    --color never `
    --approve-for-me `
    -C $Root `
    --add-dir (Join-Path $Root "answer-pass") `
    -o (Join-Path $OutDir "last-message.txt")
  Write-Output "CODEX_EXIT $LASTEXITCODE"
  exit $LASTEXITCODE
}
finally {
  Remove-Item -Force $Lock -ErrorAction SilentlyContinue
}

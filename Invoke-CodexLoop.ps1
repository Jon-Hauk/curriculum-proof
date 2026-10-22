# Supervisor: runs Codex calculation passes back to back on the rolling queue until EndTime.
# Commits locally after each pass (never pushes). Handles the 5-hour and weekly Codex limits.
param(
  [string]$EndTime = "07:45",        # local clock time, today
  [string]$NotBefore = "",           # optional local clock time to wait for before the first pass
  [int]$MaxPassMinutes = 100,        # a pass longer than this is stopped and resumed by the next pass
  [int]$QueueAheadMinutes = 180,
  [string[]]$TargetForms = @("m301-2019", "p30-2013"),  # the targeted queue; nothing else is queued
  [switch]$Refill                     # only with -Refill are other prepared forms appended from forms.json
)
$ErrorActionPreference = "Continue"
$TargetForms = @($TargetForms | ForEach-Object { $_ -split "," } | Where-Object { $_ })
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Codex = Join-Path $env:LOCALAPPDATA "Programs\OpenAI\Codex\bin\codex.exe"
$OutDir = Join-Path $Root "runs\codex"
$LogDir = Join-Path $OutDir "logs"
$Lock = Join-Path $OutDir "running.lock"
$LoopLock = Join-Path $OutDir "loop.lock"
$Progress = Join-Path $Root "PROGRESS.md"
$QueueFile = Join-Path $Root "QUEUE.md"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$End = [datetime]::ParseExact($EndTime, "HH:mm", $null)
if ($End -lt (Get-Date).AddMinutes(-1)) { $End = $End.AddDays(1) }
$SupLog = Join-Path $LogDir ("supervisor-" + (Get-Date -Format "yyyyMMdd-HHmm") + ".log")

function Log($m) { $l = (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " " + $m; Add-Content -Path $SupLog -Value $l }
function PidAlive($p) { try { $null = Get-Process -Id ([int]$p) -ErrorAction Stop; return $true } catch { return $false } }
function AppendProgress($text) { [IO.File]::AppendAllText($Progress, $text + "`r`n", (New-Object Text.UTF8Encoding $false)) }

function Get-Usage {
  $u = [ordered]@{ p = $null; pReset = $null; s = $null; sReset = $null; file = $null }
  $dir = Join-Path $env:USERPROFILE ".codex\sessions"
  $files = Get-ChildItem $dir -Recurse -Filter *.jsonl -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5
  foreach ($f in $files) {
    $lines = Get-Content $f.FullName -ErrorAction SilentlyContinue | Where-Object { $_ -match '"rate_limits"' }
    if (-not $lines) { continue }
    $line = @($lines)[-1]
    foreach ($k in @("primary", "secondary")) {
      $m = [regex]::Match($line, '"' + $k + '"\s*:\s*\{[^{}]*\}')
      if ($m.Success) {
        $pct = [regex]::Match($m.Value, '"used_percent"\s*:\s*([0-9.]+)')
        $rs = [regex]::Match($m.Value, '"resets_at"\s*:\s*([0-9]+)')
        if ($k -eq "primary") { if ($pct.Success) { $u.p = [double]$pct.Groups[1].Value }; if ($rs.Success) { $u.pReset = [DateTimeOffset]::FromUnixTimeSeconds([int64]$rs.Groups[1].Value).LocalDateTime } }
        else { if ($pct.Success) { $u.s = [double]$pct.Groups[1].Value }; if ($rs.Success) { $u.sReset = [DateTimeOffset]::FromUnixTimeSeconds([int64]$rs.Groups[1].Value).LocalDateTime } }
      }
    }
    $u.file = $f.FullName
    break
  }
  return $u
}
function UsageText($u) { "5h {0}% (resets {1:HH:mm}), weekly {2}% (resets {3:yyyy-MM-dd HH:mm})" -f $u.p, $u.pReset, $u.s, $u.sReset }

function Read-Queue {
  $rows = @()
  if (-not (Test-Path $QueueFile)) { return $rows }
  foreach ($l in Get-Content $QueueFile) {
    $c = $l.Split("|") | ForEach-Object { $_.Trim() }
    if ($c.Count -ge 9 -and $c[1] -match '^\d+$') {
      $rows += [pscustomobject]@{ order = [int]$c[1]; id = $c[2]; title = $c[3]; items = $c[4]; est = [int]$c[5]; status = $c[6]; retired = $c[7] }
    }
  }
  return $rows
}
function Write-Queue($rows) {
  $o = @("# Codex queue", "", "Rolling queue for CODEX-QUEUE.md. Codex sets status to in-progress, then retired. The supervisor appends prepared forms from forms.json so that at least $QueueAheadMinutes minutes of estimated work stay queued.", "", "| order | form-id | title | items | est-min | status | retired-at |", "|---|---|---|---|---|---|---|")
  foreach ($r in $rows) { $o += "| $($r.order) | $($r.id) | $($r.title) | $($r.items) | $($r.est) | $($r.status) | $($r.retired) |" }
  [IO.File]::WriteAllLines($QueueFile, [string[]]$o, (New-Object Text.UTF8Encoding $false))
}
function Refill-Queue {
  $rows = @(Read-Queue)
  $changed = $false
  # supervisor fallback: a complete form folder that Codex forgot to mark
  foreach ($r in $rows) {
    $d = Join-Path $OutDir $r.id
    if ($r.status -ne "retired" -and (Test-Path (Join-Path $d "completion.json")) -and (Test-Path (Join-Path $d "worked.md")) -and (Test-Path (Join-Path $d "answers.json"))) {
      $r.status = "retired"; $r.retired = (Get-Date -Format "yyyy-MM-dd HH:mm") + " (marked by supervisor)"; $changed = $true
    }
  }
  $man = Join-Path $Root "forms.json"
  if (Test-Path $man) {
    $forms = @((Get-Content -Raw $man | ConvertFrom-Json).forms)
    # drop rows that are not targeted and not yet started; they stay prepared in forms.json
    $keep = @($rows | Where-Object { $_.status -eq "retired" -or $_.status -eq "in-progress" -or $TargetForms -contains $_.id })
    if ($keep.Count -ne $rows.Count) { $rows = $keep; $changed = $true }
    $ahead = ($rows | Where-Object { $_.status -ne "retired" } | Measure-Object -Property est -Sum).Sum
    if (-not $ahead) { $ahead = 0 }
    $cands = @($forms | Where-Object { $TargetForms -contains $_.id } | Sort-Object { [array]::IndexOf($TargetForms, $_.id) })
    if ($Refill) { $cands += @($forms | Where-Object { $TargetForms -notcontains $_.id }) }
    foreach ($f in $cands) {
      if ($Refill -and $TargetForms -notcontains $f.id -and $ahead -ge $QueueAheadMinutes) { break }
      if ($rows | Where-Object { $_.id -eq $f.id }) { continue }
      if (-not (Test-Path (Join-Path $Root ("answer-pass\" + $f.id + "\questions-only.pdf")))) { continue }
      $n = 1; if ($rows.Count) { $n = ($rows | Measure-Object -Property order -Maximum).Maximum + 1 }
      $rows += [pscustomobject]@{ order = $n; id = $f.id; title = $f.title; items = $f.items; est = [int]$f.est_min; status = "queued"; retired = "" }
      $ahead += [int]$f.est_min; $changed = $true
    }
  }
  if ($changed -or -not (Test-Path $QueueFile)) { Write-Queue $rows }
  return @(Read-Queue)
}

function Form-Stats($id) {
  $d = Join-Path $OutDir "$id\items"
  $s = [ordered]@{ items = 0; agree = 0; disagree = 0 }
  if (Test-Path $d) {
    $s.items = @(Get-ChildItem $d -Filter *.py | Where-Object { $_.Name -notmatch '-check\.py$' }).Count
    foreach ($c in Get-ChildItem $d -Filter *-check.out) {
      $last = (Get-Content $c.FullName | Where-Object { $_.Trim() -ne "" } | Select-Object -Last 1)
      if ($last -match '^\s*disagree\s*$') { $s.disagree++ } elseif ($last -match '^\s*agree\s*$') { $s.agree++ }
    }
  }
  return $s
}

$Reopened = @{}
function Check-Form($id) {
  # full bar: every item has .py/.out, a -check.py/.out ending in agree/disagree, an answer, and a worked.md entry
  $d = Join-Path $OutDir $id; $it = Join-Path $d "items"
  $r = [ordered]@{ ok = $true; problems = @(); disagree = @(); empty = @() }
  $ids = @()
  if (Test-Path $it) { $ids = @(Get-ChildItem $it -Filter *.py | Where-Object { $_.Name -notmatch '-check\.py$' } | ForEach-Object { $_.BaseName }) }
  $ans = @{}
  if (Test-Path (Join-Path $d "answers.json")) {
    try { foreach ($a in (Get-Content -Raw (Join-Path $d "answers.json") | ConvertFrom-Json).items) { $ans[($a.id -replace ' ', '-')] = "$($a.answer)" } } catch { $r.problems += "answers.json unreadable" }
  } else { $r.problems += "answers.json missing" }
  foreach ($k in $ans.Keys) { if ($ids -notcontains $k) { $ids += $k } }
  $worked = ""; if (Test-Path (Join-Path $d "worked.md")) { $worked = Get-Content -Raw (Join-Path $d "worked.md") } else { $r.problems += "worked.md missing" }
  foreach ($i in ($ids | Sort-Object -Unique)) {
    if (-not (Test-Path (Join-Path $it "$i.out"))) { $r.problems += "$i no .out" }
    if (-not $ans.ContainsKey($i) -or [string]::IsNullOrWhiteSpace($ans[$i])) { $r.empty += $i; continue }
    $co = Join-Path $it "$i-check.out"
    if (-not (Test-Path (Join-Path $it "$i-check.py")) -or -not (Test-Path $co)) { $r.problems += "$i no check" }
    else {
      $last = (Get-Content $co | Where-Object { $_.Trim() -ne "" } | Select-Object -Last 1)
      if ($last -match '^\s*disagree\s*$') { $r.disagree += $i } elseif ($last -notmatch '^\s*agree\s*$') { $r.problems += "$i check has no verdict" }
    }
    $pat = '(?i)\b' + [regex]::Escape(($i -replace '-', ' ')) + '\b|\b' + [regex]::Escape($i) + '\b'
    if ($worked -and $worked -notmatch $pat) { $r.problems += "$i not in worked.md" }
  }
  if ($ids.Count -eq 0) { $r.problems += "no items" }
  if ($r.problems.Count) { $r.ok = $false }
  return $r
}
function Post-Pass($id, $why, $code, $start, $limitHit) {
  $rows = Refill-Queue
  $row = $rows | Where-Object { $_.id -eq $id }
  $st = Form-Stats $id
  $chk = Check-Form $id
  if ($row -and $row.status -eq "retired" -and -not $chk.ok) {
    if (-not $Reopened[$id]) {
      $Reopened[$id] = 1
      foreach ($r in $rows) { if ($r.id -eq $id) { $r.status = "in-progress"; $r.retired = "" } }
      Write-Queue $rows; $row.status = "in-progress (reopened: full bar not met)"
    } else { $row.status = "retired (FULL BAR NOT MET)" }
  }
  $u2 = Get-Usage
  $hash = Commit-Pass ("Codex pass {0}: {1} items, checks {2} agree / {3} disagree, status {4}." -f $id, $st.items, $st.agree, $st.disagree, $row.status)
  $mins = [math]::Round(((Get-Date) - $start).TotalMinutes, 1)
  $line = "- {0} pass end ({1}, code {2}, {3} min): form {4} status {5}; items {6}; checks {7} agree / {8} disagree; full bar {9}; commit {10}; usage {11}{12}" -f (Get-Date -Format 'HH:mm'), $why, $code, $mins, $id, $row.status, $st.items, $st.agree, $st.disagree, $(if ($chk.ok) { "met" } else { "NOT met" }), $hash, (UsageText $u2), $(if ($limitHit) { "; limit message in log" } else { "" })
  AppendProgress $line
  if ($chk.disagree.Count) { AppendProgress "  - REVIEW ${id}: disagree checks on $($chk.disagree -join ', ') (answers kept as written, not re-answered)." }
  if ($chk.empty.Count) { AppendProgress "  - REVIEW ${id}: empty answers on $($chk.empty -join ', ')." }
  if ($chk.problems.Count) { AppendProgress "  - REVIEW ${id}: full-bar gaps: $(($chk.problems | Select-Object -First 15) -join '; ')." }
  $null = Commit-Pass "Log Codex pass $id."
  Log "PASS_END form $id why $why code $code status $($row.status) commit $hash"
  return $mins
}
function Get-RepoCodex { @(Get-CimInstance Win32_Process -Filter "Name='codex.exe'" | Where-Object { $_.CommandLine -match ' exec ' -and $_.CommandLine -match [regex]::Escape($Root) }) }

function Commit-Pass($msg) {
  $paths = @("QUEUE.md", "PROGRESS.md", "CODEX-QUEUE.md", "Invoke-CodexLoop.ps1", "prepare_forms.py", "forms.json", ".gitignore")
  $paths += @(Get-ChildItem $Root -Filter "PROTOCOL-*.md" | ForEach-Object { $_.Name })
  foreach ($r in Read-Queue) { if (Test-Path (Join-Path $OutDir $r.id)) { $paths += "runs/codex/$($r.id)" } }
  foreach ($p in $paths) { if (Test-Path (Join-Path $Root $p)) { git add -- $p 2>$null } }
  git reset -q -- sources answer-pass runs/codex/logs 2>$null
  $staged = @(git diff --cached --name-only)
  $held = @()
  foreach ($f in $staged) {
    if ($f -match '^(sources|answer-pass)/' -or $f -match '(console|supervisor|pass-).*\.(log|err)$' -or $f -match '\.(log|err|lock|pdf)$') { $held += $f; continue }
    $full = Join-Path $Root $f
    if (Test-Path $full) {
      $t = Get-Content -Raw $full -ErrorAction SilentlyContinue
      if ($t -match '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -or $t -match '(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_|AKIA[0-9A-Z]{16}|xox[baprs]-|-----BEGIN [A-Z ]*PRIVATE KEY)') { $held += $f }
    }
  }
  foreach ($f in $held) { git reset -q -- $f 2>$null; Log "SCRUB held back from commit: $f" }
  if (-not (git diff --cached --name-only)) { return "none" }
  git commit -q -m $msg 2>$null | Out-Null
  return (git rev-parse --short HEAD)
}

function Stop-Tree($p) { if ($p -and -not $p.HasExited) { & taskkill.exe /T /F /PID $p.Id 2>$null | Out-Null } }

# ---- singleton
if ((Test-Path $LoopLock) -and (PidAlive (Get-Content $LoopLock))) { Log "LOOP_ALREADY_RUNNING pid $(Get-Content $LoopLock)"; exit 2 }
Set-Content -Path $LoopLock -Value $PID -Encoding ascii
Log "SUPERVISOR_START pid $PID end $($End.ToString('yyyy-MM-dd HH:mm')) notBefore '$NotBefore'"
AppendProgress "`n## Supervisor block $(Get-Date -Format 'yyyy-MM-dd HH:mm') to $($End.ToString('HH:mm')) Denver (Invoke-CodexLoop.ps1, pid $PID)`n"
$fails = 0
try {
  if ($NotBefore) {
    $nb = [datetime]::ParseExact($NotBefore, "HH:mm", $null)
    while ((Get-Date) -lt $nb -and (Get-Date) -lt $End) { Start-Sleep 20 }
  }
  # a pass left running by an earlier supervisor: wait for it, enforce the slot end, then account for it
  $orph = Get-RepoCodex
  if ($orph.Count) {
    $of = (Read-Queue | Where-Object { $_.status -eq "in-progress" } | Select-Object -First 1).id
    Log "ADOPT running codex pid $($orph[0].ProcessId) form $of"
    Set-Content -Path $Lock -Value $PID -Encoding ascii
    $ostart = $orph[0].CreationDate; $owhy = "exit"
    while ((Get-RepoCodex).Count) {
      Start-Sleep 15
      if ((Get-Date) -ge $End) { $owhy = "slot end"; foreach ($x in Get-RepoCodex) { & taskkill.exe /T /F /PID $x.ProcessId 2>$null | Out-Null }; break }
    }
    Remove-Item -Force $Lock -ErrorAction SilentlyContinue
    if ($of) { $null = Post-Pass $of "$owhy, adopted" "n/a" $ostart $false }
  }
  while ((Get-Date) -lt $End.AddMinutes(-3)) {
    if ((Get-RepoCodex).Count) { Log "a codex exec for this repo is already running; waiting"; Start-Sleep 60; continue }
    if ((Test-Path $Lock) -and (PidAlive (Get-Content $Lock))) { Log "lock held by $(Get-Content $Lock); waiting"; Start-Sleep 60; continue }
    if (Test-Path $Lock) { Remove-Item -Force $Lock; Log "removed stale lock" }
    $u = Get-Usage
    if ($u.s -ne $null -and $u.s -ge 100) { AppendProgress "- $(Get-Date -Format 'HH:mm') WEEKLY_LIMIT_HIT: $(UsageText $u). Supervisor stopped."; Log "WEEKLY_LIMIT_HIT"; break }
    if ($u.p -ne $null -and $u.p -ge 100 -and $u.pReset -gt (Get-Date)) {
      $wake = $u.pReset.AddMinutes(5)
      if ($wake -ge $End.AddMinutes(-3)) { AppendProgress "- $(Get-Date -Format 'HH:mm') 5h limit used up; reset $($u.pReset.ToString('HH:mm')) is past the slot end. Stopped."; break }
      AppendProgress "- $(Get-Date -Format 'HH:mm') 5h limit used up; sleeping until $($wake.ToString('HH:mm'))."
      Log "5H_LIMIT sleep until $wake"; while ((Get-Date) -lt $wake) { Start-Sleep 30 }; continue
    }
    $rows = Refill-Queue
    $cur = $rows | Where-Object { $_.status -eq "queued" -or $_.status -eq "in-progress" } | Select-Object -First 1
    if (-not $cur) { Log "TARGET_QUEUE_RETIRED"; AppendProgress "- $(Get-Date -Format 'HH:mm') TARGET_QUEUE_RETIRED: every targeted form is retired. Supervisor stops cleanly; no refill with other material."; break }
    if (-not (Test-Path $Codex)) { Log "CODEX_MISSING"; break }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $out = Join-Path $LogDir "pass-$stamp.log"; $err = Join-Path $LogDir "pass-$stamp.err"
    $cargs = @("exec", "--skip-git-repo-check", "--color", "never", "--approve-for-me", "-C", "`"$Root`"", "--add-dir", "`"$(Join-Path $Root 'answer-pass')`"", "-o", "`"$(Join-Path $LogDir "last-message-$stamp.txt")`"")
    $start = Get-Date
    $p = Start-Process -FilePath $Codex -ArgumentList $cargs -RedirectStandardInput (Join-Path $Root "CODEX-QUEUE.md") -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
    $null = $p.Handle
    Set-Content -Path $Lock -Value $PID -Encoding ascii
    Log "PASS_START form $($cur.id) codex pid $($p.Id) usage $(UsageText $u)"
    AppendProgress "- $($start.ToString('HH:mm')) pass start: form $($cur.id), codex pid $($p.Id), usage at launch $(UsageText $u)."
    $why = "exit"
    while (-not $p.HasExited) {
      Start-Sleep 15
      if ((Get-Date) -ge $End) { $why = "slot end"; Stop-Tree $p; break }
      if ((Get-Date) -ge $start.AddMinutes($MaxPassMinutes)) { $why = "pass timeout"; Stop-Tree $p; break }
    }
    $p.WaitForExit(30000) | Out-Null
    $code = $null; try { $code = $p.ExitCode } catch {}
    Remove-Item -Force $Lock -ErrorAction SilentlyContinue
    $logtxt = ((Get-Content -Raw $out -ErrorAction SilentlyContinue) + (Get-Content -Raw $err -ErrorAction SilentlyContinue))
    $limitHit = $logtxt -match '(?i)usage limit|rate limit reached|hit your .*limit'
    $u2 = Get-Usage
    $mins = Post-Pass $cur.id $why $code $start $limitHit
    if ($why -eq "slot end") { break }
    if ($code -ne 0 -and -not $limitHit -and $mins -lt 3) { $fails++ } else { $fails = 0 }
    if ($fails -ge 5) { AppendProgress "- $(Get-Date -Format 'HH:mm') STOPPED: 5 quick failed passes in a row; see runs/codex/logs."; break }
    if ($fails -gt 0) { Start-Sleep (60 * $fails) }
    if ($limitHit -and -not ($u2.p -ge 100)) { Start-Sleep 120 }
  }
}
finally {
  Remove-Item -Force $Lock -ErrorAction SilentlyContinue
  Remove-Item -Force $LoopLock -ErrorAction SilentlyContinue
  AppendProgress "- $(Get-Date -Format 'HH:mm') supervisor exit."
  $null = Commit-Pass "Close the Codex supervisor block."
  Log "SUPERVISOR_EXIT"
}

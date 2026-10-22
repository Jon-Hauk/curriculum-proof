# Codex calculation job

Codex does the calculations. Grok does not. The sealed Sonnet answers in `runs/answers.json` stay untouched.

The session is a 6-hour fill. Do not exit because the answer file exists. Stop only when Codex reports the usage limit, or when 6 hours of work on this queue are done.

## Rules

- Compute in Python. Exact work uses sympy. Numerical work uses numpy and scipy. High precision uses mpmath. Save the script and the output that actually ran.
- Read only `answer-pass/questions-only.pdf`.
- Do not open `sources/math-30-1-practice-test-2022.pdf`. That file contains the published key.
- Do not open `runs/answers.json`, `SCORE.md`, or any sample solution.
- One attempt per item. An empty answer is allowed when a figure did not survive. Do not guess a figure. Do not replace an answer already written in `runs/codex/answers.json`.
- Do not grade yourself and do not edit `PROTOCOL.md`.

## Queue, in order

1. Under `runs/codex/items/`, one `MC-11.py` and `MC-11.out` (and the same for every other id). Then write `runs/codex/answers.json` with `{"items":[{"id":"MC 1","answer":"<letter>"}]}`. Ids are `MC 1` through `MC 24`, `NR 1` through `NR 8`, and `WR 1` through `WR 3`.
2. For every id that already has an answer, add `MC-11-check.py` and `MC-11-check.out`. The check re-derives the value and writes `agree` or `disagree`. It does not change the answer.
3. If the 6-hour allowance is still open after both of those, write `runs/codex/worked.md` with one short derivation per id, each derivation quoting the script output. Then stop. Do not start another exam.

## Launch

From this directory:

```
powershell -NoProfile -ExecutionPolicy Bypass -File .\Invoke-CodexCalc.ps1
```

That script is one `codex exec` with workspace write, `--approve-for-me`, and this file as the prompt.

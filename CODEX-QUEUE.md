# Codex rolling calculation queue

Codex is the calculator. Codex does not grade. This file is the prompt for every pass started by `Invoke-CodexLoop.ps1`. The 2022 job in `CODEX-JOB.md` is finished history; do not redo or touch it.

## What one pass does

1. Open `QUEUE.md`. Take the first row whose status is `queued` or `in-progress`. That row's `form-id` is your form for this pass. If no row is `queued` or `in-progress`, write `runs/codex/queue-empty.txt` with the time and stop.
2. Change that row's status to `in-progress` in `QUEUE.md`.
3. Read `PROTOCOL-<form-id>.md`, then read only `answer-pass/<form-id>/questions-only.pdf` and the allowed reference `answer-pass/<form-id>/formula-sheet.pdf`.
4. Write all output under `runs/codex/<form-id>/`:
   - `items/<ID>.py` and `items/<ID>.out` for every item, where `<ID>` is the item id with the space replaced by a dash (`MC 7` becomes `MC-7`, `NR 3` becomes `NR-3`, `WR 1` becomes `WR-1`). The `.out` file is the real output of running the `.py` file with Python. Exact work uses sympy, numerical work uses numpy and scipy, high precision uses mpmath.
   - `answers.json` as `{"form":"<form-id>","items":[{"id":"MC 1","answer":"<letter>"},{"id":"NR 1","answer":"<digits>"},{"id":"WR 1","answer":"short final result"}]}`. Multiple-choice answers are a single letter. Numerical-response answers are the digits a student would record, as the question instructs.
   - `items/<ID>-check.py` and `items/<ID>-check.out` for every item that has an answer. The check re-derives the value by a different route (substitution, numeric evaluation, brute force or simulation) and its last line is exactly `agree` or `disagree`. A check never changes the answer.
   - `worked.md` with one short derivation per id, each quoting the script output it relies on.
   - `completion.json` as `{"form":"<form-id>","items":N,"answered":N,"checks_agree":N,"checks_disagree":N,"finished":"<ISO time>"}` with the real counts.
5. When all of that exists, change the row's status in `QUEUE.md` to `retired` and put the local time in its `retired-at` cell. Then stop. Do not start another form in the same pass; the supervisor commits and relaunches you right away.

If the form folder already has partial output from an earlier pass that was cut off, continue it: keep every answer, script and output that already exists, and only add what is missing.

## Rules

- Never open anything under `sources/`. Those files contain the published keys, sample solutions and scoring guides.
- Never open `runs/answers.json`, `SCORE.md`, `grade_machine.py` output, or anything under `runs/codex/` that belongs to another form, and never edit `PROTOCOL.md`, `PROTOCOL-*.md`, `CODEX-JOB.md`, `CODEX-QUEUE.md`, `forms.json` or the 2022 files directly under `runs/codex/`.
- Do not look for keys online or anywhere else. No web access is needed.
- Do not grade yourself, do not estimate a score, and do not write any claim about correctness against a key.
- One attempt per item. Never replace an answer that already exists in `answers.json`. A `disagree` check is recorded, not resolved by changing the answer.
- An empty answer is allowed when a figure or table did not survive extraction. Do not guess a figure; say in `worked.md` what was missing.
- Do not invent results. Every number in `worked.md` and `answers.json` comes from a script that actually ran.
- Do not run `git` commands, do not push, and do not write email addresses, tokens or other secrets into any file. The supervisor commits locally.
- Stay inside this repository. Never touch any other folder.

## Launch (for Jon)

The supervisor runs passes back to back until the end time and handles usage limits:

```
powershell -NoProfile -ExecutionPolicy Bypass -File .\Invoke-CodexLoop.ps1 -EndTime 07:45
powershell -NoProfile -ExecutionPolicy Bypass -File .\Invoke-CodexLoop.ps1 -NotBefore 14:00 -EndTime 19:45
```

Forms are prepared with `py -3 prepare_forms.py` (downloads to `sources/`, cuts `answer-pass/<form-id>/questions-only.pdf`, writes `PROTOCOL-<form-id>.md` and `forms.json`). Only the targeted forms (`-TargetForms`, default `m301-2019,p30-2013`) are queued; other prepared forms stay unqueued unless `-Refill` is given. The supervisor stops cleanly once the targeted queue is retired. After each pass it checks the full bar (script, output, independent check and worked derivation for every item) and flags every `disagree` check, empty answer or gap in `PROGRESS.md` for review; nothing is re-answered. A form marked retired with gaps is reopened once so Codex can add only the missing pieces.

## Precision rules (added 2026-10-19 after p30-2013 NR 2)

- When the data booklet or formula sheet gives a constant in the units the answer needs (for example h in eV*s), use that constant directly instead of converting from SI. Rounding can depend on which route is taken.
- If an unrounded value lies within 0.5% of a rounding boundary for the recorded digits, compute it by both routes and note the boundary in worked.md. Keep one answer.
- A check must re-derive the value by a different route from the question. It must not reconstruct the inputs from the recorded answer.

# curriculum-proof

**Case study:** [`CASE_STUDY.md`](CASE_STUDY.md) is the short version of what this pipeline did: 123 items worked across three forms, 113 of 114 machine-scored items correct, and how the one miss and the one disagreement were handled.

A small, script-verified pipeline for working Alberta Education diploma practice and released-item forms with AI tools, and for scoring the machine-scored items against the published keys. Jon Hauk designed and ran it. The AI tools did the work they are credited with below; every number in the outputs comes from a script that actually ran.

This repository contains the harness, the protocols, aggregate scores and the logs. The per-item solver scripts, outputs, checks, derivations and per-item answers are kept privately because they encode the copyrighted Alberta item content; see [`runs/ITEMS-PRIVATE.md`](runs/ITEMS-PRIVATE.md). It contains no Alberta Education material (see "Copyright" below).

## Notice

Item numbers refer to Alberta Education diploma exam materials, (c) Crown in Right of Alberta; not affiliated with or endorsed by the Government of Alberta. The MIT license covers only this repository's code and write-up, not Alberta's material.

Official PDFs (alberta.ca):

- [Physics 30 Released Items 2013](https://www.alberta.ca/system/files/custom_downloaded_images/edc-physics30-released-items-2013.pdf)
- [Mathematics 30-1 Released Items 2019](https://www.alberta.ca/system/files/custom_downloaded_images/ed-diploma-exam-math-30-1-released-Items-2019.pdf)
- [Mathematics 30-1 Practice Test 2022](https://www.alberta.ca/system/files/custom_downloaded_images/edc-mathematics-30-1-practice-test.pdf)

## How it works

**Director / answerer split.** A director sets up each form: it downloads the PDF, verifies its SHA-256, cuts a questions-only extract, and freezes a protocol (`PROTOCOL.md`, `PROTOCOL-<form-id>.md`) before any answer exists. The answerer only sees the questions extract and the allowed formula sheet or data booklet. It never sees the key, the sample solutions or the scoring guides, and it does not grade itself. Scoring against the key is a separate step done by something that is not the answerer.

- Director: Grok (xAI), working with Jon. Grok saw the 2022 key while locating the key page, so it was disqualified as an answerer.
- 2022 answerer: Claude Sonnet (Anthropic), via Claude Code, one call, Read/Write tools only: no shell, no Python, no calculator. Output: `runs/answers.json` (kept privately). Scored by `grade_machine.py` into `SCORE.md`.
- Calculator: OpenAI Codex CLI (model `gpt-6-astra`), run with `codex exec`. It re-worked the 2022 form (`runs/codex/`) and then worked two more forms from a queue (`runs/codex/m301-2019/`, `runs/codex/p30-2013/`).

**Every item gets four artifacts (kept privately).** For each item id (`MC n`, `NR n`, `WR n`) Codex writes a Python calculation (sympy for exact work, numpy/scipy for numerics, mpmath for high precision), the real output of running it, an independent check by a different route ending in `agree` or `disagree`, and a short derivation that quotes the saved output, plus an `answers.json` per form. A recorded answer is never replaced; a `disagree` is flagged for review, not fixed by re-answering. These artifacts encode the item content, so they are not published; only per-form `completion.json` counts are. See `runs/ITEMS-PRIVATE.md`.

**Queue.** `Invoke-CodexLoop.ps1` supervises passes over `QUEUE.md` using the prompt in `CODEX-QUEUE.md`, checks that every item has all four artifacts, flags disagreements and gaps in `PROGRESS.md`, and commits locally. `prepare_forms.py` downloads forms listed in it, verifies hashes, cuts the questions-only extracts and writes `forms.json` and the per-form protocols. Protocols exist for more forms than were run; only m301-2019 and p30-2013 were queued. `-Model` and `-ReasoningEffort` pin the Codex model for a run instead of reading the local config.

## Disagreements and lessons

- **m301-2019 MC 5 (disagreement resolved).** The calculation and its check disagreed. Diagnosis: the check counted dark bands along a line in a raster rendering of the figure, and one printed stroke produced three bands within 1 PDF point. Grouped, the count supported the recorded answer. An independent second opinion from Veridian (a multi-agent review run through Jon's Hermes agent, given only the question page) agreed with the recorded answer. The recorded answer was not changed. See `PROGRESS.md`.
- **p30-2013 NR 2 (the one miss).** Codex's numerical response did not match the key. The unrounded value landed on a rounding boundary for the digits to be recorded, and computing it through SI constants (h in J·s, then converting joules to electronvolts) rounded differently from using the data booklet's constant in eV·s directly. The check did not catch it, because it rebuilt the input from the recorded answer instead of re-deriving the value. Rules added afterwards to `CODEX-QUEUE.md`: use the booklet constant in the units the answer needs, compute both routes near a rounding boundary, and never let a check rebuild inputs from the recorded answer. The rules were added after the run; their first test is the pre-registered c30-2019 run below.

## Pre-registered runs

- **c30-2019, Chemistry 30 Released Items 2019: 56 of 60.** Pre-registered 2026-10-31 06:59 MDT; run 07:11 to 07:26 MDT in one 15-minute pass. [`PREREG-c30-2019.md`](PREREG-c30-2019.md) fixed the model, the prompt, the file hashes, the scoring rule and what gets published before any answer existed. Scored by `grade_form.py` into [`SCORE-c30-2019.md`](SCORE-c30-2019.md). All 60 items have all four artifacts, and the checks came out 60 agree, 0 disagree.
  - **All four misses had an `agree` check** (NR 2, NR 4, NR 7, NR 13), so the pipeline flagged none of them.
  - **NR 4, NR 7, NR 13: right value, recorded without its decimal point.** In each, the computed value equals the key, but the recorded digits drop the point. None of the 16 numerical responses on this form has a decimal point, against 5 of 18 on m301-2019 and p30-2013. The likely cause is the prompt: its `answers.json` format line shows `<digits>`, where the prompt those two forms read showed an example value with a decimal point. The line was changed so that the published prompt is the one Codex reads, and the pre-registration disclosed the change. The checks compared values, so they could not see a recording error.
  - **NR 2: a modelling miss.** In a calorimetry item, Codex used the total solution mass, including the dissolved solids, where the key's value corresponds to the mass of the water alone. The check summed heat capacities over the same total mass, so it shared the assumption and agreed.
  - **The precision rules.** None of the four misses is a failure they target: a rounding-route difference, or a check rebuilt from the recorded answer. The boundary rule fired on four numerical responses (NR 2, NR 4, NR 8, NR 16), each computed by two routes. NR 8 and NR 16 are correct; NR 2 and NR 4 missed for the reasons above, not rounding.
  - **For the next prompt version, not applied to this run:** say that a recorded numerical response keeps its decimal point, have the check compare the recorded string as well as the value, and have the check state its modelling assumptions so that a shared one is visible. These are now the "Recording and check rules" in `CODEX-QUEUE.md`, first tested on m301-2017.
- **m301-2017, Mathematics 30-1 Released Items 2017: pre-registered 2026-10-31, not yet run.** [`PREREG-m301-2017.md`](PREREG-m301-2017.md) tests the three recording and check rules above, with the same model and effort. It also records a grader fix: this form's key pages print a difficulty column that the c30-2019 parser misread, and the new self-check stops on any key that is not a letter or a number. The c30-2019 score is unchanged under the fixed parser.

## Results

Machine-scored items only (multiple choice and numerical response). Written responses were produced but not marked.

| Form | Worked by | Machine-scored | Correct | Misses |
|---|---|---|---|---|
| Mathematics 30-1 Practice Test 2022 | Claude Sonnet, one shot, no calculator | 32 | 30 | MC 11, NR 6 |
| Mathematics 30-1 Practice Test 2022 | Codex as Python calculator | 32 | 32 | none |
| Mathematics 30-1 Released Items 2019 (m301-2019) | Codex as Python calculator | 32 | 32 | none |
| Physics 30 Released Items 2013 (p30-2013) | Codex as Python calculator | 50 | 49 | NR 2 |
| Chemistry 30 Released Items 2019 (c30-2019), pre-registered | Codex as Python calculator | 60 | 56 | NR 2, NR 4, NR 7, NR 13 |

Caveats:

- The forms are public and may be in the models' training data. This is not a claim about unseen problems.
- Two scores are produced by scripts in this repository: Sonnet's 2022 score (`grade_machine.py` → `SCORE.md`) and the c30-2019 score (`grade_form.py` → `SCORE-c30-2019.md`). The other three Codex scores were computed by the director against the official keys outside this repository; that comparison is not included because it would reproduce the keys. You can repeat it by re-running the pipeline and comparing its answers with the key pages of the downloaded PDF (page indexes are in the protocols and `forms.json`).
- The two 2022 rows are not a fair head-to-head: Sonnet had no tools, while Codex wrote and ran Python and could view rendered figures.
- Written responses are not marked by anyone, human or model.
- One run per form, one sample per item. No error bars.
- Commit hashes mentioned in `SCORE.md` and `PROGRESS.md` refer to the private working history, which is not published (see "History").

See `RESULTS.md` for the same table on its own.

## Reproduce

Requirements: Python 3 with `pypdf`, `pymupdf`, `sympy`, `numpy`, `scipy`, `mpmath`, `matplotlib`. The launchers need Windows PowerShell and the Codex CLI; the scripts and grader do not.

1. Download the PDFs from the URLs in `PROTOCOL.md`, `PROTOCOL-<form-id>.md` or `forms.json`, and check each SHA-256, for example `certutil -hashfile file.pdf SHA256` or `sha256sum file.pdf`.
   For the queued forms, `py -3 prepare_forms.py` does this: it downloads into `sources/`, refuses a hash mismatch, and writes `answer-pass/<form-id>/questions-only.pdf` plus the formula sheet. For the 2022 form, save the PDF as `sources/math-30-1-practice-test-2022.pdf`. The 2022 questions extract (`answer-pass/questions-only.pdf`) is PDF page indexes 5 to 30 inclusive; its SHA-256 is in `PROTOCOL.md`.
2. Score a set of 2022 answers: `py -3 grade_machine.py [answers.json]` (reads the key from your local PDF; it never writes the key out). The Sonnet answers file is not published, so supply your own run (default path `runs/answers.json`, gitignored).
3. Per-item solver scripts are not published (see `runs/ITEMS-PRIVATE.md`). To reproduce, run the pipeline (step 4) against the official PDFs from alberta.ca and compare totals with the table above.
4. To run Codex yourself: `powershell -NoProfile -ExecutionPolicy Bypass -File .\Invoke-CodexLoop.ps1 -EndTime HH:mm` (see `CODEX-QUEUE.md`). Your results will differ from these.

`sources/`, `answer-pass/`, all PDFs, page renders and console logs are gitignored.

## What is not included

No Alberta Education PDFs, questions-only extracts, formula sheets or data booklets, page images, extracted question text, answer keys, sample solutions or scoring-guide text. Per-item answers, solver and check scripts, their outputs, derivations and sketches are not published either, because they encode item content.

Edits made for publication, compared with the original run:

- Local absolute paths in `runs/PROMPT.txt` (the 2022 Sonnet prompt) were made repo-relative.
- Per-item answers (`answers.json` files), item scripts and outputs, derivations (`worked.md`, `derivations.json`), item-specific build scripts and per-item hash audits were removed from the published tree (Alberta copyright). Aggregate scores are unchanged. The published history does not contain them either; see "History".
- One internal scheduling reference in `PROGRESS.md` was reworded.

## History

This repository starts from a fresh history. The working repository's history held material that should not be published (extracted question and data-booklet text for one form, local caches, local paths), so it was not carried over.

## Licence and copyright

This project's code, scripts and logs are released under the MIT License (see `LICENSE`), copyright 2026 Jon Hauk. Some scripts and outputs were generated by the AI tools credited above.

Alberta Education diploma examination content is not included in this repository. It remains © the Crown in Right of Alberta, all rights reserved, with reproduction permitted only to Alberta educators for non-profit educational use. Download it from alberta.ca yourself and use it under its own terms. The MIT License does not apply to it.

This project is not affiliated with or endorsed by Alberta Education.

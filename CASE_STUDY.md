# Case study: 123 Alberta diploma exam items, solved and cross-checked by an orchestrated AI pipeline

**In one line:** Jon Hauk designed and ran a verified AI pipeline that worked 123 released Alberta Grade 12 diploma exam items (Mathematics 30-1 and Physics 30). It finished on Oct 19, 2026, and its machine-scored results came to 113 of 114 correct.

**Mission:** Orchestrators aims to be the first superintelligence-reliant company: a small team of people willing to wade in and work directly with advanced AI, proving every result as they go. This case study is its first proof.

## Problem

Released diploma exams are a hard, public benchmark. Each item has one right answer, a published key, and no partial credit on machine-scored items. Jon wanted to know whether AI could do this work reliably, in a way a sceptical reader could audit. "The chatbot said so" was not good enough. The usual failure modes are known: models guess, grade their own work, and quietly revise answers. A believable result needed structure, not just a stronger model.

## Approach

Jon treats AI as a powerful calculator that he directs. He designed the pipeline, the cross-checks and the verification rules ([README](https://github.com/Jon-Hauk/curriculum-proof/blob/main/README.md)):

- **Director/answerer split.** A director (Grok, working with Jon) downloads each official PDF, checks its SHA-256 hash, cuts out a questions-only file and freezes a protocol before any answer exists ([PROTOCOL.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/PROTOCOL.md)). The answerer never sees the key, and it never grades itself.
- **Codex as calculator.** OpenAI's Codex CLI ran unattended through [`Invoke-CodexCalc.ps1`](https://github.com/Jon-Hauk/curriculum-proof/blob/main/Invoke-CodexCalc.ps1) and the queue supervisor [`Invoke-CodexLoop.ps1`](https://github.com/Jon-Hauk/curriculum-proof/blob/main/Invoke-CodexLoop.ps1). For every item, it had to write a Python calculation, the real output of running it, an independent check by a different route ending in `agree` or `disagree`, and a short derivation that quotes the output ([CODEX-QUEUE.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/CODEX-QUEUE.md)).
- **Hard rules.** Each item gets one attempt. A recorded answer is never replaced. A `disagree` is flagged for human review, not fixed by re-answering. The supervisor checks that every item has all four artifacts, logs any gaps in [PROGRESS.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/PROGRESS.md) and commits only locally.

## Results

Per-item answers and question setups were deliberately left out of the public repo because they would reproduce copyrighted Alberta material. The repo publishes scores and counts only.

| Form | Items worked | Checks | Machine-scored correct |
|---|---|---|---|
| Math 30-1 Practice Test 2022 | 35 | 35 agree | 32 / 32 |
| Math 30-1 Released Items 2019 | 35 | 34 agree, 1 disagree (resolved) | 32 / 32 |
| Physics 30 Released Items 2013 | 53 | 53 agree | 49 / 50 |
| **Total** | **123** | **122 agree, 1 disagree** | **113 / 114** |

Sources: [RESULTS.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/RESULTS.md), [PROGRESS.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/PROGRESS.md), and the `completion.json` files for [m301-2019](https://github.com/Jon-Hauk/curriculum-proof/blob/main/runs/codex/m301-2019/completion.json) and [p30-2013](https://github.com/Jon-Hauk/curriculum-proof/blob/main/runs/codex/p30-2013/completion.json). The pipeline is published in commits [e7e721d](https://github.com/Jon-Hauk/curriculum-proof/commit/e7e721df5fb3258125edc21c6d1d854fc5a7e6d1) and [1542e91](https://github.com/Jon-Hauk/curriculum-proof/commit/1542e9130d5ca54405f0682792a1154b3c87f0fe).

- **Time:** The run took about 40 minutes of logged agent work. The progress log shows one block of 18 minutes or less and passes of 12 and 12.8 minutes, roughly 40–45 minutes in all. Jon's own estimate is that working the same items alone would have taken him about 3 years of study.
- **The one miss (Physics NR 2)** was a rounding-boundary problem: an SI-unit route rounded differently from the data booklet's eV·s constant. Jon added precision rules afterwards. They have not yet been tested on a new form.
- **The one disagreement (Math 2019 MC 5)** came from the check itself, which counted one printed stroke three times. An independent review agreed with the recorded answer, so the answer stayed as recorded.
- **Baseline:** Claude Sonnet, given one shot with no tools, scored 30/32 on the 2022 form. The repo notes this is not a fair head-to-head comparison.

Caveats from the repo: the forms are public and may be in the models' training data. There was one run per form. Written responses were not marked. The Codex scores are director-verified against the official keys; the keys are not published in the repo.

## Why it matters

The model was not the main advantage. The orchestration was. Frozen protocols, separated roles, an independent check on every item and an append-only rule for answers turned a fast but unreliable tool into results that can be audited. Both anomalies were caught, diagnosed and logged openly, without being quietly fixed. Working alone, Jon would have to supply both the speed and the rigour himself. Orchestration plus verification gives him both and leaves an evidence trail.

## What Orchestrators offers (tentative)

Orchestrators is the working name for a company Jon is planning. It would apply the same pattern of orchestrated, verified AI work to a few areas:

- security engineering;
- general engineering and automation;
- delivering software;
- possibly supporting AI-safety and "superintelligence-friendly" projects with hardware.

Every engagement would use clear protocols, independent cross-checks and a human-reviewed audit trail. The scope is still being defined.

## Contact

GitHub: [github.com/Jon-Hauk](https://github.com/Jon-Hauk)

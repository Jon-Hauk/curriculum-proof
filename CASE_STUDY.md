# Case study: 123 Alberta diploma exam items, worked and cross-checked by an orchestrated AI pipeline

**In one line:** Jon Hauk designed and ran a cross-checked AI pipeline that worked 123 items from Alberta Grade 12 diploma practice and released-item forms (Mathematics 30-1 and Physics 30). It finished on Oct 19, 2026. Of the 114 multiple-choice and numerical-response items, 113 were correct when the director scored them against the official keys.

**Mission:** Orchestrators is a planned company: a small team of people willing to wade in and work directly with advanced AI, proving every result as they go. This case study is its first worked example.

## Problem

Released diploma exam items are a clean, public benchmark. Each item has one right answer, a published key, and no partial credit on machine-scored items. Jon wanted to know whether AI could do this work reliably, in a way a sceptical reader could reproduce. "The chatbot said so" was not good enough. The usual failure modes are known: models guess, grade their own work, and quietly revise answers. A believable result needed structure, not just a stronger model.

## Approach

Jon treats AI as a powerful calculator that he directs. He designed the pipeline, the cross-checks and the verification rules ([README](https://github.com/Jon-Hauk/curriculum-proof/blob/main/README.md)):

- **Director/answerer split.** A director (Grok, working with Jon) downloads each official PDF, checks its SHA-256 hash, cuts out a questions-only file and freezes a protocol before any answer exists ([PROTOCOL.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/PROTOCOL.md)). The answerer never sees the key, and it never grades itself.
- **Codex as calculator.** OpenAI's Codex CLI worked the items with no human input per item: [`Invoke-CodexCalc.ps1`](https://github.com/Jon-Hauk/curriculum-proof/blob/main/Invoke-CodexCalc.ps1) launched it on the 2022 form, and the queue supervisor [`Invoke-CodexLoop.ps1`](https://github.com/Jon-Hauk/curriculum-proof/blob/main/Invoke-CodexLoop.ps1) ran the other two. The supervisor was replaced partway through, and one pass was accounted for by hand; both are logged. For every item, Codex had to write a Python calculation, the real output of running it, a check that re-derives the value and ends in `agree` or `disagree`, and a short derivation that quotes the output ([CODEX-JOB.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/CODEX-JOB.md) for 2022). On the two queued forms, the check also had to take a different route ([CODEX-QUEUE.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/CODEX-QUEUE.md)).
- **Hard rules.** Each item gets one attempt. A recorded answer is never replaced. A `disagree` is flagged for human review, not fixed by re-answering. The supervisor checks that every item has all four artifacts, logs any gaps in [PROGRESS.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/PROGRESS.md) and commits only locally.

## Results

Per-item answers and question setups were deliberately left out of the public repo because they would reproduce copyrighted Alberta material. The repo publishes scores and counts only.

| Form | Items worked | Checks | Machine-scored correct |
|---|---|---|---|
| Math 30-1 Practice Test 2022 | 35 | 35 agree | 32 / 32 |
| Math 30-1 Released Items 2019 | 35 | 34 agree, 1 disagree (false alarm) | 32 / 32 |
| Physics 30 Released Items 2013 | 53 | 53 agree (1 false agree) | 49 / 50 |
| **Total** | **123** | **122 agree, 1 disagree** | **113 / 114** |

Sources: [RESULTS.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/RESULTS.md), [PROGRESS.md](https://github.com/Jon-Hauk/curriculum-proof/blob/main/PROGRESS.md), and the `completion.json` files for [m301-2019](https://github.com/Jon-Hauk/curriculum-proof/blob/main/runs/codex/m301-2019/completion.json) and [p30-2013](https://github.com/Jon-Hauk/curriculum-proof/blob/main/runs/codex/p30-2013/completion.json). The pipeline is published in commit [e7e721d](https://github.com/Jon-Hauk/curriculum-proof/commit/e7e721df5fb3258125edc21c6d1d854fc5a7e6d1); [1542e91](https://github.com/Jon-Hauk/curriculum-proof/commit/1542e9130d5ca54405f0682792a1154b3c87f0fe) corrected the README.

- **Time:** Codex's logged work came to under 43 minutes: one block of at most 18 minutes for the 2022 form, then passes of 12 and 12.8 minutes for the other two. That excludes the director's setup and the human review afterwards. Jon's own estimate is that learning the material well enough to work these items alone would take him about 3 years of study.
- **The one miss (Physics NR 2)** was a rounding-boundary problem: an SI-unit route rounded differently from the data booklet's eV·s constant. The check said `agree` anyway, because it rebuilt its input from the recorded answer instead of re-deriving the value. The pipeline did not catch this miss; scoring against the key did. Precision rules were added afterwards: use the booklet constant in the units the answer needs, compute both routes near a rounding boundary, and never let a check rebuild its inputs from the recorded answer. They have not yet been tested on a new form.
- **The one disagreement (Math 2019 MC 5)** came from the check itself, which counted one printed stroke three times: a false alarm. An independent review agreed with the recorded answer, so the answer stayed as recorded.
- **Baseline:** Claude Sonnet, given one shot with no tools, scored 30/32 on the 2022 form. The repo notes this is not a fair head-to-head comparison.

Caveats from the repo: the forms are public and may be in the models' training data. There was one run per form. Written responses were not marked. Only Sonnet's 30/32 is scored by a script in the repo (`grade_machine.py` → `SCORE.md`). The three Codex scores were computed by the director against the official keys outside the repo, because publishing that comparison would reproduce the keys.

## Why it matters

The score is not the point: a bare model, given one shot with no tools, already got 30 of 32 on the 2022 form. What the orchestration added is a result someone else can reproduce. Frozen protocols, separated roles, a check on every item and an append-only rule for answers mean every answer comes from a script that actually ran, and the whole run can be repeated from the official PDFs. The record also shows where the checking failed. The check went wrong once in each direction, a false alarm on Math MC 5 and a false agree on Physics NR 2. Both are logged openly, neither answer was quietly changed, and the second produced a new rule. Working alone, Jon would have to supply both the speed and the rigour himself. Orchestration plus verification gives him both and leaves an evidence trail.

## What Orchestrators offers (tentative)

Orchestrators is the working name for a company Jon is planning. It would apply the same pattern of orchestrated, verified AI work to a few areas:

- security engineering;
- general engineering and automation;
- delivering software;
- possibly supporting AI-safety and "superintelligence-friendly" projects with hardware;
- automated, verified research using spare compute.

Every engagement would use clear protocols, independent cross-checks and a human-reviewed audit trail. The scope is still being defined.

## Contact

GitHub: [github.com/Jon-Hauk](https://github.com/Jon-Hauk)

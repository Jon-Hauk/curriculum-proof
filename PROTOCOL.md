# Protocol — Mathematics 30-1 practice test, 2022

Frozen before the answer pass. A later edit is a new version, not the same evidence.

## Claim

This run measures one pinned system on the machine-scored items of one named public form: the Alberta Education Mathematics 30-1 Practice Test, Diploma Examinations Program 2022.

The score file reports how many of those items matched the published key, and which item ids missed. It does not interpret the score as unseen-problem performance, calculator-present performance, or a general claim about intelligence.

## Non-claim

This is not a claim about problems that have never been published. The form is public and may already be in a model's training data. It is not a claim about Chemistry 30, Biology 30, Science 30, Mathematics 31, Mathematics 30-2, Mathematics 30-3, or Physics 30. Physics 30 is a later run, not this one. Mathematics 10C, Mathematics 20-1, and Science 10 are an unscored map, not this score. It is not a claim that the answerer had the approved calculator or formula sheet a student is given.

## Item set

- Document: Mathematics 30-1 Practice Test, Diploma Examinations Program 2022, Alberta Education, Provincial Assessment.
- URL: https://www.alberta.ca/system/files/custom_downloaded_images/edc-mathematics-30-1-practice-test.pdf
- SHA-256 of the downloaded file: `EF300AB629BD24D41974A87146B2AC71EE57BE0C6B60CDB668D8EF510DD02447`
- Size: 1,147,165 bytes. 46 PDF pages.
- Questions given to the answerer: PDF page indexes 5 through 30 inclusive (printed pages 2 through 27). 26 pages. SHA-256 of that extract: `E07FBBC0F893AD5270E11EA2D7268784D167F87942E4A5D4BB7101D87BAC2FF4`
- Published key used by the grader: PDF page index 31 (printed page 28). The key is not copied into this repository.
- Sample solutions start at PDF page index 32. They are not given to the answerer and are not given to the written-response scorer.
- This form, as printed in its own answer key, is 24 multiple-choice, 8 numerical-response, and 3 written-response items. The claim for the first score is the 32 machine-scored items. Written responses are stored and are not given a mark in this version.

## Licence

The PDF says: Copyright 2022, the Crown in Right of Alberta, all rights reserved. Special permission to reproduce parts of it is granted to Alberta educators only, for educational non-profit use, and only for parts that do not contain excerpted material.

This repository does not contain the PDF, the question stems, the figures, the official key, the sample solutions, or the scoring-guide text. Local copies stay in `sources/`, which is gitignored. A stranger re-runs the check by downloading the same URL, confirming the SHA-256, and running `grade_machine.py` against `runs/answers.json`.

## System under test

- Director: Grok 4.7, in the session that wrote this file. Grok retrieved the published key while locating the key page, before any answer existed. Grok is disqualified as the answerer on this form.
- Answerer: Claude Sonnet, Claude Code `--safe-mode`, one print-mode call. Tools: Read and Write. No web, no shell, no Python, no calculator. The prompt contains the questions PDF path and the output schema. It does not contain the key, the sample solutions, or the rubric.
- Decoding: one sample. The vendor default for that call. Not best-of-k.
- Attempt policy: one answer per item. No second call after an answer file exists. A crash that writes no answer file may be repeated once, and the repeat is noted in the score file.
- Machine-scored grader: `grade_machine.py`. It parses the key from the local PDF and compares. It is not a model. It does not rewrite answers.
- Written-response grader: not used in this version. No human spot-check was done.
- Orchestration: no debate, no second model revising answers, no edit of this protocol after the answer file exists.

## What the score file reports

- The protocol version (this file's git commit).
- Counts correct and total for the 32 machine-scored items.
- The item ids that missed.
- A statement that written responses were not marked.
- It does not reprint the official key.

The answerer's choices are `runs/answers.json`. That file is the system's output. It is committed after this protocol, in a later commit.

## One-shot rule

Prompts, the answerer, the questions extract, and this protocol are fixed before `runs/answers.json` exists. No prompt edit, no change of model, and no manual rewrite of an answer after the run starts. Any later change is a new version.

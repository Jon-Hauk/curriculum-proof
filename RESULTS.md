# Results

Machine-scored items only (multiple choice and numerical response). Written responses were produced but not marked.

| Form | Worked by | Machine-scored | Correct | Misses |
|---|---|---|---|---|
| Mathematics 30-1 Practice Test 2022 | Claude Sonnet, one shot, no calculator | 32 | 30 | MC 11, NR 6 |
| Mathematics 30-1 Practice Test 2022 | OpenAI Codex CLI (`gpt-6-astra`) as Python calculator | 32 | 32 | none |
| Mathematics 30-1 Released Items 2019 (m301-2019) | Codex | 32 | 32 | none |
| Physics 30 Released Items 2013 (p30-2013) | Codex | 50 | 49 | NR 2 |

- Sonnet's 2022 score is produced by `grade_machine.py` and recorded in `SCORE.md`. The Codex scores were computed by the director (Grok, with Jon) against the official keys outside this repository, so the keys are not reproduced here.
- p30-2013 NR 2: the value landed on a rounding boundary, and converting through SI constants rounded differently from using the data booklet's constant in eV·s. Rules added afterwards in `CODEX-QUEUE.md` (untested on a new form so far).
- m301-2019 MC 5: the check said `disagree`. It was traced to a raster check counting one stroke three times; an independent Veridian review (via Hermes) agreed with the recorded answer. Logged in `PROGRESS.md`.
- Per-item answers and item scripts are kept privately (Alberta copyright); see `runs/ITEMS-PRIVATE.md`.
- The forms are public and may be in training data; this is not an unseen-problem result. One run per form, no error bars. The two 2022 rows used different tools and are not a fair head-to-head.

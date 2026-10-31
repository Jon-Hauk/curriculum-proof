# Pre-registration: c30-2019 (Chemistry 30 Released Items 2019)

Written 2026-10-31, before any Codex answer for this form exists. It is published to [github.com/Jon-Hauk/curriculum-proof](https://github.com/Jon-Hauk/curriculum-proof) before the run starts, so the commit that adds this file is the timestamp. A later edit is a new version; the run is judged against this one.

## Why this run

The published runs ended with one miss, p30-2013 NR 2. Its value sat on a rounding boundary, and its check said `agree` because it rebuilt the input from the recorded answer. Three precision rules were added to `CODEX-QUEUE.md` afterwards and have not been tested. This run is their first test, on a subject the pipeline has not worked before.

## What will run

- **Form:** c30-2019, Chemistry 30 Released Items 2019 (November 2018 exam). Source, extract and data-booklet hashes are in `PROTOCOL-c30-2019.md`. 60 machine-scored items: MC 1-44 and NR 1-16. No written response.
- **Answerer:** OpenAI Codex CLI (0.165.0 when this was written; each pass log records the version that ran), model `gpt-6-astra`, reasoning effort `xhigh`. That is the model and effort the published runs used; the supervisor pins them for this run instead of reading the local config.
- **Prompt:** `CODEX-QUEUE.md` exactly as in this commit. Compared with the prompt the published m301-2019 and p30-2013 passes read, it adds the precision rules, and its `answers.json` format line shows placeholders instead of example values.
- **Command,** from the working repository root, with any end time that leaves at least two hours:

  ```
  powershell -NoProfile -ExecutionPolicy Bypass -File .\Invoke-CodexLoop.ps1 -TargetForms c30-2019 -Model gpt-6-astra -ReasoningEffort xhigh -EndTime HH:mm
  ```

- Only this form is targeted. Other prepared forms are not run under this pre-registration.

## Frozen files

SHA-256 of each file as stored in this commit (LF line endings, as GitHub serves it):

| File | SHA-256 |
|---|---|
| `CODEX-QUEUE.md` | `1420eb30a544703b06e7996705c971fb480828fc774138784df849caf304dce6` |
| `Invoke-CodexLoop.ps1` | `d911f203fda372567198cef5f02bc6192deda4a00eec723f6f400f74f702551f` |
| `grade_form.py` | `fbd105bea18ff47bfb23a02f58d0323abfb70f88c364ebc1751c8c439b81b6f9` |
| `PROTOCOL-c30-2019.md` | `b8be175a94c0effce22463eec9b81643749887cd7806e50a9cfe41f531c970ac` |
| `forms.json` | `b88c7e781b6dd22145fbfe612aeefa6772269ad1196fb1e09abff57ff1b64487` |
| `prepare_forms.py` | `717f1e617e3eaf3822d119374a56da8595ba8eda3c4eb0463d707984f0fb7f46` |

## Rules for the run

- One run, one attempt per item. A recorded answer is never replaced, and the form is not re-run whatever the score.
- A pass cut off by a usage limit or the slot end is continued by the next pass, which keeps every existing answer and adds only what is missing. A form reopened once for missing artifacts is handled the same way. Both are the same run.
- If the run cannot start (for example, the model is unavailable) and no answer has been written, it may be launched again under this pre-registration. Once any answer exists, that run is the run.
- A `disagree` check is flagged for review, not resolved by re-answering.

## Scoring

- After the form is retired: `py -3 grade_form.py c30-2019`. It reads the key from the item-information pages of the local PDF at grade time and writes `SCORE-c30-2019.md` with the total and the miss ids only.
- The matching rule is the one in `grade_form.py`'s docstring: MC letters must match; NR digits must match after removing whitespace; a key marked "(any order)" accepts the digits in any order; every value a key lists is accepted; a blank answer is a miss.
- The grader is not Codex. Before the run it was tested against the key pages for structure only: it parses 60 items and their ids match `forms.json`. No key value was printed or recorded.

## Published whatever the result

- `SCORE-c30-2019.md`: machine-scored correct out of 60, and the miss ids.
- The `completion.json` counts: items, answered, checks agree, checks disagree.
- For each miss: whether its check said `agree` or `disagree`, and a one-line cause with no answer values.
- For each `disagree`: how it was resolved.
- For each miss, whether it is one of the two failures the precision rules target: a rounding-route difference, or a check that rebuilt its input from the recorded answer. Either counts against the rules.
- The number of items whose worked derivation notes a rounding boundary, which shows whether the boundary rule was exercised at all.
- Logged Codex time, from `PROGRESS.md`.
- A new row in `RESULTS.md` and the README results table.

## What this run cannot show

- The form is public, and the November 2018 exam may be in the model's training data.
- One run and one sample per item, so no error bars.
- A clean score fits the rules working but does not prove it. If no item lands near a rounding boundary, the run shows only that the rules did no harm on this form.

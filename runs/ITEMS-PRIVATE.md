# Per-item artifacts are kept privately

Per-item solver scripts (`items/<ID>.py`), their check scripts, saved outputs, worked derivations, sketches and per-item answer files (`answers.json`) are kept privately and are not part of this repository. They encode the copyrighted item content (numeric givens, setups and option values) and the computed answers, which together would reproduce Alberta Education's released items and answer keys (Crown in Right of Alberta, all rights reserved).

Aggregate results are in `RESULTS.md`, `SCORE.md`, `PROGRESS.md` and the per-form `completion.json` files.

To reproduce the results, download the official PDFs from alberta.ca (URLs and SHA-256 values in `PROTOCOL.md`, `PROTOCOL-<form-id>.md` and `forms.json`), prepare the forms with `prepare_forms.py`, run the pipeline (`Invoke-CodexLoop.ps1`, see `CODEX-QUEUE.md`), and score with `grade_machine.py` or against the key pages of your local PDFs.

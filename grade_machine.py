"""Compare runs/answers.json to the key printed in the local Alberta PDF.

The key is read from the PDF at grade time. It is not written into SCORE.md.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
PDF = ROOT / "sources" / "math-30-1-practice-test-2022.pdf"
ANSWERS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "runs" / "answers.json"  # private, not published
SCORE = ROOT / "SCORE.md"
KEY_PAGE = 31
EXPECTED = 32


def load_key(pdf: Path) -> dict[str, set[str]]:
    text = PdfReader(str(pdf)).pages[KEY_PAGE].extract_text() or ""
    key: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = re.match(r"^(NR|MC)\s+(\d+)\s+(\S+)$", line.strip())
        if not match:
            continue
        item_id = f"{match.group(1)} {match.group(2)}"
        raw = match.group(3).strip()
        key[item_id] = {part for part in raw.split("/") if part}
    if len(key) != EXPECTED:
        raise SystemExit(f"key page yielded {len(key)} machine-scored items, expected {EXPECTED}")
    return key


def norm(value: str) -> str:
    return re.sub(r"\s+", "", value).upper().rstrip(".")


def matches(item_id: str, given: str, accepted: set[str]) -> bool:
    got = norm(given)
    if item_id.startswith("MC"):
        return got in {norm(a) for a in accepted}
    return got in {norm(a) for a in accepted}


def protocol_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> None:
    if not PDF.is_file():
        raise SystemExit(f"missing {PDF}")
    if not ANSWERS.is_file():
        raise SystemExit(f"missing {ANSWERS}")
    key = load_key(PDF)
    payload = json.loads(ANSWERS.read_text(encoding="utf-8"))
    rows = payload["items"] if isinstance(payload, dict) else payload
    by_id = {str(row["id"]).strip(): str(row["answer"]) for row in rows}
    misses: list[str] = []
    correct = 0
    for item_id in sorted(key, key=lambda s: (s.split()[0], int(s.split()[1]))):
        if item_id not in by_id or by_id[item_id].strip() == "":
            misses.append(f"{item_id} (no answer)")
            continue
        if matches(item_id, by_id[item_id], key[item_id]):
            correct += 1
        else:
            misses.append(item_id)
    extra = sorted(set(by_id) - set(key) - {f"WR {n}" for n in range(1, 4)})
    miss_text = ", ".join(misses) if misses else "none"
    extra_text = ", ".join(extra) if extra else "none"
    SCORE.write_text(
        "\n".join(
            [
                "# Score — Mathematics 30-1 practice test, 2022",
                "",
                f"Protocol commit graded against: `{protocol_commit()}`",
                "",
                f"Machine-scored: {correct}/{EXPECTED}.",
                f"Miss ids: {miss_text}.",
                f"Unexpected ids ignored: {extra_text}.",
                "",
                "Written responses are not marked. Per-item answers are kept privately.",
                "The official key is not reprinted here.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"{correct}/{EXPECTED}")
    print("misses:", miss_text)


if __name__ == "__main__":
    main()

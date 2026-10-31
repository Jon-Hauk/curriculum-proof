"""Compare runs/codex/<form-id>/answers.json to the key printed in the local Alberta PDF.

Usage:
    py -3 grade_form.py <form-id>               score the form, write SCORE-<form-id>.md
    py -3 grade_form.py <form-id> --check-key   parse the key only, print counts

The key is read from the PDF's item-information pages (forms.json `key_pages`)
at grade time. It is not written into SCORE-<form-id>.md or printed.

Matching rule, fixed before any answer for a pre-registered form exists:
- MC: the recorded letter equals the key letter.
- NR: the recorded digits equal an accepted value after removing whitespace.
  A key marked "(any order)" accepts any ordering of the same digits. A key
  listing several values ("a, b" or a "*(see below)" footnote) accepts each.
- Blank or missing answers are misses. WR items are not scored.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
FORMS = ROOT / "forms.json"
ROW = re.compile(r"^(MC|NR)\s*(\d+)\s+(.*)$")
DIFFICULTY = re.compile(r"^\d+(\.\d+)?%\s*")
VALUE = re.compile(r"^(-?\d*\.?\d+)\s*(,)?\s*")
FOOTNOTE = re.compile(r"^\*NR\s*(\d+):\s*(.*)$")
LIST_TAIL = re.compile(r"^[\d.,\s]+$")


@dataclass
class Key:
    accepted: set[str]
    any_order: bool = False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def norm(value: str) -> str:
    return re.sub(r"\s+", "", value).upper().rstrip(".")


def split_values(text: str) -> set[str]:
    return {norm(part) for part in text.split(",") if norm(part)}


def leading_values(text: str) -> tuple[list[str], str]:
    """Split "12.5, 13 (any order) RF 1" into (["12.5", "13"], "(any order) RF 1")."""
    values: list[str] = []
    rest = text.strip()
    while match := VALUE.match(rest):
        values.append(match.group(1))
        rest = rest[match.end() :]
        if not match.group(2):
            break
    return values, rest


def expected_ids(items: str) -> list[str]:
    ids: list[str] = []
    for kind, first, last in re.findall(r"\b(MC|NR)\s+(\d+)-(\d+)", items):
        ids += [f"{kind} {n}" for n in range(int(first), int(last) + 1)]
    return ids


def load_form(form_id: str) -> dict:
    forms = json.loads(FORMS.read_text(encoding="utf-8"))["forms"]
    for form in forms:
        if form["id"] == form_id:
            return form
    raise SystemExit(f"{form_id} is not in forms.json")


def load_key(pdf: Path, pages: list[int], ids: list[str]) -> dict[str, Key]:
    reader = PdfReader(str(pdf))
    lines: list[str] = []
    for page in pages:
        lines += [line.strip() for line in (reader.pages[page].extract_text() or "").splitlines()]
    key: dict[str, Key] = {}
    footnotes: dict[str, str] = {}
    pending: set[str] = set()
    for index, line in enumerate(lines):
        note = FOOTNOTE.match(line)
        if note:
            text = note.group(2)
            for tail in lines[index + 1 :]:
                if not LIST_TAIL.match(tail):
                    break
                text += " " + tail
            footnotes[f"NR {note.group(1)}"] = text
            continue
        row = ROW.match(line)
        if not row:
            continue
        item_id = f"{row.group(1)} {row.group(2)}"
        # some forms print a difficulty percentage before the key; a value list
        # ending in a comma continues on the next line
        raw = DIFFICULTY.sub("", row.group(3).strip())
        for tail in lines[index + 1 :]:
            if not raw.rstrip().endswith(","):
                break
            raw += " " + tail
        if item_id.startswith("MC"):
            key[item_id] = Key({norm(raw.split()[0])})
        elif raw.startswith("*"):
            pending.add(item_id)
        else:
            values, rest = leading_values(raw)
            key[item_id] = Key({norm(v) for v in values}, rest.startswith("(any order)"))
    for item_id in pending:
        if item_id not in footnotes:
            raise SystemExit(f"{item_id} points to a footnote that was not found")
        key[item_id] = Key(split_values(footnotes[item_id]))
    if sorted(key) != sorted(ids) or any(not k.accepted for k in key.values()):
        raise SystemExit(f"key pages yielded {len(key)} usable items, expected {len(ids)}")
    # a layout the parser does not know shows up here, not as a wrong score
    for item_id, k in key.items():
        if item_id.startswith("MC"):
            ok = len(k.accepted) == 1 and next(iter(k.accepted)) in {"A", "B", "C", "D"}
        else:
            ok = all(re.fullmatch(r"-?\d*\.?\d+", v) for v in k.accepted)
        if not ok:
            raise SystemExit(f"{item_id}: key value is not a letter A-D or a number; layout not understood")
    return key


def matches(given: str, key: Key) -> bool:
    got = norm(given)
    if key.any_order:
        return sorted(got) in [sorted(a) for a in key.accepted]
    return got in key.accepted


def head_commit() -> str:
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
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    form = load_form(sys.argv[1])
    pdf = ROOT / "sources" / form["url"].rsplit("/", 1)[-1]
    if not pdf.is_file():
        raise SystemExit(f"missing {pdf}")
    if sha256(pdf) != form["sha256"].upper():
        raise SystemExit(f"{pdf.name} does not match the SHA-256 in forms.json")
    ids = expected_ids(form["items"])
    key = load_key(pdf, form["key_pages"], ids)
    if "--check-key" in sys.argv[2:]:
        mc = sum(1 for i in key if i.startswith("MC"))
        print(f"key parsed: {len(key)} items ({mc} MC, {len(key) - mc} NR), id set matches forms.json")
        return
    answers = ROOT / "runs" / "codex" / form["id"] / "answers.json"
    if not answers.is_file():
        raise SystemExit(f"missing {answers}")
    payload = json.loads(answers.read_text(encoding="utf-8"))
    rows = payload["items"] if isinstance(payload, dict) else payload
    by_id = {str(row["id"]).strip(): str(row["answer"]) for row in rows}
    misses: list[str] = []
    correct = 0
    for item_id in ids:
        if item_id not in by_id or by_id[item_id].strip() == "":
            misses.append(f"{item_id} (no answer)")
        elif matches(by_id[item_id], key[item_id]):
            correct += 1
        else:
            misses.append(item_id)
    extra = sorted(i for i in set(by_id) - set(key) if not i.startswith("WR"))
    miss_text = ", ".join(misses) if misses else "none"
    extra_text = ", ".join(extra) if extra else "none"
    score = ROOT / f"SCORE-{form['id']}.md"
    score.write_text(
        "\n".join(
            [
                f"# Score — {form['title']}",
                "",
                f"Graded by `grade_form.py` at commit `{head_commit()}`.",
                f"Answers file SHA-256: `{sha256(answers)}`",
                "",
                f"Machine-scored: {correct}/{len(ids)}.",
                f"Miss ids: {miss_text}.",
                f"Unexpected ids ignored: {extra_text}.",
                "",
                "Per-item answers are kept privately. The official key is not reprinted here.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"{correct}/{len(ids)}")
    print("misses:", miss_text)


if __name__ == "__main__":
    main()

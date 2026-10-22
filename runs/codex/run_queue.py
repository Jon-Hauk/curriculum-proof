"""Run saved per-item code once; preserve stdout/stderr and existing answers."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
IDS = [f"{kind} {i}" for kind, count in [("MC", 24), ("NR", 8), ("WR", 3)] for i in range(1, count + 1)]

def run_one(item, check=False):
    stem = item.replace(" ", "-") + ("-check" if check else "")
    script, output = BASE / "items" / f"{stem}.py", BASE / "items" / f"{stem}.out"
    if output.exists():
        print(f"PRESERVED {output.name}", flush=True)
        return
    if not script.exists():
        raise FileNotFoundError(script)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        process = subprocess.run([sys.executable, "-X", "utf8", str(script)], stdout=stream, stderr=subprocess.STDOUT, cwd=BASE.parents[1])
    print(f"{stem}: exit {process.returncode}", flush=True)
    if process.returncode:
        raise RuntimeError(f"Execution failed; preserved {output}. No retry performed.")

def record_answers():
    path = BASE / "answers.json"
    existing = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {"items": []}
    seen = {record["id"] for record in existing["items"]}
    for item in IDS:
        if item in seen:
            continue
        output = BASE / "items" / (item.replace(" ", "-") + ".out")
        records = [json.loads(line.removeprefix("ANSWER_JSON ")) for line in output.read_text(encoding="utf-8").splitlines() if line.startswith("ANSWER_JSON ")]
        if len(records) != 1 or records[0]["id"] != item:
            raise ValueError(f"Missing or ambiguous recorded output: {item}")
        existing["items"].append(records[0])
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8-sig"))
        assert existing["items"][:len(old["items"])] == old["items"]
        if existing == old:
            print("All existing answers preserved; nothing to add.")
            return
        # Append-only in content: existing entries remain byte-for-byte equivalent JSON values.
        path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(existing, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    print(f"Recorded {len(existing['items'])} answers.")

if __name__ == "__main__":
    print("UTC", datetime.now(timezone.utc).isoformat(), flush=True)
    mode = sys.argv[1]
    if mode == "record":
        record_answers()
    else:
        selected = sys.argv[2:] or IDS
        prior = BASE / "answers.json"
        already = {v["id"] for v in json.loads(prior.read_text(encoding="utf-8-sig"))["items"]} if prior.exists() else set()
        for item in selected:
            if mode == "attempt" and item in already:
                print(f"PRESERVED existing answer {item}")
                continue
            run_one(item, check=mode == "check")

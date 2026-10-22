"""Download official Alberta Education released-item PDFs into sources/ (gitignored),
verify them, and cut questions-only extracts into answer-pass/<form-id>/ (gitignored).
Key tables, sample solutions and scoring guides are never copied. Page indexes are 0-based."""
import hashlib, json, os, sys, urllib.request, datetime
from pypdf import PdfReader, PdfWriter
ROOT = os.path.dirname(os.path.abspath(__file__))
B = "https://www.alberta.ca/system/files/"
FORMULA = {
 "m301": (B+"edc-diploma-math-30-1-formula-sheet.pdf", "6d65e98d0c3da19b620abb7eb3588146f240a817448b761a11708e59eb623a46"),
 "m302": (B+"edc-diploma-math-30-2-formula-sheet.pdf", "40b0ec794880072cab915d8ee3e04d4c3f91b1269e936fa9f76eb3dcdd3a3797"),
 "c30-": (B+"custom_downloaded_images/edc-chemistry30-data-booklet.pdf", "f4ece0b308774ec2a16a79f8be5f8eb4c9aed14e881f0425db33f17e106c7ae6"),
 "p30-": (B+"custom_downloaded_images/edc-physics30-data-booklet.pdf", "5651387018f0b268a266db8927dd1554647ed9f416cc3c0ef4cc8fea1667e710"),
}
# id, title, url-path, sha256, q_first, q_last, excluded key pages (item information), first excluded solution page or None, items, est minutes
FORMS = [
 ("m301-2019","Mathematics 30-1 Released Items 2019 (January 2019 Form 1)","custom_downloaded_images/ed-diploma-exam-math-30-1-released-Items-2019.pdf","b5a961f87847eff1d531a602d8847f1cf929da4164fe7bd1d0d1a48f2a6314dc",8,32,[5,6,7],33,"MC 1-24, NR 1-8, WR 1-3",25),
 ("m302-2021aug","Mathematics 30-2 Released Items August 2021","edc-mathematics-30-2-released-items-august-2021.pdf","7804b1ddf66e4d02eb6c964ae65fa4cbd79c3f39c17f20002b43342f1cc832c7",8,31,[5,6,7],32,"MC 1-24, NR 1-8, WR 1-2",22),
 ("m301-2017","Mathematics 30-1 Released Items 2017 (April 2017)","custom_downloaded_images/edc-math30-1-released-items-2017.pdf","dbe0dbcfa32a4fb1dfe7f9546f42494cd3075d4638648c7fc697d7e3c20104c4",7,29,[5,6],None,"MC 1-28, NR 1-12",25),
 ("m302-2019apr","Mathematics 30-2 Released Items April 2019","edc-mathematics-30-2-released-items-april2019.pdf","35d8185c9d1b6849e1ee19980e66d5ea0b8efeba18a37d033d393650304b6ef3",8,32,[5,6,7],33,"MC 1-24, NR 1-8, WR 1-2",22),
 ("m301-2016","Mathematics 30-1 Released Items 2016 (April 2016)","custom_downloaded_images/edc-math30-1-released-items-2016.pdf","1bd63928300e714a7aac11d26fc9c945499b15f8e07de3fa71e06c06a07141cb",7,30,[5,6],None,"MC 1-28, NR 1-12",25),
 ("m302-2019jan","Mathematics 30-2 Released Items January 2019","custom_downloaded_images/ed-mathematics-30-2-released-materials-2019.pdf","a77556f513d889089931dcdc5a7b7b6eea49a657d598abe1d39d2b0971abafc0",8,32,[5,6,7],33,"MC 1-24, NR 1-8, WR 1-2",22),
 ("m302-2016","Mathematics 30-2 Released Items 2016 (August 2013 exam)","custom_downloaded_images/edc-math30-2-released-items-2016.pdf","aee002759401b39acf1a717325ce6e037744a1ba9e46b1ffe5113a901b68a32f",7,30,[5,6],None,"MC 1-28, NR 1-12",22),
 ("m302-2013","Mathematics 30-2 Released Items 2013 (January 2013)","custom_downloaded_images/edc-math30-2-released-items-2013.pdf","6e2968a55367dcd079b79b74f83254085156fb8ea635bdfb44085a4df4eca1dc",7,29,[5,6],None,"MC 1-28, NR 1-12",22),
 ("c30-2019","Chemistry 30 Released Items 2019 (November 2018 exam)","custom_downloaded_images/ed-chemistry-30-released-items-2019.pdf","8ccacf95ea37efd16316ea2dd90a6c6e94009f2853fadc59583160b08a82bc7f",7,38,[5,6],None,"MC 1-44, NR 1-16, ids as printed",30),
 ("p30-2013","Physics 30 Released Items 2013 (June 2009 exam)","custom_downloaded_images/edc-physics30-released-items-2013.pdf","22ee87b9ffbbca5599b11e06d596be85b7eded155c4b4993694c2c168b1f1f43",6,38,[5],39,"MC and NR ids as printed, WR 1-3",30),
 ("m301-2014","Mathematics 30-1 Released Items 2014 (Nov 2012 and Jan 2014 items)","custom_downloaded_images/edc-math30-1-released-items-2014.pdf","f96c9ced4061137159cfd365141b1bbb46f58989ba3cd46d9d2c75a4dd6e2d31",6,15,[5],None,"14 machine-scored items, ids as printed",16),
]
BAD = ("Diff.*", "Scoring Guide for", "Sample Solution", "Item Information", "Blueprint Summary")
def fetch(url, dest):
    if not os.path.exists(dest):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            f.write(r.read())
    data = open(dest, "rb").read()
    return hashlib.sha256(data).hexdigest(), len(data)
def sha(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()
def main():
    os.makedirs(os.path.join(ROOT,"sources"), exist_ok=True)
    man_path = os.path.join(ROOT, "forms.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {"forms": []}
    have = {f["id"] for f in man["forms"]}
    only = set(sys.argv[1:])
    for fid,title,path,want,q0,q1,keyp,sol0,items,est in FORMS:
        if fid in have or (only and fid not in only): continue
        url = B+path; src = os.path.join(ROOT,"sources",os.path.basename(path))
        got,size = fetch(url, src)
        if got != want:
            print("HASH_MISMATCH", fid, got); continue
        rd = PdfReader(src); n = len(rd.pages)
        txt = [(rd.pages[i].extract_text() or "") for i in range(q0, q1+1)]
        if not any(k in txt[0] for k in ("Released Items","Released Questions","Multiple-choice and Numerical-response")) and not txt[0].lstrip().startswith("1. "):
            print("START_CHECK_FAILED", fid); continue
        bad = [q0+i for i,t in enumerate(txt) if any(b in t for b in BAD)]
        if bad:
            print("KEY_TEXT_IN_RANGE", fid, bad); continue
        out = os.path.join(ROOT,"answer-pass",fid); os.makedirs(out, exist_ok=True)
        w = PdfWriter()
        for i in range(q0, q1+1): w.add_page(rd.pages[i])
        qp = os.path.join(out,"questions-only.pdf")
        with open(qp,"wb") as f: w.write(f)
        furl, fsha = FORMULA[fid[:4]]
        fp = os.path.join(out,"formula-sheet.pdf")
        fgot,_ = fetch(furl, os.path.join(ROOT,"sources",os.path.basename(furl)))
        if fgot != fsha: print("FORMULA_HASH_MISMATCH", fid); continue
        open(fp,"wb").write(open(os.path.join(ROOT,"sources",os.path.basename(furl)),"rb").read())
        rec = dict(id=fid,title=title,url=url,sha256=got.upper(),size=size,pages=n,
                   questions_pages=[q0,q1],key_pages=keyp,
                   solutions_from=sol0, items=items, est_min=est,
                   questions_sha256=sha(qp).upper(), formula_url=furl, formula_sha256=fsha.upper(),
                   prepared=datetime.datetime.now().isoformat(timespec="seconds"))
        man["forms"].append(rec)
        write_protocol(rec)
        print("PREPARED", fid, rec["sha256"], size, q0, q1)
        json.dump(man, open(man_path,"w"), indent=1)
def write_protocol(r):
    q0,q1 = r["questions_pages"]
    sol = (f"Written-response sample solutions and scoring guides: PDF page index {r['solutions_from']} to the end."
           if r["solutions_from"] is not None else "This document has no sample solutions or scoring guides after the released items.")
    s = f"""# Protocol {r['id']} - {r['title']}

New version for one more form. It does not edit or replace `PROTOCOL.md` (the frozen 2022 Mathematics 30-1 protocol).
Written before any Codex answer for this form exists. A later edit is a new version.

## Source

- Document: {r['title']}, Alberta Education, Provincial Assessment.
- URL: {r['url']}
- SHA-256 of the downloaded file: `{r['sha256']}`
- Size: {r['size']:,} bytes. {r['pages']} PDF pages. Local copy: `sources/` (gitignored, never opened by Codex).
- Allowed reference: the official formula sheet or data booklet, {r['formula_url']} (SHA-256 `{r['formula_sha256']}`), copied unchanged to `answer-pass/{r['id']}/formula-sheet.pdf`.

## Page ranges (0-based PDF page indexes)

- Questions given to Codex: page indexes {q0} through {q1} inclusive, extracted to `answer-pass/{r['id']}/questions-only.pdf`. SHA-256 of that extract: `{r['questions_sha256']}`
- Item-information pages, which print the keys and difficulty: page indexes {', '.join(map(str,r['key_pages']))}. Not extracted, not given to Codex, not copied into this repository.
- {sol} Not extracted, not given to Codex.
- Pages before the item information are title, contents and introduction. Not used.

## Item ids

{r['items']}. Ids are written as `MC n`, `NR n` and `WR n`, using the numbers printed in the questions extract.

## Rules

- Codex is the calculator. It computes each item in Python, saves the script and its real output, runs one independent check per item (agree or disagree), and writes worked derivations that quote the output.
- Codex does not grade. No key, item-information page, sample solution or scoring guide is given to it, and it must not open `sources/`.
- One attempt per item. An existing answer is never replaced. An empty answer is allowed when a figure did not survive extraction.
- No score is computed in this version. Any later comparison against the published key is a separate step by a grader that is not Codex, recorded as a new file.

## Licence

Crown copyright, the Crown in Right of Alberta, all rights reserved. The PDF, stems, figures, key, sample solutions and scoring guides are not in this repository.
"""
    open(os.path.join(ROOT, f"PROTOCOL-{r['id']}.md"),"w",encoding="utf-8").write(s)
if __name__ == "__main__":
    main()

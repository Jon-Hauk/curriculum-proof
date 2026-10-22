"""Extract and render only the authorized questions-only PDF."""
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent / "source-pages"
DEST.mkdir(exist_ok=True)
source = ROOT / "answer-pass" / "questions-only.pdf"
doc = pymupdf.open(source)
print(f"Source: {source.relative_to(ROOT)}")
print(f"Pages: {len(doc)}")
for number, page in enumerate(doc, 1):
    print(f"\n--- PDF PAGE {number} ---\n{page.get_text()}")
    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(DEST / f"page-{number:02}.png")

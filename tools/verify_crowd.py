"""Verify Crowd.docx IEEE formatting after fix."""
from docx import Document
from docx.oxml.ns import qn

doc = Document(r"c:\Users\akshi\Downloads\Crowd.docx")
print("Sections:", len(doc.sections))
for i, s in enumerate(doc.sections):
    cols_el = s._sectPr.find(qn("w:cols"))
    cols = cols_el.attrib if cols_el is not None else {}
    print(
        f"  {i}: top={s.top_margin.inches:.3f}in "
        f"left={s.left_margin.inches:.3f}in cols={cols}"
    )

print("\nFirst 12 paragraphs:")
for i, p in enumerate(doc.paragraphs[:12]):
    runs = [
        (r.text[:30], r.bold, r.italic, r.font.size.pt if r.font.size else None)
        for r in p.runs[:4]
    ]
    print(f"{i:3d} [{p.style.name}] wc={len(p.text.split())} | {p.text[:70]}")
    print(f"     runs {runs}")

print("\nHeadings sample:")
for i, p in enumerate(doc.paragraphs):
    if p.style.name == "Heading 1":
        runs = [(r.bold, r.font.size.pt if r.font.size else None) for r in p.runs]
        brs = p._p.findall(".//" + qn("w:br"))
        print(f"  {i} {p.text} runs={runs} col_breaks={sum(1 for b in brs if b.get(qn('w:type'))=='column')}")

print("\nReferences:")
for i, p in enumerate(doc.paragraphs):
    if p.style.name == "references" or p.text.strip().upper() == "REFERENCES":
        print(f"  {i} [{p.style.name}] {p.text[:90]}")

print(f"\nTotal words: {sum(len(p.text.split()) for p in doc.paragraphs)}")

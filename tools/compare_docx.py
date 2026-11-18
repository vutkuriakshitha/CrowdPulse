"""Deep compare IEEE template vs Crowd docx using python-docx."""
from docx import Document
from docx.shared import Pt
from pathlib import Path
from collections import Counter


def para_info(p):
    style = p.style.name if p.style else None
    fonts, sizes, bold, italic = set(), set(), False, False
    text_parts = []
    for run in p.runs:
        text_parts.append(run.text)
        if run.bold:
            bold = True
        if run.italic:
            italic = True
        if run.font.name:
            fonts.add(run.font.name)
        if run.font.size:
            sizes.add(run.font.size.pt)
    text = "".join(text_parts).strip()
    return {
        "text": text,
        "style": style,
        "fonts": sorted(fonts),
        "sizes": sorted(sizes),
        "bold": bold,
        "italic": italic,
        "wc": len(text.split()) if text else 0,
    }


def analyze(path):
    doc = Document(path)
    paras = [para_info(p) for p in doc.paragraphs if para_info(p)["text"] or p.style]
    # sections / page setup
    sec = doc.sections[0]
    return {
        "path": path,
        "paras": paras,
        "page_width_in": sec.page_width.inches,
        "page_height_in": sec.page_height.inches,
        "left_margin_in": sec.left_margin.inches,
        "right_margin_in": sec.right_margin.inches,
        "top_margin_in": sec.top_margin.inches,
        "bottom_margin_in": sec.bottom_margin.inches,
        "styles": sorted({s.name for s in doc.styles if hasattr(s, "name")}),
    }


def print_report(label, info):
    print("=" * 90)
    print(label, info["path"])
    print(
        f"Page: {info['page_width_in']:.2f}x{info['page_height_in']:.2f} in | "
        f"Margins L/R/T/B: {info['left_margin_in']:.2f}/{info['right_margin_in']:.2f}/"
        f"{info['top_margin_in']:.2f}/{info['bottom_margin_in']:.2f}"
    )
    styles = Counter(p["style"] for p in info["paras"])
    print("Style counts:", dict(styles))
    print(f"Paragraphs: {len(info['paras'])}, Words: {sum(p['wc'] for p in info['paras'])}")
    print("Available styles sample:", info["styles"][:20])
    print()
    for i, p in enumerate(info["paras"]):
        t = p["text"][:140] + ("..." if len(p["text"]) > 140 else "")
        print(
            f"{i+1:3d} | {p['style']} | sz={p['sizes']} | font={p['fonts']} | "
            f"b={p['bold']} | wc={p['wc']} | {t}"
        )
    print()


def compare_styles(t, c):
    print("=" * 90)
    print("STYLE SIZE COMPARISON (template vs crowd)")
    print("=" * 90)
    t_by_style = {}
    for p in t["paras"]:
        if p["style"] not in t_by_style and p["sizes"]:
            t_by_style[p["style"]] = p["sizes"]
    c_by_style = {}
    for p in c["paras"]:
        if p["style"] not in c_by_style and p["sizes"]:
            c_by_style[p["style"]] = p["sizes"]
    all_styles = sorted(set(t_by_style) | set(c_by_style))
    for s in all_styles:
        ts = t_by_style.get(s, "—")
        cs = c_by_style.get(s, "—")
        match = "OK" if ts == cs else "MISMATCH"
        print(f"{s:20s} template={ts} crowd={cs} [{match}]")


if __name__ == "__main__":
    template = analyze(r"c:\Users\akshi\Downloads\IEEE conference-template-a4.docx")
    crowd = analyze(r"c:\Users\akshi\Downloads\Crowd.docx")
    print_report("TEMPLATE", template)
    print_report("CROWD", crowd)
    compare_styles(template, crowd)

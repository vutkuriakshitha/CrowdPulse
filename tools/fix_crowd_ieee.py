"""Fix Crowd.docx to match IEEE conference template formatting."""
from __future__ import annotations

import re
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Pt, Twips

SOURCE = Path(r"c:\Users\akshi\Downloads\Crowd.docx")
BACKUP = Path(r"c:\Users\akshi\Downloads\Crowd_backup.docx")
OUTPUT = Path(r"c:\Users\akshi\Downloads\Crowd.docx")

STYLE_MAP = {
    "papertitle": "paper title",
    "BodyText": "Body Text",
    "Heading1": "Heading 1",
    "Heading2": "Heading 2",
    "bulletlist": "bullet list",
    "figurecaption": "figure caption",
}

AUTHORS = [
    "V. Akshitha (23B81A05K6)",
    "G. Manvitha (23B81A05M5)",
    "G. Srivalli (23B81A05Q1)",
]
AFFILIATION_LINES = [
    "Department of Computer Science and Engineering",
    "CVR College of Engineering",
    "Hyderabad, India",
]


def clear_run_formatting(run) -> None:
    run.bold = None
    run.italic = None
    run.font.size = None
    run.font.name = None
    rpr = run._r.get_or_add_rPr()
    for tag in ("sz", "szCs", "rFonts", "b", "i", "bCs", "iCs"):
        el = rpr.find(qn(f"w:{tag}"))
        if el is not None:
            rpr.remove(el)


def set_paragraph_style(paragraph, style_name: str) -> None:
    try:
        paragraph.style = style_name
    except KeyError:
        mapped = STYLE_MAP.get(style_name, style_name)
        paragraph.style = mapped


def rebuild_author_paragraph(paragraph, name: str) -> None:
    set_paragraph_style(paragraph, "Author")
    paragraph.clear()
    lines = [name, *AFFILIATION_LINES]
    for idx, line in enumerate(lines):
        run = paragraph.add_run(line)
        clear_run_formatting(run)
        if idx < len(lines) - 1:
            paragraph.add_run().add_break()


def rebuild_label_paragraph(paragraph, label: str, body: str, *, label_bold: bool, body_italic: bool = False) -> None:
    style_name = "Abstract" if label == "Abstract" else "Keywords"
    set_paragraph_style(paragraph, style_name)
    paragraph.clear()
    prefix = paragraph.add_run(f"{label}—")
    clear_run_formatting(prefix)
    prefix.bold = label_bold
    content = paragraph.add_run(body)
    clear_run_formatting(content)
    if body_italic:
        content.italic = True


def normalize_paragraph_runs(paragraph, *, keep_bold: bool = False, keep_italic: bool = False) -> None:
    for run in paragraph.runs:
        if not keep_bold:
            run.bold = None
        if not keep_italic:
            run.italic = None
        run.font.size = None
        run.font.name = None
        rpr = run._r.get_or_add_rPr()
        for tag in ("sz", "szCs", "rFonts", "b", "bCs", "i", "iCs"):
            if keep_bold and tag in ("b", "bCs"):
                continue
            if keep_italic and tag in ("i", "iCs"):
                continue
            el = rpr.find(qn(f"w:{tag}"))
            if el is not None:
                rpr.remove(el)


def add_column_break_before(paragraph) -> None:
    br_types = {
        br.get(qn("w:type"))
        for br in paragraph._p.findall(".//" + qn("w:br"))
    }
    if "column" in br_types:
        return
    run = paragraph.runs[0] if paragraph.runs else paragraph.add_run("")
    run.add_break(WD_BREAK.COLUMN)


def fix_section_layout(doc: Document) -> None:
    # IEEE A4 main section: top 54pt, left/right 44.65pt, bottom 72pt, 2 columns, 18pt gutter
    for section in doc.sections:
        section.page_height = Twips(16838)
        section.page_width = Twips(11906)
        section.top_margin = Twips(1080)      # 54pt
        section.bottom_margin = Twips(1440)   # 72pt
        section.left_margin = Twips(893)      # 44.65pt
        section.right_margin = Twips(893)
        section.header_distance = Twips(720)  # 36pt
        section.footer_distance = Twips(720)

    # First section: single column for title/authors/abstract
    first = doc.sections[0]
    first_cols = first._sectPr.find(qn("w:cols"))
    if first_cols is not None:
        for attr in ("num", "equalWidth", "sep"):
            if attr in first_cols.attrib:
                del first_cols.attrib[attr]
        first_cols.set(qn("w:space"), "720")  # 36pt

    # Middle section (if present): 3 columns for author blocks
    if len(doc.sections) >= 2:
        mid = doc.sections[1]
        mid_cols = mid._sectPr.find(qn("w:cols"))
        if mid_cols is None:
            mid_cols = mid._sectPr.makeelement(qn("w:cols"), {})
            mid._sectPr.append(mid_cols)
        mid_cols.set(qn("w:num"), "3")
        mid_cols.set(qn("w:space"), "720")
        if qn("w:equalWidth") not in mid_cols.attrib:
            mid_cols.set(qn("w:equalWidth"), "1")

    # Last/body section: 2 columns
    body = doc.sections[-1]
    body_cols = body._sectPr.find(qn("w:cols"))
    if body_cols is None:
        body_cols = body._sectPr.makeelement(qn("w:cols"), {})
        body._sectPr.append(body_cols)
    body_cols.set(qn("w:num"), "2")
    body_cols.set(qn("w:space"), "360")  # 18pt
    body_cols.set(qn("w:equalWidth"), "1")
    if qn("w:sep") in body_cols.attrib:
        del body_cols.attrib[qn("w:sep")]


def strip_manual_reference_numbers(text: str) -> str:
    return re.sub(r"^\[\d+\]\s*", "", text.strip())


def fix_document() -> None:
    shutil.copy2(SOURCE, BACKUP)
    doc = Document(SOURCE)

    # Title
    if doc.paragraphs:
        set_paragraph_style(doc.paragraphs[0], "paper title")
        normalize_paragraph_runs(doc.paragraphs[0])

    # Remove empty filler paragraph between title and authors if present
    paras = doc.paragraphs
    if len(paras) > 1 and not paras[1].text.strip():
        p = paras[1]._element
        p.getparent().remove(p)

    # Authors (first three affiliation blocks)
    author_paras = [p for p in doc.paragraphs if p.style.name in ("Author", "Normal")][:3]
    for para, name in zip(author_paras, AUTHORS):
        rebuild_author_paragraph(para, name)

    # Abstract
    for para in doc.paragraphs:
        if para.style.name == "Abstract" or para.text.startswith("Abstract"):
            body = re.sub(r"^Abstract\s*[—\-–]\s*", "", para.text.strip())
            rebuild_label_paragraph(para, "Abstract", body, label_bold=True)
            break

    # Keywords
    for para in doc.paragraphs:
        if para.style.name == "Keywords" or para.text.startswith("Keywords"):
            body = re.sub(r"^Keywords\s*[—\-–]\s*", "", para.text.strip())
            rebuild_label_paragraph(para, "Keywords", body, label_bold=True, body_italic=True)
            break

    # Column break before first Heading 1 (start two-column body)
    for para in doc.paragraphs:
        if para.style.name in ("Heading 1", "Heading1") and para.text.strip():
            add_column_break_before(para)
            break

    # Headings and body: remove manual bold/size overrides
    for para in doc.paragraphs:
        style = para.style.name
        if style in ("Heading 1", "Heading1"):
            set_paragraph_style(para, "Heading 1")
            normalize_paragraph_runs(para)
        elif style in ("Heading 2", "Heading2"):
            set_paragraph_style(para, "Heading 2")
            normalize_paragraph_runs(para)
        elif style in ("Body Text", "BodyText"):
            set_paragraph_style(para, "Body Text")
            normalize_paragraph_runs(para)
        elif style in ("bullet list", "bulletlist"):
            set_paragraph_style(para, "bullet list")
            normalize_paragraph_runs(para)
        elif style in ("figure caption", "figurecaption"):
            set_paragraph_style(para, "figure caption")
            normalize_paragraph_runs(para)

    # References heading + entries
    ref_started = False
    for para in doc.paragraphs:
        text = para.text.strip()
        if text.upper() == "REFERENCES":
            set_paragraph_style(para, "Heading 1")
            normalize_paragraph_runs(para)
            ref_started = True
            continue
        if ref_started and text:
            cleaned = strip_manual_reference_numbers(text)
            set_paragraph_style(para, "references")
            para.clear()
            run = para.add_run(cleaned)
            clear_run_formatting(run)

    fix_section_layout(doc)
    doc.save(OUTPUT)
    print(f"Saved corrected document to: {OUTPUT}")
    print(f"Backup created at: {BACKUP}")


if __name__ == "__main__":
    fix_document()

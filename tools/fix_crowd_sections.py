"""Fix Crowd.docx section layout to match IEEE template."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Twips

OUTPUT = Path(r"c:\Users\akshi\Downloads\Crowd.docx")


def set_cols(sect_pr, *, num=None, space_twips: int = 720) -> None:
    cols = sect_pr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sect_pr.append(cols)
    for attr in list(cols.attrib):
        del cols.attrib[attr]
    cols.set(qn("w:space"), str(space_twips))
    if num is not None:
        cols.set(qn("w:num"), str(num))
        cols.set(qn("w:equalWidth"), "1")


def set_margins(sect_pr) -> None:
    pg_mar = sect_pr.find(qn("w:pgMar"))
    if pg_mar is None:
        pg_mar = OxmlElement("w:pgMar")
        sect_pr.append(pg_mar)
    pg_mar.set(qn("w:top"), "1080")
    pg_mar.set(qn("w:right"), "893")
    pg_mar.set(qn("w:bottom"), "1440")
    pg_mar.set(qn("w:left"), "893")
    pg_mar.set(qn("w:header"), "720")
    pg_mar.set(qn("w:footer"), "720")
    pg_mar.set(qn("w:gutter"), "0")


def ensure_sect_pr_on_paragraph(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    sect_pr = p_pr.find(qn("w:sectPr"))
    if sect_pr is None:
        sect_pr = OxmlElement("w:sectPr")
        p_pr.append(sect_pr)
    return sect_pr


def remove_sect_pr(paragraph):
    p_pr = paragraph._p.find(qn("w:pPr"))
    if p_pr is None:
        return
    sect_pr = p_pr.find(qn("w:sectPr"))
    if sect_pr is not None:
        p_pr.remove(sect_pr)


def fix_sections() -> None:
    doc = Document(OUTPUT)
    paras = doc.paragraphs

    # Remove all inline section breaks; we'll rebuild cleanly.
    for p in paras:
        remove_sect_pr(p)

    # Identify anchor paragraphs by content/style.
    title_p = paras[0]
    author_ps = [p for p in paras if p.style.name == "Author"][:3]
    abstract_p = next(p for p in paras if p.style.name == "Abstract")
    intro_p = next(
        p for p in paras if p.style.name == "Heading 1" and p.text.strip().startswith("I.")
    )

    # Section 0 ends after title -> single column header block start
    sect0 = ensure_sect_pr_on_paragraph(title_p)
    set_margins(sect0)
    set_cols(sect0, num=None, space_twips=720)

    # Section 1 ends after last author -> three columns for author row
    sect1 = ensure_sect_pr_on_paragraph(author_ps[-1])
    set_margins(sect1)
    set_cols(sect1, num=3, space_twips=720)

    # Section 2 ends after keywords -> single column for abstract block
    keywords_p = next(p for p in paras if p.style.name == "Keywords")
    sect2 = ensure_sect_pr_on_paragraph(keywords_p)
    set_margins(sect2)
    set_cols(sect2, num=None, space_twips=720)

    # Final section (document body) -> two columns
    body_sect = doc.sections[-1]._sectPr
    set_margins(body_sect)
    set_cols(body_sect, num=2, space_twips=360)

    # Ensure column break at start of Introduction
    br_types = {
        br.get(qn("w:type"))
        for br in intro_p._p.findall(".//" + qn("w:br"))
    }
    if "column" not in br_types:
        run = intro_p.runs[0] if intro_p.runs else intro_p.add_run("")
        run.add_break(WD_BREAK.COLUMN)

    doc.save(OUTPUT)
    print("Section layout fixed.")


if __name__ == "__main__":
    fix_sections()

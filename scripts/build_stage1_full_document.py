"""Generate CrowdPulse Stage-I Major Project Report (~40 pages) per CVR CSE guidelines."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(r"c:\MAJORPROJECT\docs")
ASSET_DIR = OUT_DIR / "assets" / "stage1"
OUT_PATH = OUT_DIR / "CrowdPulse_Stage1_Major_Project_Report.docx"
OUT_DOWNLOADS = Path(
    r"c:\Users\akshi\Downloads\CrowdPulse_Stage1_Major_Project_Report.docx"
)

TITLE = "CrowdPulse: An Intelligent Crowd Analytics and Decision Support Platform"
TEAM = [
    ("V. Akshitha", "23B81A05K6"),
    ("G. Manvitha", "23B81A05M5"),
    ("G. Srivalli", "23B81A05Q1"),
]
SUPERVISOR = "Mr. M. Hanimi Reddy"
SUPERVISOR_DESIG = "Sr. Assistant Professor"
HOD = "Dr. A. Vani Vathsala"
ACADEMIC_YEAR = "2026-2027"


# ── formatting helpers ───────────────────────────────────────────────────────


def set_run_font(run, name="Times New Roman", size=12, bold=False, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def add_para(
    doc,
    text,
    *,
    size=12,
    bold=False,
    italic=False,
    align="justify",
    space_after=8,
    space_before=0,
    first_line_indent=None,
):
    p = doc.add_paragraph()
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if first_line_indent is not None:
        pf.first_line_indent = Inches(first_line_indent)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_page_break(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)


def add_chapter_heading(doc, text):
    add_page_break(doc)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text.upper())
    set_run_font(run, size=14, bold=True)


def add_section_heading(doc, text, level=2):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level == 2 else 8)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text.upper() if level == 2 else text)
    set_run_font(run, size=12, bold=True)


def add_subsection_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    set_run_font(run, size=12, bold=True)


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if level:
        p.paragraph_format.left_indent = Inches(0.5 * level)
    run = p.add_run(text)
    set_run_font(run, size=12)


def set_cell_shading(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def fill_table(table, rows, header=True):
    for r_i, row_data in enumerate(rows):
        for c_i, val in enumerate(row_data):
            cell = table.cell(r_i, c_i)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            set_run_font(run, size=10, bold=(header and r_i == 0))
            if header and r_i == 0:
                set_cell_shading(cell, "1F4E79")
                run.font.color.rgb = RGBColor(255, 255, 255)


def add_caption(doc, text):
    add_para(doc, text, size=11, italic=True, align="center", space_after=12, space_before=4)


def add_figure(doc, path: Path, caption: str, width=Inches(5.5)):
    if path.exists():
        doc.add_picture(str(path), width=width)
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_caption(doc, caption)


def setup_margins(section):
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3.75)
    section.right_margin = Cm(2.5)


def add_footer_page_number(section, fmt="decimal"):
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" PAGE "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_end)
    set_run_font(run, size=10)


# ── diagram generation ───────────────────────────────────────────────────────


def _font(size=14):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_usecase_diagram(path: Path):
    w, h = 900, 520
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f = _font(13)
    fb = _font(15)
    d.rectangle([30, 180, 130, 340], outline="black", width=2)
    d.text((45, 240), "Operator", fill="black", font=f)
    d.rectangle([30, 60, 130, 140], outline="black", width=2)
    d.text((55, 90), "Admin", fill="black", font=f)
    d.rectangle([280, 40, 820, 460], outline="black", width=3)
    d.text((420, 55), "CrowdPulse System", fill="black", font=fb)
    cases = [
        "Login / Authenticate",
        "View Digital Twin Dashboard",
        "Receive Risk Alerts (ERA)",
        "Accept / Dismiss Actions",
        "Upload / Process CCTV",
        "Run What-If Simulation",
        "Generate Incident Report",
    ]
    y = 100
    for c in cases:
        d.ellipse([360, y, 740, y + 38], outline="black", width=2)
        d.text((380, y + 10), c, fill="black", font=_font(11))
        y += 48
    d.line([130, 100, 360, 120], fill="black", width=2)
    d.line([130, 260, 360, 200], fill="black", width=2)
    d.line([130, 260, 360, 280], fill="black", width=2)
    img.save(path)


def draw_architecture_diagram(path: Path):
    w, h = 920, 560
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f = _font(12)
    fb = _font(14)
    boxes = [
        (340, 20, 580, 70, "Next.js Ops Console"),
        (340, 100, 580, 150, "FastAPI REST + JWT"),
        (60, 190, 260, 250, "YOLO / HOG\nDetector"),
        (300, 190, 500, 250, "Tracker +\nZone Analytics"),
        (540, 190, 740, 250, "DCRS + ERA"),
        (780, 190, 900, 250, "Gradient\nBoosting"),
        (200, 310, 420, 370, "What-If Simulator"),
        (480, 310, 700, 370, "Incident Reporter"),
        (300, 420, 620, 480, "SQLite / Postgres + Twin Store"),
    ]
    for x1, y1, x2, y2, label in boxes:
        d.rectangle([x1, y1, x2, y2], outline="black", width=2)
        d.multiline_text((x1 + 12, y1 + 10), label, fill="black", font=f, spacing=4)
    d.text((350, 500), "Sample / Uploaded CCTV", fill="black", font=f)
    arrows = [
        ((460, 70), (460, 100)),
        ((460, 150), (460, 190)),
        ((260, 220), (300, 220)),
        ((500, 220), (540, 220)),
        ((740, 220), (780, 220)),
        ((460, 250), (460, 310)),
        ((460, 370), (460, 420)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        d.line([x1, y1, x2, y2], fill="black", width=2)
    d.text((20, 10), "CrowdPulse Level A Architecture", fill="black", font=fb)
    img.save(path)


def draw_sequence_diagram(path: Path):
    w, h = 920, 500
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f = _font(11)
    actors = ["Admin", "UI", "API", "CV", "Risk", "Twin"]
    xs = [40, 180, 320, 460, 600, 740]
    for i, name in enumerate(actors):
        d.rectangle([xs[i], 20, xs[i] + 90, 55], outline="black", width=2)
        d.text((xs[i] + 8, 28), name, fill="black", font=f)
        d.line([xs[i] + 45, 55, xs[i] + 45, 470], fill="gray", width=1)
    msgs = [
        (0, 1, 80, "Select dense sample"),
        (1, 2, 110, "POST /pipeline/run"),
        (2, 3, 140, "Detect + Track frames"),
        (3, 2, 170, "Zone counts"),
        (2, 4, 200, "DCRS + ERA + GB"),
        (4, 2, 230, "Alerts + actions"),
        (2, 5, 260, "Update twin store"),
        (2, 1, 290, "Twin snapshot"),
        (1, 0, 320, "Map colors + queue"),
    ]
    for src, dst, y, label in msgs:
        x1, x2 = xs[src] + 45, xs[dst] + 45
        d.line([x1, y, x2, y], fill="black", width=2)
        d.text(((x1 + x2) // 2 - 60, y - 14), label, fill="black", font=_font(10))
    d.text((20, 460), "Figure 4.3 — Risk pipeline sequence", fill="black", font=f)
    img.save(path)


def draw_class_diagram(path: Path):
    w, h = 920, 480
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f = _font(11)
    classes = [
        (40, 60, 280, 180, "ZoneMetrics", "density, mean_speed\nopposing_flow, exit_pressure"),
        (340, 60, 580, 180, "RiskScore", "dcrs, band, zone_id\nfeatures: dict"),
        (640, 60, 880, 180, "DecisionBundle", "actions: list\nrationale: str"),
        (190, 240, 430, 360, "DCRSEngine", "+ evaluate(metrics)\n+ forecast()"),
        (470, 240, 710, 360, "MLRecommender", "+ rank_actions()\n+ safety_filter()"),
        (340, 390, 580, 460, "VideoProcessor", "+ process(video_id)"),
    ]
    for x1, y1, x2, y2, name, attrs in classes:
        d.rectangle([x1, y1, x2, y2], outline="black", width=2)
        d.text((x1 + 10, y1 + 8), name, fill="black", font=f)
        d.line([x1, y1 + 28, x2, y1 + 28], fill="black", width=1)
        d.multiline_text((x1 + 10, y1 + 35), attrs, fill="black", font=_font(10), spacing=3)
    d.line([430, 180, 310, 240], fill="black", width=2)
    d.line([580, 180, 590, 240], fill="black", width=2)
    d.line([310, 360, 460, 390], fill="black", width=2)
    img.save(path)


def ensure_diagrams():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "usecase": ASSET_DIR / "usecase_diagram.png",
        "architecture": ASSET_DIR / "architecture_diagram.png",
        "sequence": ASSET_DIR / "sequence_diagram.png",
        "class": ASSET_DIR / "class_diagram.png",
    }
    draw_usecase_diagram(paths["usecase"])
    draw_architecture_diagram(paths["architecture"])
    draw_sequence_diagram(paths["sequence"])
    draw_class_diagram(paths["class"])
    return paths


# ── front matter ─────────────────────────────────────────────────────────────


def build_cover_pages(doc):
    add_para(doc, "CVR COLLEGE OF ENGINEERING", size=14, bold=True, align="center", space_after=4)
    add_para(
        doc,
        "(An UGC Autonomous Institution, Affiliated to JNTUH,\nAccredited by NBA, and NAAC 'A' Grade)",
        size=11,
        align="center",
        space_after=12,
    )
    add_para(doc, TITLE, size=16, bold=True, align="center", space_after=18)
    add_para(
        doc,
        "A dissertation submitted to the Jawaharlal Nehru Technological University, Hyderabad "
        "in partial fulfillment of the requirement for the award of degree of",
        size=12,
        align="center",
        space_after=8,
    )
    add_para(doc, "BACHELOR OF TECHNOLOGY", size=14, bold=True, align="center", space_after=4)
    add_para(doc, "IN", size=12, align="center", space_after=4)
    add_para(doc, "COMPUTER SCIENCE AND ENGINEERING", size=14, bold=True, align="center", space_after=18)
    add_para(doc, "Submitted by", size=12, bold=True, align="center", space_after=6)
    for name, roll in TEAM:
        add_para(doc, f"{name} ({roll})", size=12, align="center", space_after=2)
    add_para(doc, "Under the Guidance of", size=12, bold=True, align="center", space_before=12, space_after=6)
    add_para(doc, SUPERVISOR, size=12, align="center", space_after=2)
    add_para(doc, SUPERVISOR_DESIG, size=12, align="center", space_after=12)
    add_para(doc, "Department of Computer Science and Engineering", size=12, align="center", space_after=4)
    add_para(doc, "CVR COLLEGE OF ENGINEERING", size=12, bold=True, align="center", space_after=4)
    add_para(
        doc,
        "Vastunagar, Mangalpalli (V), Ibrahimpatnam (M),\nRanga Reddy (Dist.) - 501510, Telangana State",
        size=11,
        align="center",
        space_after=8,
    )
    add_para(doc, ACADEMIC_YEAR, size=12, bold=True, align="center")

    add_page_break(doc)
    add_para(doc, "CVR COLLEGE OF ENGINEERING", size=13, bold=True, align="center", space_after=4)
    add_para(
        doc,
        "(An UGC Autonomous Institution, Affiliated to JNTUH,\nAccredited by NBA, and NAAC 'A' Grade)",
        size=11,
        align="center",
        space_after=10,
    )
    add_para(doc, "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", size=12, bold=True, align="center", space_after=18)
    add_para(doc, "CERTIFICATE", size=14, bold=True, align="center", space_after=12)
    team_str = ", ".join(f"{n} ({r})" for n, r in TEAM)
    add_para(
        doc,
        f"This is to certify that the Project Work Stage-I entitled {TITLE} is submitted by "
        f"{team_str} in partial fulfillment of the requirements for the award of the degree of "
        f"Bachelor of Technology in Computer Science and Engineering for the academic year {ACADEMIC_YEAR}.",
        first_line_indent=0.3,
        space_after=24,
    )
    add_para(doc, "Project Supervisor\t\tProfessor in-charge project", bold=True, space_after=24)
    add_para(doc, f"({SUPERVISOR})\t\t( Name )", space_after=4)
    add_para(doc, f"{SUPERVISOR_DESIG}\t\tDesignation", space_after=24)
    add_para(doc, "Professor and Head, CSE", space_after=4)
    add_para(doc, f"({HOD})", space_after=12)

    add_page_break(doc)
    add_para(doc, "DECLARATION", size=14, bold=True, align="center", space_after=12)
    add_para(
        doc,
        f"We, hereby declare that this Project Work Stage-I report titled {TITLE} submitted to the "
        "Department of Computer Science and Engineering, CVR College of Engineering, is a record of "
        f"original work done by us under the guidance of {SUPERVISOR}. The information and data given "
        "in the report is authentic to the best of our knowledge. This project report has not been "
        "submitted to any other university or institution for the award of any degree or diploma, "
        "nor has it been published previously.",
        first_line_indent=0.3,
        space_after=24,
    )
    for name, roll in TEAM:
        add_para(doc, f"{name} ({roll})", space_after=8)
    add_para(doc, "Date:", space_before=12, space_after=4)
    add_para(doc, "Place: Hyderabad", space_after=12)

    add_page_break(doc)
    add_para(doc, "ACKNOWLEDGEMENT", size=14, bold=True, align="center", space_after=12)
    add_para(
        doc,
        "We express our sincere gratitude to our project supervisor, "
        f"{SUPERVISOR}, {SUPERVISOR_DESIG}, Department of Computer Science and Engineering, "
        "CVR College of Engineering, for his continuous guidance, constructive feedback, and encouragement "
        "throughout the Stage-I phase of this major project. His technical insights on computer vision, "
        "risk modelling, and software architecture significantly shaped the direction of CrowdPulse.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        f"We thank {HOD}, Professor and Head, Department of Computer Science and Engineering, "
        "for providing the laboratory facilities and academic support required to carry out this work. "
        "We also thank the faculty members of the CSE department for their valuable suggestions during "
        "internal reviews and progress discussions.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "We extend our appreciation to our peers and family members for their moral support and patience "
        "during the development and documentation of this intelligent crowd analytics platform.",
        first_line_indent=0.3,
    )

    add_page_break(doc)
    add_para(doc, "ABSTRACT", size=14, bold=True, align="center", space_after=12)
    add_para(
        doc,
        "Large public gatherings at stadiums, festivals, transit hubs, and civic events continue to "
        "produce preventable crush and congestion incidents despite widespread CCTV deployment. "
        "Traditional surveillance practice relies on human operators scanning multiple feeds, while "
        "counting-only computer-vision tools improve awareness but rarely close the loop from "
        "perception to explainable action. CrowdPulse addresses this gap as an intelligent crowd "
        "analytics and decision support platform for venue control rooms.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "The proposed system ingests CCTV or sample video, detects and tracks persons using YOLOv8 "
        "(with OpenCV HOG fallback), maps observations to venue zones, and computes a Dynamic Crowd "
        "Risk Score (DCRS) that combines density with flow-speed decay, opposing-flow conflict, exit "
        "pressure, and related multi-factor signals. Each alert is accompanied by Explainable Risk "
        "Attribution (ERA). A Gradient Boosting recommender ranks control-room interventions under a "
        "deterministic safety filter. Operators interact through a JWT-secured Next.js digital-twin "
        "dashboard supporting Accept/Dismiss decisions, what-if simulation, and incident reporting, "
        "with historical logging in a schema-backed SQLite database (Postgres-ready).",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "This Stage-I report presents the problem motivation, literature survey, requirement analysis, "
        "and system design of CrowdPulse. The Level A implementation targets a single-venue academic "
        "pilot suitable for stadium and public-venue demonstration while remaining architecturally "
        "open to multi-camera scale-out in future work.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Keywords — crowd analytics, crowd safety, YOLOv8, computer vision, Dynamic Crowd Risk Score, "
        "explainable AI, Gradient Boosting, decision support, digital twin, smart surveillance",
        italic=True,
        size=11,
        space_after=12,
    )


def build_toc_and_lists(doc, diagrams):
    add_page_break(doc)
    add_para(doc, "TABLE OF CONTENTS", size=14, bold=True, align="center", space_after=12)
    toc_items = [
        ("List of Tables", ""),
        ("List of Figures", ""),
        ("Abbreviations", ""),
        ("1", "INTRODUCTION"),
        ("1.1", "Motivation"),
        ("1.2", "Problem Statement"),
        ("1.3", "Project Objectives"),
        ("1.4", "Project Report Organization"),
        ("2", "LITERATURE SURVEY"),
        ("2.1", "Existing Work"),
        ("2.2", "Limitations of Existing Work"),
        ("3", "REQUIREMENT ANALYSIS"),
        ("3.1", "Software Requirements"),
        ("3.2", "Hardware Requirements"),
        ("3.3", "User Requirements"),
        ("4", "SYSTEM DESIGN"),
        ("4.0", "Proposed System Architecture"),
        ("4.1", "Proposed Methods / Algorithms"),
        ("4.2", "Class / Use Case / Activity / Sequence Diagrams"),
        ("4.3", "Datasets and Technology Stack"),
        ("", "REFERENCES"),
        ("", "APPENDIX"),
    ]
    t = doc.add_table(rows=len(toc_items) + 1, cols=2)
    t.style = "Table Grid"
    fill_table(t, [["Section", "Page No."]] + [[a, b] for a, b in toc_items], header=True)
    add_page_break(doc)

    add_para(doc, "LIST OF TABLES", size=14, bold=True, align="center", space_after=12)
    tables = [
        "Table 2.1 — Comparison of academic crowd monitoring techniques",
        "Table 2.2 — Selected IEEE-oriented papers (2023–2025)",
        "Table 3.1 — Functional requirements",
        "Table 3.2 — Non-functional requirements",
        "Table 4.1 — DCRS feature definitions",
        "Table 4.2 — Risk band classification",
        "Table 4.3 — Gradient Boosting benchmark summary",
        "Table 4.4 — Technology stack by module",
        "Table 4.5 — Demo venue zone topology (Aether Arena)",
    ]
    for i, item in enumerate(tables, 1):
        add_para(doc, f"Table {i}: {item.split('—')[1].strip() if '—' in item else item}", size=11, space_after=4)

    add_page_break(doc)
    add_para(doc, "LIST OF FIGURES", size=14, bold=True, align="center", space_after=12)
    figures = [
        "Figure 3.1 — Use case diagram (Operator and Admin actors)",
        "Figure 4.1 — Proposed system architecture (Level A)",
        "Figure 4.2 — Component / class diagram (core AI modules)",
        "Figure 4.3 — Sequence diagram of risk pipeline",
    ]
    for item in figures:
        add_para(doc, item, size=11, space_after=4)

    add_page_break(doc)
    add_para(doc, "ABBREVIATIONS", size=14, bold=True, align="center", space_after=12)
    abbr = [
        ("API", "Application Programming Interface"),
        ("CCTV", "Closed-Circuit Television"),
        ("CDSE", "Cognitive Decision Support Engine"),
        ("COCO", "Common Objects in Context (dataset)"),
        ("DCRS", "Dynamic Crowd Risk Score"),
        ("ERA", "Explainable Risk Attribution"),
        ("GB", "Gradient Boosting"),
        ("HOG", "Histogram of Oriented Gradients"),
        ("JWT", "JSON Web Token"),
        ("RBAC", "Role-Based Access Control"),
        ("REST", "Representational State Transfer"),
        ("UI", "User Interface"),
        ("XAI", "Explainable Artificial Intelligence"),
        ("YOLO", "You Only Look Once"),
    ]
    t2 = doc.add_table(rows=len(abbr) + 1, cols=2)
    t2.style = "Table Grid"
    fill_table(t2, [["Abbreviation", "Expansion"]] + list(abbr), header=True)


# ── chapters ─────────────────────────────────────────────────────────────────


def add_body_block(doc, paragraphs):
    """Add multiple justified body paragraphs (first-line indent)."""
    for text in paragraphs:
        add_para(doc, text, first_line_indent=0.3)


def add_activity_diagram_section(doc):
    add_subsection_heading(doc, "4.2.1 Activity Diagram Description")
    add_body_block(
        doc,
        [
            "The activity diagram for the CrowdPulse operator workflow describes the following activity "
            "swimlanes. In the Authentication swimlane, the user opens the login page, enters credentials, "
            "and the system validates against the users table; on success a JWT is issued and the dashboard "
            "loads; on failure an error message is displayed. In the Monitoring swimlane, the Operator "
            "views the digital twin map with zone colours updated from the twin store; the system polls "
            "GET /api/v1/twin/snapshot or receives WebSocket push every 3 seconds.",
            "In the Alert Handling swimlane, when DCRS exceeds threshold the system creates an alert "
            "record with ERA explanation; the dashboard displays a risk card; the Operator reads the "
            "narrative and contributing factors; the system presents Gradient Boosting recommendations "
            "in the decision queue; the Operator selects Accept or Dismiss; the system persists the "
            "decision via POST /api/v1/decisions/ack. In the Admin Processing swimlane, the Admin "
            "uploads or selects sample video, triggers POST /api/v1/pipeline/run, the system executes "
            "detect-track-analytics-DCRS-ERA-GB chain, updates twin store, and notifies dashboard.",
            "In the Simulation swimlane, the Operator configures a what-if scenario (close exit, rainfall, "
            "VIP zone, hold ingress), submits POST /api/v1/simulation/what-if, the simulator perturbs "
            "twin parameters and re-evaluates DCRS across zones, and results display predicted peak DCRS "
            "and affected zones. In the Reporting swimlane, the Operator requests incident report "
            "generation; the system assembles timeline from alerts and decisions; markdown report is "
            "persisted and displayed in ReportPanel.",
        ],
    )


def add_literature_detailed_table(doc):
    add_para(doc, "Table 2.4 — Extended literature review matrix", size=11, italic=True, align="center")
    lt = doc.add_table(rows=11, cols=5)
    lt.style = "Table Grid"
    fill_table(
        lt,
        [
            ["S.No", "Paper / System", "Year", "Technique", "Limitation"],
            ["1", "Hybrid YOLOv4 crowd monitoring", "2023", "YOLOv4+DeepSORT", "No decision engine"],
            ["2", "Crowd Multi Prediction CNN", "2023", "Multi-task CNN", "Reactive anomaly only"],
            ["3", "CSRNet crowd counting", "2018", "Density-map CNN", "No motion trajectories"],
            ["4", "IoT + YOLO counting", "2024", "YOLOv8 pipeline", "No XAI / what-if"],
            ["5", "Encoder-Decoder LSTM forecast", "2024", "Multi-cam LSTM", "Density-only forecast"],
            ["6", "WiFi-Video dual attention", "2024", "Multi-modal fusion", "No ops twin"],
            ["7", "YOLOv8 + LSTM stampede", "2025", "Short LSTM horizon", "No Accept/Dismiss loop"],
            ["8", "IICCM Hajj framework", "2025", "CV+AI+IoT integrated", "Broad proposal"],
            ["9", "XAI evacuation optimization", "2025", "MLP + SHAP", "Offline simulation"],
            ["10", "D-Shield digital twin", "2025", "Edge + twin hazard", "Limited DSS / GenAI"],
        ],
    )
    add_caption(doc, "Table 2.4. Extended literature comparison matrix.")


def add_extended_literature(doc):
    add_subsection_heading(doc, "2.1.4 Crowd Multi-Prediction and Anomaly Detection")
    add_body_block(
        doc,
        [
            "Crowd Multi Prediction (IEEE ICCE, 2023) proposes a single shared network for counting, "
            "localization, and anomaly detection simultaneously. While efficient, the anomaly signal remains "
            "reactive — triggered when the network flags deviation from normal patterns rather than "
            "forecasting multi-factor risk five to ten minutes ahead. CrowdPulse extends this direction "
            "by combining instantaneous analytics with forecast_surge from a zone-graph forecaster.",
            "Dual-metric stampede risk systems using YOLOv11 with optical-flow chaos score (2025) improve "
            "on single density thresholds by adding motion chaos as a second signal. However, the combination "
            "remains binary-threshold oriented rather than producing a continuous graded score with "
            "per-feature attribution. DCRS integrates density, speed drop, opposing flow, exit pressure, "
            "weather, time priors, historical hotspots, and forecast surge into one calibrated score.",
            "Advancing urban evacuation via cloud big data and IoT (IEEE CONIT, 2024) demonstrates "
            "stadium-scale exit risk scoring using sensor streams and Spark processing. The approach is "
            "sensor-heavy and weak on vision-native forecasting and explainability. CrowdPulse adopts "
            "a vision-first path suitable for existing CCTV infrastructure while keeping IoT fusion as "
            "a Level B extension.",
        ],
    )
    add_literature_detailed_table(doc)


def add_extended_design(doc):
    add_section_heading(doc, "4.11 Detailed Pipeline Walkthrough")
    stages = [
        (
            "Stage 1 — Video Acquisition",
            "The Admin authenticates via POST /api/v1/auth/login and receives a JWT. Video source is "
            "resolved from one of three paths: (a) multipart upload via POST /api/v1/videos/upload; "
            "(b) selection from the sample catalog (sparse, medium, dense procedurally generated clips); "
            "(c) latest queued video asset. Video metadata is persisted in the video_assets table with "
            "status tracking (uploaded, queued, processing, complete, failed).",
        ),
        (
            "Stage 2 — Frame Sampling and Detection",
            "The video processor reads frames with a configurable stride (default: every Nth frame) and "
            "maximum frame cap to bound compute on laptop CPU. Each frame passes through the detector "
            "module: YOLOv8n inference at 640px when weights are loaded, otherwise HOG detectMultiScale. "
            "Person-class detections (COCO class 0) above confidence threshold 0.22 are retained as "
            "bounding boxes with confidence scores.",
        ),
        (
            "Stage 3 — Tracking and Zone Assignment",
            "The CentroidTracker associates detections across frames using centroid distance and IoU "
            "matching, assigning persistent track IDs. Each track accumulates position history for speed "
            "and heading computation. Zone assignment uses point-in-polygon tests against seeded zone "
            "GeoJSON polygons (Aether Arena zones A–D). Tracks crossing zone boundaries update zone "
            "occupancy counts in real time during frame iteration.",
        ),
        (
            "Stage 4 — Zone Analytics Feature Extraction",
            "For each zone, analytics computes: density = count / area_m2; mean_speed from track "
            "displacement over recent frames; speed_drop = 1 − v_current / v_baseline; opposing_flow "
            "from heading circular variance indicating bidirectional conflict; congestion proxy combining "
            "density and speed decay; group_cohesion from local track clustering; abnormal_motion from "
            "track jerk; exit_pressure from queue length relative to exit throughput capacity.",
        ),
        (
            "Stage 5 — DCRS Evaluation and Alert Generation",
            "The DCRS engine evaluates clipped features through weighted logistic regression, producing "
            "a score in [0, 100] mapped to Green/Yellow/Orange/Red bands. The zone-graph forecaster "
            "contributes forecast_surge for 5–10 minute horizon. Alerts are created when DCRS ≥ 60 or "
            "forecast DCRS ≥ 60. Each alert persists to the alerts table with JSON-encoded ERA "
            "explanation containing top-k feature contributions and human-readable narrative.",
        ),
        (
            "Stage 6 — Gradient Boosting Recommendations",
            "The ML recommender extracts a feature vector from current zone metrics and DCRS context, "
            "runs inference through the trained MultiOutputClassifier (GradientBoostingClassifier per "
            "action label), ranks actions by predicted probability, and passes candidates through the "
            "CDSE safety filter. Unsafe actions (e.g., close last exit) are removed. Surviving actions "
            "form a DecisionBundle linked to the alert in the decisions table.",
        ),
        (
            "Stage 7 — Twin Update and Dashboard Refresh",
            "The in-memory twin store is updated with zone metrics, risk scores, active alerts, and "
            "pending decisions. The API returns a twin snapshot to the frontend. WebSocket /ws/twin "
            "pushes updates every 3 seconds for live demo mode. The DigitalTwinMap component re-renders "
            "zone colours by band; RiskCards and DecisionQueue populate with ERA and action data.",
        ),
        (
            "Stage 8 — Operator Decision and Reporting",
            "The Operator reviews recommendations and clicks Accept or Dismiss on each action card. "
            "POST /api/v1/decisions/ack records the decision with timestamp and user ID for audit. "
            "Optional what-if simulation perturbs twin parameters and re-runs DCRS. Incident report "
            "generation assembles timeline, risk analysis, interventions taken, and improvement "
            "suggestions into markdown persisted in incident_reports.",
        ),
    ]
    for title, body in stages:
        add_subsection_heading(doc, title)
        add_para(doc, body, first_line_indent=0.3)

    add_section_heading(doc, "4.12 Testing and Verification Strategy")
    add_body_block(
        doc,
        [
            "Although formal test results belong to Stage-II, the Level A implementation includes a "
            "structured verification strategy aligned with the 25-day development plan. Unit tests in "
            "backend/tests/unit/test_core_ai.py validate DCRS scoring boundaries, ERA contribution "
            "ranking, CDSE safety filter constraints, and multi-camera fusion geometry. Day verification "
            "scripts (backend/scripts/day2_verify.py through day23_verify.py) assert end-to-end "
            "behaviour for each development milestone.",
            "Scenario-based manual testing uses three sample CCTV clips: sparse_crowd.mp4 (expect Green "
            "bands), medium_crowd.mp4 (expect Yellow), and dense_crowd.mp4 (expect Orange/Red with "
            "alerts and recommendations). The demo checklist (docs/DEMO_CHECKLIST.md) defines the viva "
            "script: login as Admin, run pipeline on dense sample, show twin map colours, expand ERA "
            "card, Accept an action, run what-if with exit closure, generate incident report.",
            "Precomputed demo backup JSON in backend/data/demo_backup/ provides fallback snapshots if "
            "live YOLO inference fails during panel demonstration, ensuring graceful degradation rather "
            "than demo failure.",
        ],
    )


def add_extended_intro(doc):
    add_section_heading(doc, "1.7 Importance of Crowd Safety Analytics")
    add_body_block(
        doc,
        [
            "The socio-economic impact of crowd disasters extends beyond immediate casualties to legal "
            "liability, venue licensing, insurance costs, and public trust in event management. The 2010 "
            "Love Parade stampede in Duisburg, the 2021 Astroworld festival incident in Houston, and "
            "recurring pilgrimage corridor congestions in South Asia demonstrate that surveillance "
            "infrastructure alone does not prevent tragedy — decision latency and unclear situational "
            "assessment are recurring failure modes.",
            "Computer vision offers a scalable sensing layer because CCTV cameras are already deployed "
            "at most large venues. The research challenge is not whether cameras exist but how to convert "
            "video streams into actionable intelligence within the decision cycle of a control room. "
            "CrowdPulse positions itself at this conversion boundary: from pixels to zone metrics, from "
            "metrics to multi-factor risk, from risk to explained alerts, and from alerts to ranked "
            "interventions with human-in-the-loop approval.",
            "For the Telangana State Police and stadium authority context, the platform provides a "
            "credible academic prototype that mirrors operational control-room workflows while remaining "
            "honest about pilot maturity — single venue, file-based ingest, public detector weights, "
            "and synthetic decision labels — with a clear path to production scale-out documented in "
            "the Level B roadmap.",
        ],
    )


def build_chapter1(doc):
    add_chapter_heading(doc, "Chapter 1 — Introduction")

    add_section_heading(doc, "1.1 Motivation")
    add_para(
        doc,
        "Large public gatherings — religious festivals, stadium match days, transit hubs, concerts, and "
        "civic events — continue to produce preventable crush and congestion incidents despite the "
        "near-universal deployment of closed-circuit television (CCTV). Historical disasters at pilgrimage "
        "sites, sports venues, and concert grounds demonstrate that dense crowds can transition from "
        "orderly flow to dangerous compression within minutes. In many of these cases, camera feeds were "
        "available, but the operational gap was not a lack of video; it was the absence of timely, "
        "explainable decision support that converts pixels into prioritized actions for a control room.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Traditional surveillance practice relies on human operators scanning multiple video walls. "
        "Operators are expected to notice rising density, opposing pedestrian streams, exit queuing, and "
        "anomalous motion while simultaneously coordinating radio traffic. Under cognitive load, "
        "threshold-based high-density alarms often fire late — after a zone already looks congested on "
        "screen. Counting-only computer-vision tools improve awareness but still leave authorities without "
        "a closed loop from perception to risk explanation to recommended intervention.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "CrowdPulse is motivated by three practical needs observed in control-room settings. First, "
        "zone-level situational awareness must update continuously from CCTV or recorded footage. Second, "
        "risk must be expressed as a multi-factor score that includes density together with flow-speed "
        "decay, opposing-flow conflict, and exit pressure — signals that often precede visible crush. "
        "Third, every alert should be explainable and paired with ranked actions so that non-technical "
        "officers can accept, dismiss, or escalate decisions with an auditable trail.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "The Telangana State Police and stadium control-room scenario provides a realistic evaluation "
        "context. Venues such as Aether Arena (demo topology) represent the kind of multi-zone concourse "
        "where gate control, public-address messaging, guard redeployment, and medical standby must be "
        "coordinated under time pressure. CrowdPulse treats crowd safety as a decision-support problem "
        "rather than a detection-only problem, while remaining deployable on a standard laptop for "
        "academic and venue-pilot demonstration.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "1.2 Problem Statement")
    add_para(
        doc,
        "Existing crowd-surveillance systems do not provide an integrated mechanism that converts CCTV "
        "observations into a multi-factor Dynamic Crowd Risk Score, attaches feature-level explanations, "
        "and ranks operational interventions for a control-room operator. Most deployed and academic "
        "solutions remain reactive: they raise alerts only after a density (or simple chaos) threshold is "
        "crossed, and they stop at visualization without an Accept/Dismiss decision loop, what-if "
        "simulation, historical logging of zone risk, or role-separated authentication for Admin ingest "
        "versus Operator monitoring.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Consequently, authorities still lack a production-oriented closed loop from detection and "
        "tracking through predictive flow-speed aware early warning to explainable, recommended action. "
        "The specific unsolved problem addressed by CrowdPulse is how to transform zone-level video "
        "analytics into graded, explainable risk intelligence and ranked interventions within a secured "
        "digital-twin operations console — without requiring city-scale infrastructure or proprietary "
        "police CCTV corpora for a college-deployable pilot.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "1.3 Project Objectives")
    add_para(doc, "The primary objectives of CrowdPulse are:", space_after=4)
    objectives = [
        "Real-time density detection: Detect and track people in CCTV or sample video using YOLOv8 (with OpenCV HOG fallback), assign detections to venue zones, and compute zone occupancy and density metrics.",
        "Early-warning prediction: Combine density with predictive flow-speed and related signals (speed drop, opposing flow, exit pressure) inside a Dynamic Crowd Risk Score (DCRS) to raise graded Green / Yellow / Orange / Red warnings before conditions become unrecoverable.",
        "Centralized dashboard: Provide a secured Next.js digital-twin ops console where officers view live zone risk coloring, explanations (ERA), Gradient Boosting action recommendations, and what-if outcomes in one place.",
        "Historical logging: Persist venues, zones, alerts, decisions, processed videos, and incident reports in a schema-backed database (SQLite, Postgres-ready) to support after-action review and accountability.",
        "Explainable decision support: Attach Explainable Risk Attribution (ERA) to alerts and rank interventions with Gradient Boosting plus a deterministic safety filter (for example, never close the last exit).",
        "Role-based control-room access: Enforce JWT authentication so Operators monitor and decide, while Admins additionally run CCTV ingest and pipeline processing.",
    ]
    for o in objectives:
        add_bullet(doc, o)

    add_section_heading(doc, "1.4 Project Report Organization")
    add_para(
        doc,
        "This Stage-I report is organized into four chapters followed by references and appendix. "
        "Chapter 1 introduces the background, motivation, problem statement, objectives, and report "
        "structure. Chapter 2 presents the literature survey, covering deployed crowd-monitoring systems "
        "and academic detection, density-map, and forecasting techniques, together with identified "
        "limitations of existing work. Chapter 3 documents requirement analysis, including software, "
        "hardware, and user requirements. Chapter 4 describes the proposed system design, architecture, "
        "algorithms, UML diagrams, datasets, and technology stack. Subsequent stages of the major project "
        "will cover detailed implementation, testing, results, and conclusions.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "1.5 Scope of the Project")
    add_subsection_heading(doc, "1.5.1 In Scope (Level A)")
    for item in [
        "Single-venue pilot topology with seeded zones, cameras, and exits (Aether Arena demo venue).",
        "File-based and sample CCTV ingest with Admin-triggered pipeline processing.",
        "Person detection using YOLOv8n or OpenCV HOG fallback; centroid-IoU multi-object tracking.",
        "Zone-level analytics: density, speed drop, opposing flow, exit pressure, and related features.",
        "Dynamic Crowd Risk Score with Green / Yellow / Orange / Red bands and ERA explainability.",
        "Gradient Boosting action recommendations with deterministic safety constraints.",
        "Next.js digital-twin dashboard, Accept/Dismiss decision queue, what-if simulation, incident reports.",
        "JWT Operator / Admin authentication, structured API validation, and SQLite schema-backed persistence.",
    ]:
        add_bullet(doc, item)

    add_subsection_heading(doc, "1.5.2 Out of Scope (Level A)")
    for item in [
        "City-scale multi-camera geometric fusion and anti-double-counting across overlapping feeds.",
        "Mandatory GPU inference — the system runs on standard laptop CPU with HOG fallback.",
        "Live RTSP mosaic viewer as a completed product feature (cameras exist as seeded metadata).",
        "Full TimescaleDB hypertables, Redis stream edge fleet, and Kubernetes HA as runtime claims.",
        "Training a custom person detector on private police CCTV corpora.",
        "Legal replacement of human authority — CrowdPulse advises; officers decide.",
    ]:
        add_bullet(doc, item)

    add_section_heading(doc, "1.6 Applications")
    add_body_block(
        doc,
        [
            "CrowdPulse is applicable wherever CCTV-backed crowd safety operations require faster situational "
            "awareness than manual monitoring alone can provide. Primary application domains include stadium "
            "and sports-venue control rooms during match days and concerts; transit hub operations during "
            "peak commute and festival surges; religious and civic gathering command centers; and large "
            "commercial complexes where ingress/egress bottlenecks must be managed proactively.",
            "Within each domain, the same core pipeline applies: video ingest, person detection and tracking, "
            "zone analytics, multi-factor risk scoring, explainable alerts, and ranked interventions. The "
            "Level A pilot demonstrates this loop on a four-zone venue topology, which generalizes to larger "
            "venues by adding zones and cameras without changing the decision-support architecture.",
            "For academic evaluation, CrowdPulse also serves as a reference implementation of Clean "
            "Architecture applied to an AI-enabled operations product — separating perception, risk, "
            "explainability, decision support, simulation, and reporting into replaceable modules behind "
            "typed FastAPI contracts and a schema-backed persistence layer.",
        ],
    )
    add_extended_intro(doc)


def build_chapter2(doc):
    add_chapter_heading(doc, "Chapter 2 — Literature Survey")

    add_section_heading(doc, "2.1 Existing Work")
    add_subsection_heading(doc, "2.1.1 Deployed Operational Systems")
    add_para(
        doc,
        "Large Indian pilgrimage gatherings such as the Kumbh Mela have increasingly adopted AI-assisted "
        "command centers that fuse CCTV, drone feeds, and GIS maps to estimate crowd accumulation at "
        "ghats, corridors, and choke points. Reported capabilities typically include density heatmaps, "
        "camera-wall situational awareness, and threshold-based alerts for police and municipal authorities. "
        "These deployments prove that computer vision can operate at festival scale and that centralized "
        "dashboards improve coordination.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Hajj-oriented research and operational frameworks integrate computer vision, IoT sensing, and "
        "evacuation planning for extremely dense ritual routes. The Integrated Intelligent Framework for "
        "Crowd Control (IICCM, IEEE Access 2025) discusses tracking, behavior analysis, and planning "
        "support for authorities. Cloud big-data evacuation systems for stadium case studies combine IoT, "
        "MQTT, Kafka, and Spark-based risk scoring. These systems are valuable references for zone "
        "ontology and evacuation thinking, yet many remain broad architectural proposals or sensing-heavy "
        "pipelines without a unified explainability layer and lightweight ops console reproducible in a "
        "college venue pilot.",
        first_line_indent=0.3,
    )

    add_subsection_heading(doc, "2.1.2 Academic Detection and Counting Techniques")
    add_para(
        doc,
        "Academic crowd counting broadly splits into detection-based and density-map-based families. "
        "Detection-based pipelines use object detectors such as YOLO variants coupled with multi-object "
        "trackers like DeepSORT or ByteTrack. They work well at sparse-to-moderate density, provide "
        "bounding boxes useful for tracking speed and direction, and integrate cleanly with zone polygons. "
        "Their accuracy degrades under extreme occlusion when individual bodies are no longer separable.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Density-map approaches such as CSRNet regress a continuous density field and integrate it to "
        "obtain a count; they are stronger in extreme density but weaker at yielding per-person trajectories "
        "needed for flow-speed and opposing-flow features. Hybrid YOLO monitoring systems (IEEE Access, "
        "2023) demonstrate simultaneous count, speed, and direction estimation. IoT plus YOLO pipelines "
        "(IEEE IC-CGU, 2024) show practical live density monitoring. Encoder–Decoder LSTM multi-camera "
        "density forecasting (IEEE I2CACIS, 2024) adds short-horizon prediction beyond instantaneous count.",
        first_line_indent=0.3,
    )

    add_para(doc, "Table 2.1 — Comparison of academic crowd monitoring techniques", size=11, italic=True, align="center")
    t = doc.add_table(rows=4, cols=4)
    t.style = "Table Grid"
    fill_table(
        t,
        [
            ["Approach", "Strengths", "Weaknesses", "Relevance to CrowdPulse"],
            [
                "YOLO + tracking",
                "Person IDs, speed, direction; moderate-density real-time",
                "Fails under extreme occlusion",
                "Primary Level A path for motion features",
            ],
            [
                "CSRNet / density-map CNNs",
                "Better extreme-density counting",
                "Weak per-person trajectories",
                "Reference only; DCRS needs motion features",
            ],
            [
                "LSTM density forecast",
                "Short-horizon prediction",
                "Density-only; no decision engine",
                "Motivates forecast_surge in DCRS",
            ],
        ],
    )
    add_caption(doc, "Table 2.1. Detection-based vs density-map techniques.")

    add_subsection_heading(doc, "2.1.3 Recent IEEE-Oriented Research (2023–2025)")
    add_para(
        doc,
        "Recent publications advance hybrid YOLO counting with speed and direction estimation, IoT+YOLO live "
        "density pipelines, encoder–decoder LSTM multi-camera density forecasting, and conceptual "
        "stampede-prevention stacks coupling YOLOv8 with short LSTM horizons (IEEE GIEST, 2025). Parallel "
        "work explores digital-twin hazard identification (D-Shield, 2025) and offline XAI for evacuation "
        "optimization. Dual-metric stampede risk using YOLOv11 plus optical-flow chaos score (2025) "
        "introduces graded alerts from density and chaos together. Across this corpus, perception quality "
        "has improved substantially.",
        first_line_indent=0.3,
    )

    add_para(doc, "Table 2.2 — Selected papers and implications", size=11, italic=True, align="center")
    t2 = doc.add_table(rows=7, cols=4)
    t2.style = "Table Grid"
    fill_table(
        t2,
        [
            ["S.No", "Work / Theme", "Implication", "Gap vs CrowdPulse"],
            ["1", "Hybrid YOLOv4 monitoring (2023)", "Count + speed + direction feasible", "No multi-factor DCRS / action cards"],
            ["2", "IoT + YOLO counting (2024)", "Practical live density pipelines", "Detection-centric; weak XAI"],
            ["3", "Encoder–Decoder LSTM forecast (2024)", "Multi-camera density forecast", "No decision engine / twin ops"],
            ["4", "YOLOv8 + LSTM stampede alerts (2025)", "Short-horizon graded alerts", "No Accept/Dismiss DSS loop"],
            ["5", "IICCM Hajj framework (2025)", "Integrated control architecture", "Limited unified XAI + what-if"],
            ["6", "XAI evacuation optimization (2025)", "Explanations help planning", "Mostly offline; not live CCTV twin"],
        ],
    )
    add_caption(doc, "Table 2.2. Literature snapshot (2023–2025).")

    add_section_heading(doc, "2.2 Limitations of Existing Work")
    add_para(
        doc,
        "The central limitation across deployed and academic systems is reactivity without decision closure. "
        "Most existing work alerts only once density (or a dual density–chaos metric) crosses a threshold. "
        "That is necessary but insufficient: crush risk often builds through slowing flow, bidirectional "
        "conflict, and exit pressure before raw headcount looks catastrophic. Few systems ship an "
        "operator-facing loop that scores multi-factor risk including flow-speed decay, explains the score, "
        "recommends actions, and logs decisions for audit.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Additional limitations identified in the literature review include: (1) fragmented digital twins "
        "that rarely fuse anti-double-count multi-camera analytics with live risk coloring; (2) opaque alerts "
        "without causal feature attributions; (3) absence of what-if simulation on a live venue twin; "
        "(4) missing resource optimization for guards, medical teams, and gate control; (5) weak historical "
        "hotspot learning across recurring events; (6) no automated after-action incident reporting; and "
        "(7) edge–cloud architectures that lack a shared zone ontology for scalable decision support.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "CrowdPulse addresses these limitations by elevating predictive flow-speed signals inside DCRS, "
        "attaching ERA explanations, ranking interventions with Gradient Boosting under safety constraints, "
        "and presenting everything in a JWT-secured digital-twin dashboard with Accept/Dismiss workflow, "
        "what-if simulation, and incident reporting — deployable as a single-venue Level A pilot.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "2.3 Comparative Analysis of Detection Approaches")
    add_body_block(
        doc,
        [
            "Redmon et al. introduced YOLO, framing object detection as a single regression problem over a "
            "grid, enabling real-time inference suitable for control-room refresh rates. Subsequent YOLO "
            "variants (v4 through v8) improved accuracy–speed trade-offs. For CrowdPulse, YOLOv8n (nano) "
            "was selected because it balances inference speed on commodity hardware with sufficient person-class "
            "recall for moderate-density venue zones. When GPU or model weights are unavailable, OpenCV HOG "
            "provides a deterministic CPU fallback so the demo pipeline never fails silently.",
            "Wojke et al. proposed DeepSORT, combining Kalman filtering with deep appearance descriptors "
            "for online multi-object tracking. DeepSORT remains a strong baseline for identity continuity "
            "across frames. CrowdPulse Level A uses a lighter centroid-IoU tracker to avoid additional deep "
            "model dependencies while still producing track-level speed and heading estimates needed for "
            "opposing-flow and speed-drop features. ByteTrack is planned for Level B when multi-camera "
            "continuity becomes critical.",
            "Li et al. proposed CSRNet, a dilated-convolution density-map regressor designed for highly "
            "congested scenes where individual detection fails. CSRNet excels at counting in extreme "
            "density but does not naturally yield per-person trajectories. Because DCRS explicitly includes "
            "speed_drop and opposing_flow — features derived from track kinematics — CrowdPulse prioritizes "
            "detection+tracking over pure density-map regression for Level A, while acknowledging CSRNet "
            "as a complementary path for future hybrid fusion at extreme density.",
        ],
    )

    add_section_heading(doc, "2.4 Research Gap Summary")
    add_body_block(
        doc,
        [
            "Cross-cutting analysis of fourteen IEEE and peer-reviewed sources (2023–2025) reveals ten "
            "persistent gaps: (1) reactive vs predictive alerting; (2) detection without ranked decisions; "
            "(3) fragmented digital twins; (4) opaque alerts; (5) no closed-loop what-if simulation; "
            "(6) missing resource optimization; (7) weak historical hotspot learning; (8) no GenAI "
            "after-action reporting; (9) edge–cloud split without shared zone ontology; and (10) "
            "single-metric risk (density-only or density+chaos). CrowdPulse targets gaps 1–5 and 10 "
            "directly in Level A, with gaps 6–9 addressed in the design roadmap.",
            "The STDCformer spatial–temporal transformer (Information Fusion, 2025) advances crowd flow "
            "prediction through causal de-confounding but remains a research model without an operations "
            "platform. Smart building evacuation systems with explainable Re-ID (Engineering Applications "
            "of AI, 2025) improve multi-camera identity continuity during evacuations but do not provide "
            "predictive venue-risk twinning. WiFi–video dual-attention fusion (IEEE TMC, 2024) stabilizes "
            "large-area counting but does not translate sensing fusion into operational decision cards.",
            "These findings justify CrowdPulse as a systems-integration contribution: not merely another "
            "detector or density estimator, but a closed-loop decision-support platform that combines "
            "perception, multi-factor risk, explainability, ML-ranked actions, digital-twin visualization, "
            "simulation, and reporting in one deployable stack.",
        ],
    )

    add_para(doc, "Table 2.3 — Cross-cutting literature gaps", size=11, italic=True, align="center")
    gt = doc.add_table(rows=7, cols=3)
    gt.style = "Table Grid"
    fill_table(
        gt,
        [
            ["Gap ID", "Description", "CrowdPulse response"],
            ["G1", "Reactive density-only alerts", "DCRS multi-factor + forecast_surge"],
            ["G2", "No ranked interventions", "Gradient Boosting + safety filter"],
            ["G3", "Opaque risk scores", "ERA feature attributions + narrative"],
            ["G4", "No operator decision loop", "Accept/Dismiss queue with audit log"],
            ["G5", "No what-if planning", "Scenario simulator on live twin"],
            ["G6", "Weak historical learning", "Hotspot priors per zone / event phase"],
        ],
    )
    add_caption(doc, "Table 2.3. Literature gaps and CrowdPulse design responses.")
    add_extended_literature(doc)


def build_chapter3(doc, diagrams):
    add_chapter_heading(doc, "Chapter 3 — Requirement Analysis")
    add_para(
        doc,
        "Requirement analysis identifies the software, hardware, and user capabilities required to build "
        "CrowdPulse as a control-room oriented venue pilot. Requirements are written so that non-technical "
        "officers receive a clear dashboard, while the engineering stack remains modular and replaceable "
        "under Clean Architecture principles.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "3.1 Software Requirements")
    add_para(doc, "Table 3.1 — Functional requirements", size=11, italic=True, align="center")
    fr = doc.add_table(rows=9, cols=3)
    fr.style = "Table Grid"
    fill_table(
        fr,
        [
            ["ID", "Requirement", "Description"],
            ["FR-1", "Authentication", "JWT login; Operator and Admin roles with RBAC."],
            ["FR-2", "Video input", "Admin uploads CCTV clips or selects sample sparse/medium/dense footage."],
            ["FR-3", "Detection & tracking", "YOLOv8n / HOG person detection; centroid-IoU tracking."],
            ["FR-4", "Risk calculation", "Zone DCRS with G/Y/O/R bands and ERA explanations."],
            ["FR-5", "Dashboard", "Digital twin map and panels refresh with metrics and decisions."],
            ["FR-6", "Alerts", "Raised from DCRS thresholds with explainable narratives."],
            ["FR-7", "Historical logging", "Venues, zones, alerts, decisions, videos, reports persisted."],
            ["FR-8", "Simulation", "What-if scenarios and Accept/Dismiss decision workflow."],
        ],
    )
    add_caption(doc, "Table 3.1. Functional requirements.")

    add_para(doc, "Table 3.2 — Non-functional requirements", size=11, italic=True, align="center")
    nfr = doc.add_table(rows=8, cols=3)
    nfr.style = "Table Grid"
    fill_table(
        nfr,
        [
            ["ID", "Requirement", "Description"],
            ["NFR-1", "Performance", "Interactive pipeline latency suitable for demo refresh on laptop CPU."],
            ["NFR-2", "Scalability", "Multi-zone venue support; Postgres-ready schema."],
            ["NFR-3", "Usability", "Risk colours, short ERA explanations, action cards for officers."],
            ["NFR-4", "Security", "JWT, env secrets, Pydantic input validation."],
            ["NFR-5", "Reliability", "Graceful empty-video, detection-failure, and HOG fallback handling."],
            ["NFR-6", "Maintainability", "Replaceable modules: perception, risk, decision, simulation."],
            ["NFR-7", "Compatibility", "Modern desktop browsers; Python 3.10+ backend."],
        ],
    )
    add_caption(doc, "Table 3.2. Non-functional requirements.")

    add_para(doc, "Software stack components:", bold=True, space_after=4)
    for item in [
        "Backend: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy (async), SQLite / Postgres.",
        "AI/ML: Ultralytics YOLOv8n, OpenCV, NumPy, scikit-learn Gradient Boosting.",
        "Frontend: Node.js LTS, Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts, Zustand.",
        "Auth: PyJWT, bcrypt; optional Docker Compose for packaged deployment.",
        "Development: VS Code, Git, Postman / OpenAPI Swagger at /docs.",
    ]:
        add_bullet(doc, item)

    add_section_heading(doc, "3.2 Hardware Requirements")
    add_para(
        doc,
        "CrowdPulse is intentionally feasible on a standard laptop without a dedicated GPU. GPU acceleration "
        "can speed YOLO inference when available, but it is not required for Level A because OpenCV HOG "
        "provides a CPU fallback and frame sampling keeps compute bounded.",
        first_line_indent=0.3,
    )
    for item in [
        "Processor: Intel Core i5 / AMD Ryzen 5 or higher (i3 minimum for light demo).",
        "RAM: Minimum 8 GB (16 GB recommended when enabling YOLOv8n).",
        "Storage: At least 20 GB free for packages, models, sample videos, and database.",
        "Display: 1366×768 or higher for the ops dashboard.",
        "Network: Localhost demo after dependency install; internet for initial setup only.",
        "GPU: Not required (explicit feasibility constraint for college / venue pilot laptops).",
    ]:
        add_bullet(doc, item)

    add_section_heading(doc, "3.3 User Requirements")
    add_para(
        doc,
        "CrowdPulse serves two primary user roles in the control-room context. The Operator (Officer) "
        "monitors the digital twin, reviews risk alerts with ERA explanations, accepts or dismisses "
        "recommended actions, runs what-if scenarios, and generates incident reports. The Admin additionally "
        "uploads CCTV footage, registers sample videos, triggers the end-to-end pipeline, and resets demo "
        "metrics when required.",
        first_line_indent=0.3,
    )
    add_figure(doc, diagrams["usecase"], "Figure 3.1. Use case diagram — Operator and Admin actors.")

    for title, body in [
        ("UC-1 Login", "User authenticates; system issues JWT and enforces role permissions."),
        ("UC-2 View Dashboard", "User inspects zone colours, DCRS bands, alerts, and decision queue."),
        ("UC-3 Process Footage", "Admin runs detect→track→DCRS→recommend pipeline on sample or uploaded video."),
        ("UC-4 Receive Alert", "Dashboard presents alert with ERA top contributing factors."),
        ("UC-5 Accept / Dismiss", "Operator records decision on GB recommendation for audit trail."),
        ("UC-6 What-If Simulation", "User perturbs exits, weather, or ingress; system re-scores twin."),
        ("UC-7 Incident Report", "User generates after-action markdown summary of timeline and decisions."),
    ]:
        add_para(doc, title, bold=True, align="left", space_after=2)
        add_para(doc, body, first_line_indent=0.2, space_after=6)

    add_section_heading(doc, "3.4 System Constraints and Assumptions")
    add_body_block(
        doc,
        [
            "The following constraints shape the Level A design. First, video input is file-based (uploaded "
            "MP4 or procedurally generated sample clips) rather than continuous live RTSP ingest — this "
            "ensures reproducible academic demonstration without dependency on venue network infrastructure. "
            "Second, person detection relies on public COCO-pretrained YOLOv8n weights; no custom detector "
            "training on private CCTV corpora is performed. Third, the Gradient Boosting recommender is "
            "trained on synthetic multi-label scenarios because real labeled operator decisions require "
            "venue-specific standard operating procedures not available in a college project context.",
            "Assumptions include: (a) venue zones are defined as static polygons with known capacity and "
            "exit topology; (b) camera views can be mapped to zones (homography metadata seeded for future "
            "multi-camera fusion); (c) officers have desktop browsers and network access to the ops console; "
            "(d) human authority retains final decision power — CrowdPulse recommends but does not autonomously "
            "execute gate closures or evacuations.",
        ],
    )

    add_section_heading(doc, "3.5 Security Requirements")
    add_body_block(
        doc,
        [
            "Security requirements follow production-oriented patterns appropriate for a control-room pilot. "
            "Authentication uses JWT tokens issued after bcrypt password verification. All operational APIs "
            "require a valid Bearer token except login and public health endpoints. Role-based access control "
            "separates Operator (read + decide) from Admin (read + decide + ingest + pipeline). Secrets "
            "(SECRET_KEY, token expiry) are configured via environment variables, not hardcoded in source. "
            "API inputs are validated with Pydantic models to prevent malformed requests from corrupting "
            "pipeline state.",
        ],
    )
    for item in [
        "Operator role: view twin, risk alerts, decisions, what-if, reports — cannot upload or run pipeline.",
        "Admin role: all Operator capabilities plus video upload, process, pipeline run, twin metric reset.",
        "Demo accounts: tsp.operator / tsp.admin with venue-specific passwords (seeded, changeable via env).",
        "CORS origins configured via CORS_ORIGINS environment variable for frontend integration.",
    ]:
        add_bullet(doc, item)

    add_section_heading(doc, "3.6 Interface Requirements")
    add_body_block(
        doc,
        [
            "The operator interface is implemented as a Next.js web application styled for control-room "
            "readability: dark theme, IBM Plex typography, zone choropleth coloured by DCRS band (Green / "
            "Yellow / Orange / Red), expandable risk cards with ERA narratives, and a decision queue with "
            "Accept and Dismiss buttons. Recharts provides density and DCRS trend visualizations. The "
            "interface refreshes from REST snapshot polling and WebSocket twin push (every 3 seconds).",
            "The machine interface is a FastAPI REST API documented at /docs (Swagger UI). Key integration "
            "points include POST /api/v1/pipeline/run for end-to-end processing, GET /api/v1/twin/snapshot "
            "for dashboard state, GET /api/v1/risk/alerts for ERA-enriched alerts, and POST /api/v1/decisions/ack "
            "for operator decisions. All responses use typed JSON schemas for frontend consumption.",
        ],
    )

    add_section_heading(doc, "3.7 Summary")
    add_body_block(
        doc,
        [
            "Chapter 3 established the contractual requirements for CrowdPulse: authenticated video-to-decision "
            "workflows, multi-factor risk with early-warning signals, a usable ops dashboard, security via "
            "JWT and RBAC, and historical logging — all runnable on a CPU-only laptop for a venue pilot. "
            "These requirements directly drive the system design presented in Chapter 4.",
        ],
    )


def build_chapter4(doc, diagrams):
    add_chapter_heading(doc, "Chapter 4 — System Design")

    add_section_heading(doc, "4.0 Proposed System Architecture")
    add_para(
        doc,
        "CrowdPulse follows Clean Architecture with four logical layers: Presentation (Next.js ops console), "
        "API (FastAPI REST + JWT + WebSocket), Application (use-cases: process video, run pipeline, evaluate "
        "risk), and AI plus Infrastructure (detection, tracking, DCRS, ERA, Gradient Boosting, database, "
        "twin store, video files). This separation ensures each module is scalable and replaceable — for "
        "example, swapping centroid-IoU tracking for ByteTrack in Level B without rewriting the dashboard.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "The end-to-end data flow is: CCTV or sample video → frame sampling → person detection (YOLOv8n or "
        "HOG) → centroid-IoU tracking → zone assignment → zone analytics → DCRS evaluation → ERA "
        "explanation → Gradient Boosting recommendations → safety filter → digital twin update → operator "
        "Accept/Dismiss → optional what-if → incident report and database persistence.",
        first_line_indent=0.3,
    )
    add_figure(doc, diagrams["architecture"], "Figure 4.1. Proposed Level A system architecture.")

    add_section_heading(doc, "4.1 Proposed Methods / Algorithms")

    add_subsection_heading(doc, "4.1.1 Person Detection and Tracking")
    add_para(
        doc,
        "Person detection uses Ultralytics YOLOv8n with COCO person class (class 0) when weights are "
        "available. Configuration includes confidence threshold 0.22, image size 640, and IoU 0.45. "
        "If YOLO fails to load, OpenCV HOG with default people SVM provides a CPU fallback. Detections are "
        "associated across frames using a CentroidTracker that matches by centroid distance and bounding-box "
        "IoU, enabling per-track speed and heading estimation.",
        first_line_indent=0.3,
    )

    add_subsection_heading(doc, "4.1.2 Zone Analytics")
    add_para(
        doc,
        "Tracked persons are assigned to polygonal venue zones via point-in-polygon tests. Per-zone metrics "
        "include: density (count / area), mean speed from track displacement, speed drop relative to baseline, "
        "opposing-flow conflict via heading circular variance, congestion proxy, group cohesion, abnormal "
        "motion, and exit pressure (queue length / exit throughput). These features deliberately extend "
        "beyond headcount so early-warning behaviour can emerge before a pure density threshold trips.",
        first_line_indent=0.3,
    )

    add_subsection_heading(doc, "4.1.3 Dynamic Crowd Risk Score (DCRS)")
    add_para(
        doc,
        "DCRS maps clipped multi-factor features through a weighted logistic transform: "
        "logit = bias + Σ w_i · clip(φ_i); DCRS = 100 · sigmoid(logit). Alerts are raised when "
        "DCRS ≥ 60 or forecast DCRS at t+10 minutes ≥ 60. A lightweight zone-graph forecaster supplies "
        "forecast_surge for predictive early warning.",
        first_line_indent=0.3,
    )

    add_para(doc, "Table 4.1 — DCRS feature definitions", size=11, italic=True, align="center")
    ft = doc.add_table(rows=8, cols=3)
    ft.style = "Table Grid"
    fill_table(
        ft,
        [
            ["Feature", "Definition", "Range"],
            ["density_norm", "persons/m² relative to capacity", "[0, 2+]"],
            ["speed_drop", "1 − v_t / v_baseline", "[0, 1]"],
            ["opposing_flow", "bidirectional flow conflict", "[0, 1]"],
            ["exit_pressure", "queue / exit throughput", "[0, 2+]"],
            ["forecast_surge", "predicted Δdensity over horizon", "[0, 2+]"],
            ["historical_hotspot", "empirical congestion prior", "[0, 1]"],
            ["weather_factor", "rainfall / heat penalty", "[0, 1]"],
        ],
    )
    add_caption(doc, "Table 4.1. Primary DCRS input features.")

    add_para(doc, "Table 4.2 — Risk band classification", size=11, italic=True, align="center")
    bt = doc.add_table(rows=5, cols=2)
    bt.style = "Table Grid"
    fill_table(
        bt,
        [
            ["Band", "DCRS Range"],
            ["Green", "< 40"],
            ["Yellow", "40 – 60"],
            ["Orange", "60 – 80"],
            ["Red", "≥ 80"],
        ],
    )
    add_caption(doc, "Table 4.2. DCRS risk band mapping.")

    add_subsection_heading(doc, "4.1.4 Explainable Risk Attribution (ERA)")
    add_para(
        doc,
        "ERA ranks feature contributions by weighted impact on the DCRS logit and generates a short "
        "human-readable narrative for alert cards. Top-k drivers (for example, speed drop, exit pressure, "
        "opposing flow) are exposed via the API as narrative, contributions JSON, and top_labels. This "
        "addresses opaque threshold alarms common in prior reactive systems and reduces alert fatigue by "
        "telling officers why a zone is flagged.",
        first_line_indent=0.3,
    )

    add_subsection_heading(doc, "4.1.5 Gradient Boosting Decision Support")
    add_para(
        doc,
        "A scikit-learn GradientBoostingClassifier wrapped in MultiOutputClassifier ranks candidate "
        "interventions: open_exit, close_exit, deploy_guards, redirect_zone, activate_pa, deploy_medical, "
        "route_evacuation, hold_ingress. Training uses synthetic multi-label scenarios derived from "
        "expert-style rules over feature ranges (~3000 samples). A deterministic safety layer filters unsafe "
        "recommendations (never close the last exit). Benchmark: GB F1-micro 0.9983 vs Random Forest 0.9974.",
        first_line_indent=0.3,
    )

    add_para(doc, "Table 4.3 — Recommender benchmark (synthetic dataset)", size=11, italic=True, align="center")
    rt = doc.add_table(rows=3, cols=3)
    rt.style = "Table Grid"
    fill_table(
        rt,
        [
            ["Model", "F1-micro", "Exact Match"],
            ["Gradient Boosting", "0.9983", "0.9907"],
            ["Random Forest", "0.9974", "0.9853"],
        ],
    )
    add_caption(doc, "Table 4.3. Gradient Boosting selected as primary recommender.")

    add_subsection_heading(doc, "4.1.6 What-If Simulation and Incident Reporting")
    add_para(
        doc,
        "The what-if simulator perturbs twin state with scenarios such as exit closure, rainfall, VIP zone "
        "hold, and ingress hold, then re-computes peak DCRS and congested zones. Incident reporting assembles "
        "Executive Summary, Timeline, Risk Analysis, Interventions, Hotspots, and Improvements sections using "
        "a structured template with optional Ollama LLM enhancement.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "4.2 Class / Use Case / Activity / Sequence Diagrams")
    add_para(
        doc,
        "Figure 4.2 presents the core domain classes and AI engines. Figure 4.3 shows the sequence of "
        "interactions when an Admin triggers the one-click pipeline. The use case diagram was presented "
        "in Chapter 3 (Figure 3.1). Activity flows follow the pipeline: authenticate → select video → "
        "detect → track → assign zones → compute DCRS → explain → recommend → update twin → operator decision.",
        first_line_indent=0.3,
    )
    add_figure(doc, diagrams["class"], "Figure 4.2. Core class diagram (domain entities and AI engines).")
    add_figure(doc, diagrams["sequence"], "Figure 4.3. Sequence diagram — Admin pipeline run.")

    add_section_heading(doc, "4.3 Datasets and Technology Stack")

    add_subsection_heading(doc, "4.3.1 Datasets")
    add_para(
        doc,
        "Person detection uses public pretrained YOLOv8n weights (COCO person class); no custom detector "
        "training is performed for Level A. The Gradient Boosting recommender is trained on synthetic "
        "multi-factor crowd-risk scenarios with rule-derived multi-label actions — ethical and reproducible "
        "for academic evaluation. Demo CCTV clips (sparse_crowd.mp4, medium_crowd.mp4, dense_crowd.mp4) are "
        "generated procedurally with OpenCV for reproducible demonstration without copyrighted footage.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Venue topology is seeded as Aether Arena with zones A–D, exits, and camera metadata in SQLite. "
        "Historical hotspot priors are stored per zone and event phase. The project does not claim a private "
        "police CCTV corpus; real footage can be uploaded by Admin when available.",
        first_line_indent=0.3,
    )

    add_para(doc, "Table 4.5 — Demo venue zone topology", size=11, italic=True, align="center")
    zt = doc.add_table(rows=5, cols=4)
    zt.style = "Table Grid"
    fill_table(
        zt,
        [
            ["Zone", "Name", "Capacity", "Exits"],
            ["A", "North Concourse", "800", "Gate-A, Gate-B"],
            ["B", "Central Bowl", "1600", "Gate-B, Gate-C"],
            ["C", "East Corridor", "500", "Gate-C"],
            ["D", "South Plaza", "900", "Gate-D, Gate-E"],
        ],
    )
    add_caption(doc, "Table 4.5. Aether Arena demo zones.")

    add_subsection_heading(doc, "4.3.2 Technology Stack")
    add_para(doc, "Table 4.4 — Technology stack by module", size=11, italic=True, align="center")
    ts = doc.add_table(rows=9, cols=3)
    ts.style = "Table Grid"
    fill_table(
        ts,
        [
            ["Module", "Technologies", "Purpose"],
            ["Frontend", "Next.js 14, React, TypeScript, Tailwind, Recharts", "Ops dashboard"],
            ["API", "FastAPI, Pydantic, Uvicorn, JWT", "REST + WebSocket services"],
            ["Perception", "YOLOv8n, OpenCV HOG, centroid-IoU tracker", "Detect + track"],
            ["Risk / XAI", "Custom DCRS, ERA attributor", "Scoring + explanations"],
            ["Decision", "scikit-learn Gradient Boosting, safety filter", "Action ranking"],
            ["Simulation", "What-if engine", "Scenario planning"],
            ["Reporting", "Template markdown, optional Ollama", "Incident reports"],
            ["Data", "SQLAlchemy, SQLite, twin store", "Persistence + live state"],
        ],
    )
    add_caption(doc, "Table 4.4. Module-wise technology stack.")

    add_para(
        doc,
        "Database schema (Level A implemented tables): users, venues, zones, cameras, alerts, decisions, "
        "simulations, incident_reports, historical_hotspots, video_assets, detection_runs, risk_snapshots. "
        "Level B extensions planned include TimescaleDB hypertables for detections and fused_counts, Redis "
        "streams for edge publishing, and multi-camera fusion with homography-based anti-double-counting.",
        first_line_indent=0.3,
    )

    add_section_heading(doc, "4.4 Database Design")
    add_body_block(
        doc,
        [
            "The persistence layer uses SQLAlchemy async ORM with SQLite as the Level A runtime database "
            "and Postgres/TimescaleDB as the Level B migration target. All operational entities — venues, "
            "zones, cameras, users, alerts, decisions, videos, detection runs, risk snapshots, simulations, "
            "incident reports, and historical hotspots — are defined as first-class tables rather than "
            "hard-coded dictionaries, ensuring schema-backed design suitable for production evolution.",
            "The entity-relationship model follows a venue-centric topology: a venue contains multiple zones "
            "and cameras; zones produce risk snapshots and alerts; alerts yield decisions with JSON-encoded "
            "action bundles; videos link to detection runs that store engine type, summary metrics, and "
            "frame timeline. Historical hotspots capture empirical congestion priors per zone and event phase, "
            "feeding the historical_hotspot feature in DCRS.",
        ],
    )

    add_para(doc, "Table 4.6 — Implemented database tables (Level A)", size=11, italic=True, align="center")
    db_t = doc.add_table(rows=13, cols=3)
    db_t.style = "Table Grid"
    fill_table(
        db_t,
        [
            ["Table", "Primary purpose", "Key fields"],
            ["users", "Control-room accounts", "username, password_hash, role"],
            ["venues", "Venue topology", "name, timezone, boundary GeoJSON"],
            ["zones", "Zone polygons", "code, polygon, capacity, exits, adjacent"],
            ["cameras", "Camera metadata", "code, stream_url, homography, fps"],
            ["alerts", "Risk alerts", "zone_id, severity, dcrs, band, explanation JSON"],
            ["decisions", "Decision bundles", "alert_id, rationale, actions JSON"],
            ["video_assets", "Uploaded/sample videos", "filename, storage_path, status"],
            ["detection_runs", "CV pipeline output", "video_id, engine, summary, timeline"],
            ["risk_snapshots", "Persisted DCRS", "zone_id, dcrs, band, metrics, features"],
            ["simulations", "What-if runs", "venue_id, scenario JSON, result JSON"],
            ["incident_reports", "After-action reports", "event_name, markdown, pdf_uri"],
            ["historical_hotspots", "Zone priors", "zone_id, event_phase, score"],
        ],
    )
    add_caption(doc, "Table 4.6. Level A SQLAlchemy models.")

    add_section_heading(doc, "4.5 API Design")
    add_body_block(
        doc,
        [
            "The FastAPI application exposes versioned REST endpoints under /api/v1 with JWT authentication "
            "via HTTP Bearer tokens. Public endpoints include GET /health (service and database health) and "
            "POST /api/v1/auth/login (credential exchange for JWT). Protected endpoints enforce role checks "
            "through dependency injection: pipeline and video upload require Admin role; twin, risk, and "
            "decision endpoints require any authenticated user.",
            "The one-click pipeline endpoint POST /api/v1/pipeline/run orchestrates the full chain: resolve "
            "video source (upload, sample, or latest), sample frames with configurable stride, run detection "
            "and tracking, assign zones, compute analytics, evaluate DCRS, generate ERA explanations, rank "
            "Gradient Boosting actions, update the in-memory twin store, persist snapshots to the database, "
            "and return the twin snapshot to the caller. This endpoint is the primary viva demonstration path.",
        ],
    )

    add_para(doc, "Table 4.7 — Key REST API endpoints", size=11, italic=True, align="center")
    api_t = doc.add_table(rows=12, cols=3)
    api_t.style = "Table Grid"
    fill_table(
        api_t,
        [
            ["Method", "Endpoint", "Description"],
            ["POST", "/api/v1/auth/login", "JWT authentication"],
            ["GET", "/api/v1/venues/demo", "Demo venue with zones and cameras"],
            ["POST", "/api/v1/videos/upload", "Multipart CCTV upload (Admin)"],
            ["POST", "/api/v1/pipeline/run", "Full end-to-end pipeline (Admin)"],
            ["GET", "/api/v1/twin/snapshot", "Digital twin state"],
            ["GET", "/api/v1/risk/alerts", "Alerts with ERA explanations"],
            ["POST", "/api/v1/risk/evaluate", "Run DCRS on current twin"],
            ["GET", "/api/v1/decisions", "Decision queue"],
            ["POST", "/api/v1/decisions/ack", "Accept/Dismiss action"],
            ["POST", "/api/v1/simulation/what-if", "Scenario simulation"],
            ["POST", "/api/v1/reports/incident", "Generate incident report"],
        ],
    )
    add_caption(doc, "Table 4.7. Primary API endpoints.")

    add_section_heading(doc, "4.6 Frontend Design")
    add_body_block(
        doc,
        [
            "The Next.js 14 frontend implements a control-room operations console with the following "
            "component modules. DigitalTwinMap renders zone polygons coloured by DCRS risk band with "
            "hover metrics. RiskCards displays expandable DCRS cards with ERA top contributing factors. "
            "DecisionQueue presents Gradient Boosting recommendations with Accept and Dismiss actions. "
            "VideoUploadPanel (Admin) supports multipart upload and sample video selection. WhatIfPanel "
            "accepts scenario parameters (exit closure, rainfall, VIP hold, ingress hold) and displays "
            "re-scored twin outcomes. HotspotPanel ranks historical congestion priors. TrendChart plots "
            "density and DCRS time series. ReportPanel triggers incident report generation.",
            "State management uses Zustand for client-side auth token and twin snapshot caching. The API "
            "client (services/api.ts) centralizes fetch calls with JWT header injection. Authentication "
            "flow redirects unauthenticated users to the login page; role-gated UI elements hide Admin-only "
            "controls from Operator accounts.",
        ],
    )

    add_section_heading(doc, "4.7 Deployment Architecture")
    add_body_block(
        doc,
        [
            "CrowdPulse is Docker-ready via docker-compose.yml in infra/docker/, defining services for "
            "Postgres (TimescaleDB PG16), Redis, MinIO object storage, FastAPI backend, Next.js frontend, "
            "and an optional edge profile. For Level A academic demonstration, the stack runs natively: "
            "uvicorn backend on port 8000 and next dev/build frontend on port 3000, with SQLite file at "
            "backend/data/crowdpulse.db.",
            "Kubernetes deployment manifest (infra/k8s/api-deployment.yaml) provides a scale-out path for "
            "Level B. Environment configuration uses pydantic-settings reading from .env: DATABASE_URL, "
            "SECRET_KEY, AUTH_REQUIRED, YOLO_MODEL_NAME, CORS_ORIGINS, and related keys. Model warmup "
            "on startup pre-loads YOLO weights and the Gradient Boosting joblib file to avoid first-request "
            "latency during live demonstration.",
        ],
    )

    add_section_heading(doc, "4.8 Module Implementation Summary")
    add_body_block(
        doc,
        [
            "Backend modules follow Clean Architecture boundaries. The api layer (backend/app/api/) defines "
            "route handlers and JWT dependencies. The application layer (backend/app/application/use_cases/) "
            "implements run_pipeline, process_video, and evaluate_risk orchestration. The domain layer "
            "(backend/app/domain/entities/crowd.py) defines Pydantic entities: RiskBand, ZoneMetrics, "
            "RiskScore, RiskExplanation, DecisionAction, DecisionBundle, SimulationScenario, and "
            "SimulationResult. The AI layer (backend/app/ai/) contains perception, risk, xai, decision, "
            "simulation, reporting, forecasting, and fusion subpackages. Infrastructure "
            "(backend/app/infrastructure/) provides database models, seed data, twin store, and video storage.",
            "Development progressed through a structured 25-day Level A plan (Days 1–23 complete at Stage-I "
            "submission). Milestones included: project scaffold and health endpoints (Day 1–2), venue seed "
            "and twin store (Day 3–5), YOLO detection and tracking (Day 6–8), zone analytics and DCRS "
            "(Day 9–11), ERA and Gradient Boosting (Day 12–14), dashboard and decision queue (Day 15–17), "
            "what-if and incident reports (Day 18–20), auth and pipeline integration (Day 21–23). Each day "
            "has a verification script in backend/scripts/ and a completion log in docs/DAY*_COMPLETE.md.",
        ],
    )

    add_section_heading(doc, "4.9 Future Scope (Level B)")
    add_body_block(
        doc,
        [
            "Level B extensions planned beyond Stage-I include: ByteTrack multi-object tracking in the "
            "production pipeline; multi-camera fusion with homography projection and spatial clustering "
            "for anti-double-counting; Temporal Fusion Transformer and Graph Neural Network forecasting "
            "with trained weights replacing the lightweight statistical forecaster; full TimescaleDB "
            "hypertables for detections and fused_counts; live RTSP camera ingest; edge YOLO nodes "
            "publishing to Redis Streams; ONNX edge deployment; Celery workers for async video processing; "
            "Prometheus/Grafana observability; and optional Keycloak production authentication.",
            "These extensions are documented in FUTURE_SCOPE.md and the full IEEE-oriented PROJECT_DESIGN.md "
            "(research name VigilantTwin). Level A honestly delivers a single-venue academic pilot; Level B "
            "targets production venue scale without changing the core decision-support architecture.",
        ],
    )

    add_section_heading(doc, "4.10 Chapter Summary")
    add_body_block(
        doc,
        [
            "Chapter 4 presented the complete system design of CrowdPulse: Clean Architecture layering, "
            "the perception-to-decision pipeline, DCRS and ERA algorithms, Gradient Boosting recommender "
            "with safety filter, UML diagrams, database schema, API contracts, frontend modules, deployment "
            "topology, and technology stack. Together with Chapters 1–3, this Stage-I report documents the "
            "problem, literature gap, requirements, and proposed design sufficient for internal evaluation "
            "and subsequent implementation testing in Stage-II.",
        ],
    )
    add_extended_design(doc)
    add_activity_diagram_section(doc)


def build_references_and_appendix(doc):
    add_page_break(doc)
    add_para(doc, "REFERENCES", size=14, bold=True, align="center", space_after=12)
    refs = [
        "[1] Hwanam Kim, Byungchul Choi, Effect of ethanol diesel blend fuels on emission and particle size distribution in a common-rail direct injection diesel engine with warm-up catalytic converter, Renewable Energy, Vol. 33, Issue 10, pp. 2222-2228, 2008.",
        "[2] Realtime Crowd Monitoring—Estimating Count, Speed and Direction Using Hybridized YOLOv4, IEEE Access, 2023.",
        "[3] Integrated Crowd Counting Using IoT, OpenCV and YOLO, IEEE IC-CGU, 2024.",
        "[4] Crowd Density Forecasting with Distributed Cameras using Encoder–Decoder LSTM, IEEE I2CACIS, 2024.",
        "[5] A Novel AI-Based Predictive Crowd Monitoring and Stampede Prevention, IEEE GIEST, 2025.",
        "[6] Toward an Integrated Intelligent Framework for Crowd Control (IICCM), IEEE Access, 2025.",
        "[7] Li et al., CSRNet: Dilated Convolutional Neural Networks for Understanding the Highly Congested Scenes, CVPR, 2018.",
        "[8] Redmon/Ultralytics YOLO family — real-time object detection (YOLOv8 used in this work).",
        "[9] Wojke et al., Simple Online and Realtime Tracking with a Deep Association Metric (DeepSORT), ICIP, 2017.",
        "[10] Predicting and Optimizing Crowd Evacuations with XAI, Computer Animation and Virtual Worlds, 2025.",
        "[11] D-Shield: Digital Twin Stampede Hazard Identification, 2025.",
        "[12] Holt, D.H. Management principles and practices. Sydney: Prentice-Hall, 1997.",
        "[13] Endalamaw, Dense Crowd Activity Detection using YOLOv8 and DeepSORT, 2024.",
        "[14] STDCformer: Spatial–Temporal Causal De-Confounding Transformer for Crowd Flow, Information Fusion, 2025.",
        "[15] Smart Building Evacuation Multi-Camera + Explainable Re-ID, Engineering Applications of AI, 2025.",
        "[16] Heterogeneous Dual-Attentional Network for WiFi–Video Crowd Counting, IEEE TMC, 2024.",
        "[17] Advancing Urban Evacuation via Cloud Big Data & IoT, IEEE CONIT, 2024.",
        "[18] Dual-Metric Stampede Risk using YOLOv11 + Optical Flow Chaos Score, 2025.",
        "[19] FastAPI Documentation — https://fastapi.tiangolo.com/ [Accessed: Aug 2026].",
        "[20] Ultralytics YOLOv8 Documentation — https://docs.ultralytics.com/ [Accessed: Aug 2026].",
    ]
    for r in refs:
        add_para(doc, r, size=11, align="left", space_after=4)

    add_page_break(doc)
    add_para(doc, "APPENDIX", size=14, bold=True, align="center", space_after=12)
    add_subsection_heading(doc, "Appendix A — Source Code Repository Structure")
    add_body_block(
        doc,
        [
            "The CrowdPulse repository at c:\\MAJORPROJECT follows a monorepo layout with backend, frontend, "
            "edge, infra, docs, and scripts directories. The backend FastAPI application entry point is "
            "backend/app/main.py, which configures CORS, lifespan hooks (database init, seed, model warmup), "
            "and mounts the v1 API router plus WebSocket twin endpoint.",
        ],
    )
    for item in [
        "backend/app/api/v1/routes/ — auth, venues, videos, pipeline, twin, risk, decisions, simulation, analytics, reports",
        "backend/app/ai/perception/detector.py — YOLOv8n + HOG person detection",
        "backend/app/ai/perception/tracker.py — CentroidTracker with IoU matching",
        "backend/app/ai/perception/zone_assigner.py — Point-in-polygon zone assignment",
        "backend/app/ai/perception/analytics.py — Zone density, speed, opposing flow features",
        "backend/app/ai/risk/dcrs.py — Dynamic Crowd Risk Score engine",
        "backend/app/ai/xai/attributor.py — Explainable Risk Attribution",
        "backend/app/ai/decision/ml_recommender.py — Gradient Boosting action recommender",
        "backend/app/ai/decision/cdse.py — Cognitive Decision Support Engine + safety filter",
        "backend/app/ai/simulation/what_if.py — What-if scenario simulator",
        "backend/app/ai/reporting/incident_report.py — Incident report generator",
        "backend/app/infrastructure/persistence/seed.py — Aether Arena demo seed",
        "backend/app/infrastructure/persistence/twin_store.py — In-memory live twin cache",
        "frontend/src/components/digital-twin/DigitalTwinMap.tsx — Zone choropleth dashboard",
        "frontend/src/components/risk/DecisionQueue.tsx — Accept/Dismiss action queue",
        "frontend/src/services/api.ts — Typed API client with JWT injection",
        "docs/ — ARCHITECTURE.md, API.md, DCRS_ALGORITHM.md, DEMO_CHECKLIST.md, and day logs",
        "backend/tests/unit/test_core_ai.py — Unit tests for DCRS, ERA, CDSE, fusion",
        "backend/scripts/day23_verify.py — End-to-end pipeline verification script",
    ]:
        add_bullet(doc, item)

    add_subsection_heading(doc, "Appendix B — Demo Accounts and Sample Data")
    add_para(doc, "Table B.1 — Seeded control-room accounts", size=11, italic=True, align="center")
    acc_t = doc.add_table(rows=4, cols=3)
    acc_t.style = "Table Grid"
    fill_table(
        acc_t,
        [
            ["Username", "Password", "Role"],
            ["tsp.operator", "Operator@TS2026", "Operator"],
            ["tsp.admin", "Admin@TS2026", "Admin"],
            ["stadium.ops", "Stadium@TS2026", "Operator"],
        ],
    )
    add_caption(doc, "Table B.1. Demo accounts for viva demonstration.")

    add_subsection_heading(doc, "Appendix C — DCRS Algorithm Pseudocode")
    add_para(
        doc,
        "Algorithm 1: Evaluate DCRS for a zone\n"
        "Input: ZoneMetrics m, weights w, bias b\n"
        "Output: RiskScore with dcrs, band, explanation\n"
        "1. Compute feature vector φ from m (density_norm, speed_drop, opposing_flow, ...)\n"
        "2. Clip each φ_i to valid range\n"
        "3. logit ← b + Σ w_i · φ_i\n"
        "4. dcrs ← 100 · sigmoid(logit)\n"
        "5. band ← Green if dcrs < 40; Yellow if dcrs < 60; Orange if dcrs < 80; else Red\n"
        "6. explanation ← ERA.rank_contributions(φ, w)\n"
        "7. If dcrs ≥ 60 OR forecast_dcrs(t+10) ≥ 60 then raise alert\n"
        "8. Return RiskScore(dcrs, band, explanation)",
        size=11,
        align="left",
        space_after=12,
    )

    add_subsection_heading(doc, "Appendix D — Gradient Boosting Action Types")
    for item in [
        "open_exit — Open an additional exit to relieve exit pressure.",
        "close_exit — Close a non-critical exit to redirect flow (safety filter blocks last exit).",
        "deploy_guards — Deploy security personnel to a congested zone.",
        "redirect_zone — Redirect incoming crowd to an adjacent lower-risk zone.",
        "activate_pa — Activate public-address system with crowd guidance message.",
        "deploy_medical — Deploy medical team to zone with elevated risk.",
        "route_evacuation — Initiate controlled evacuation routing.",
        "hold_ingress — Hold ingress at gates to reduce incoming flow.",
    ]:
        add_bullet(doc, item)

    add_subsection_heading(doc, "Appendix E — List of Papers Published (if any)")
    add_para(
        doc,
        "No papers have been published based on this report at the time of Stage-I submission. "
        "Publication is planned upon completion of Stage-II evaluation and experimental results.",
        first_line_indent=0.3,
    )


def build_document() -> Path:
    diagrams = ensure_diagrams()
    doc = Document()
    setup_margins(doc.sections[0])

    build_cover_pages(doc)
    build_toc_and_lists(doc, diagrams)

    # New section for body chapters (Arabic page numbers from here)
    doc.add_section(WD_SECTION.NEW_PAGE)
    setup_margins(doc.sections[-1])
    add_footer_page_number(doc.sections[-1])

    build_chapter1(doc)
    build_chapter2(doc)
    build_chapter3(doc, diagrams)
    build_chapter4(doc, diagrams)
    build_references_and_appendix(doc)

    doc.save(OUT_PATH)
    OUT_DOWNLOADS.parent.mkdir(parents=True, exist_ok=True)
    import shutil

    shutil.copy2(OUT_PATH, OUT_DOWNLOADS)
    return OUT_PATH


if __name__ == "__main__":
    path = build_document()
    # Estimate pages
    from docx import Document as D

    d = D(path)
    words = sum(len(p.text.split()) for p in d.paragraphs)
    print(f"Generated: {path}")
    print(f"Also copied to: {OUT_DOWNLOADS}")
    print(f"Approx words: {words} (~{words // 250} pages at 250 w/page)")

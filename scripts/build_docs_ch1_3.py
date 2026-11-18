"""Generate CrowdPulse Chapter 1-3 documentation and IEEE-style research paper (DOCX)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT_DIR = Path(r"c:\MAJORPROJECT\docs")
USECASE_IMG = OUT_DIR / "assets" / "usecase_crowdpulse.png"
DOC_PATH = OUT_DIR / "CrowdPulse_Documentation_Chapters_1-3.docx"
PAPER_PATH = OUT_DIR / "CrowdPulse_Research_Paper_Ch1-3.docx"


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
    style=None,
    size=12,
    bold=False,
    italic=False,
    align="justify",
    space_after=8,
    space_before=0,
    first_line_indent=None,
):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if first_line_indent is not None:
        pf.first_line_indent = Inches(first_line_indent)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_heading_custom(doc, text, level=1):
    # Academic numbered headings as plain bold paragraphs (college report style)
    sizes = {1: 16, 2: 14, 3: 12}
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    set_run_font(run, size=sizes.get(level, 12), bold=True)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if level:
        p.paragraph_format.left_indent = Inches(0.5 * level)
    run = p.add_run(text)
    set_run_font(run, size=12)
    return p


def set_cell_shading(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
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


def build_documentation() -> Path:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(1)

    # Title page block
    add_para(
        doc,
        "CrowdPulse: An Intelligent Crowd Analytics and Decision Support Platform",
        size=18,
        bold=True,
        align="center",
        space_after=6,
    )
    add_para(
        doc,
        "Documentation — Chapters 1 to 3",
        size=14,
        bold=True,
        align="center",
        space_after=6,
    )
    add_para(
        doc,
        "Industrial Oriented Mini Project (IOMP)\nDepartment of Computer Science and Engineering\nCVR College of Engineering",
        size=12,
        align="center",
        space_after=6,
    )
    add_para(
        doc,
        "Submitted by: V. Akshitha (23B81A05K6)\nProject Supervisor: Mr. M. Hanimi Reddy, Sr. Assistant Professor",
        size=12,
        align="center",
        space_after=18,
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 1
    # ═══════════════════════════════════════════════════════════════════
    add_heading_custom(doc, "CHAPTER 1 — INTRODUCTION", level=1)

    add_heading_custom(doc, "1.1 Background and Motivation", level=2)
    add_para(
        doc,
        "Large public gatherings — religious festivals, stadium match days, transit hubs, and civic events — "
        "continue to produce preventable crush and congestion incidents despite the near-universal deployment "
        "of closed-circuit television (CCTV). Historical disasters at pilgrimage sites, sports venues, and "
        "concert grounds have shown that dense crowds can transition from orderly flow to dangerous "
        "compression within minutes. In many of these cases, camera feeds were available, but the operational "
        "gap was not a lack of video; it was the absence of timely, explainable decision support that converts "
        "pixels into prioritized actions for a control room.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "Traditional surveillance practice relies on human operators scanning multiple video walls. Operators "
        "are expected to notice rising density, opposing pedestrian streams, exit queuing, and anomalous motion "
        "while simultaneously coordinating radio traffic. Under cognitive load, threshold-based “high density” "
        "alarms often fire late — after a zone already looks congested on screen. Counting-only computer-vision "
        "tools improve awareness but still leave authorities without a closed loop from perception to risk "
        "explanation to recommended intervention. This motivation frames CrowdPulse: a venue-oriented "
        "platform that treats crowd safety as a decision-support problem, not merely a detection problem.",
        first_line_indent=0.3,
    )
    add_para(
        doc,
        "CrowdPulse is therefore motivated by three practical needs observed in control-room settings. First, "
        "zone-level situational awareness must update continuously from CCTV or recorded footage. Second, risk "
        "must be expressed as a multi-factor score that includes density together with flow-speed decay, "
        "opposing-flow conflict, and exit pressure — signals that often precede visible crush. Third, every "
        "alert should be explainable and paired with ranked actions so that non-technical officers can accept, "
        "dismiss, or escalate decisions with an auditable trail. The Level A implementation targets a single-venue "
        "pilot suitable for academic demonstration and local stadium / public-venue evaluation, while remaining "
        "architecturally open to multi-camera scale-out.",
        first_line_indent=0.3,
    )

    add_heading_custom(doc, "1.2 Problem Statement", level=2)
    add_para(
        doc,
        "Existing crowd-surveillance systems do not provide an integrated mechanism that converts CCTV "
        "observations into a multi-factor Dynamic Crowd Risk Score, attaches feature-level explanations, and "
        "ranks operational interventions for a control-room operator. Most deployed and academic solutions "
        "remain reactive: they raise alerts only after a density (or simple chaos) threshold is crossed, and "
        "they stop at visualization without an Accept/Dismiss decision loop, what-if simulation, historical "
        "logging of zone risk, or role-separated authentication for Admin ingest versus Operator monitoring. "
        "Consequently, authorities still lack a production-oriented closed loop from detection and tracking "
        "through predictive flow-speed aware early warning to explainable, recommended action — which is the "
        "specific unsolved problem addressed by CrowdPulse.",
        first_line_indent=0.3,
    )

    add_heading_custom(doc, "1.3 Objectives", level=2)
    add_para(
        doc,
        "The primary objectives of this project are:",
        space_after=4,
    )
    objectives = [
        "Real-time density detection: Detect and track people in CCTV / sample video using YOLOv8 (with OpenCV HOG fallback), assign detections to venue zones, and compute zone occupancy and density metrics.",
        "Early-warning prediction: Combine density with predictive flow-speed and related signals (speed drop, opposing flow, exit pressure) inside a Dynamic Crowd Risk Score (DCRS) to raise graded Green / Yellow / Orange / Red warnings before conditions become unrecoverable.",
        "Centralized dashboard: Provide a secured Next.js digital-twin ops console where officers view live zone risk coloring, explanations (ERA), Gradient Boosting action recommendations, and what-if outcomes in one place.",
        "Historical logging: Persist venues, zones, alerts, decisions, processed videos, and incident reports in a schema-backed database (SQLite, Postgres-ready) to support after-action review and accountability.",
        "Explainable decision support: Attach Explainable Risk Attribution (ERA) to alerts and rank interventions with Gradient Boosting plus a deterministic safety filter (for example, never close the last exit).",
        "Role-based control-room access: Enforce JWT authentication so Operators monitor and decide, while Admins additionally run CCTV ingest / pipeline processing.",
    ]
    for o in objectives:
        add_bullet(doc, o)

    add_heading_custom(doc, "1.4 Scope of the Project", level=2)
    add_heading_custom(doc, "1.4.1 In Scope (Level A)", level=3)
    for item in [
        "Single-venue pilot topology with seeded zones, cameras, and exits (demo venue).",
        "File-based / sample CCTV ingest and pipeline processing (Admin).",
        "Person detection (YOLOv8n or HOG), centroid-IoU tracking, and zone analytics.",
        "DCRS risk bands, ERA explanations, and Gradient Boosting recommendations.",
        "Digital twin dashboard, Accept/Dismiss decision queue, what-if simulation, and incident report generation.",
        "JWT Operator / Admin authentication and structured API validation.",
    ]:
        add_bullet(doc, item)

    add_heading_custom(doc, "1.4.2 Explicitly Out of Scope (Level A)", level=3)
    for item in [
        "City-scale multi-camera geometric fusion and anti-double-counting across overlapping feeds.",
        "Mandatory GPU inference; the system is designed to run on a standard laptop CPU (YOLO optional; HOG fallback).",
        "Live RTSP mosaic viewer as a completed product feature (cameras exist as seeded metadata).",
        "Full TimescaleDB hypertables, Redis stream edge fleet, and Kubernetes production HA as runtime claims.",
        "Training a custom person detector on private police CCTV corpora (uses public COCO person weights / HOG).",
        "Legal command-and-control replacement for human authority decisions — CrowdPulse advises; officers decide.",
    ]:
        add_bullet(doc, item)

    add_heading_custom(doc, "1.5 Organization of the Report", level=2)
    add_para(
        doc,
        "The remainder of this report is organized as follows. Chapter 2 presents the literature review, "
        "covering deployed crowd-monitoring systems such as large pilgrimage command centers, academic "
        "detection and density-map techniques (YOLO with tracking versus CSRNet-style density estimation), "
        "and the research gap that motivates predictive flow-speed aware early warning and closed-loop "
        "decision support. Chapter 3 documents requirement analysis, including functional and non-functional "
        "requirements, hardware and software requirements, and a use-case view of Officer and Admin "
        "interactions with the system. Subsequent chapters (beyond this submission package) will describe "
        "system design, implementation, testing, results, and conclusions.",
        first_line_indent=0.3,
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 2
    # ═══════════════════════════════════════════════════════════════════
    add_heading_custom(doc, "CHAPTER 2 — LITERATURE REVIEW", level=1)
    add_para(
        doc,
        "This chapter surveys deployed operational systems and academic computer-vision techniques for crowd "
        "monitoring. The goal is twofold: demonstrate awareness of what already exists, and justify why "
        "CrowdPulse’s combination of multi-factor DCRS, predictive flow-speed signals, explainability, and "
        "operator decision support closes a gap that density-threshold tools leave open.",
        first_line_indent=0.3,
    )

    add_heading_custom(doc, "2.1 Deployed Systems", level=2)
    add_heading_custom(doc, "2.1.1 Kumbh Mela / Large Pilgrimage AI Command Centers", level=3)
    add_para(
        doc,
        "Large Indian pilgrimage gatherings such as the Kumbh Mela have increasingly adopted AI-assisted "
        "command centers that fuse CCTV, drone feeds, and GIS maps to estimate crowd accumulation at "
        "ghats, corridors, and pontine choke points. Reported capabilities typically include density heatmaps, "
        "camera-wall situational awareness, and threshold-based alerts for police and municipal authorities. "
        "These deployments prove that computer vision can operate at festival scale and that centralized "
        "dashboards improve coordination. However, publicly described stacks still emphasize monitoring and "
        "alerting more than closed-loop execution: they rarely publish explainable multi-factor risk scores, "
        "ranked gate/PA/guard recommendations with Accept/Dismiss audit trails, or interactive what-if "
        "simulation on a live venue twin. The execution/response gap — moving from “zone looks dense” to "
        "“which safe action should the officer take next, and why” — remains an operational weakness.",
        first_line_indent=0.3,
    )

    add_heading_custom(doc, "2.1.2 Hajj Crowd Monitoring Frameworks", level=3)
    add_para(
        doc,
        "Hajj-oriented research and operational frameworks integrate computer vision, IoT sensing, and "
        "evacuation planning for extremely dense ritual routes. Recent integrated intelligent crowd-control "
        "frameworks discuss tracking, behavior analysis, and planning support for authorities. These systems "
        "are valuable references for zone ontology and evacuation thinking. Their limitation, from a "
        "productized decision-support perspective, is that many remain broad architectural proposals or "
        "sensing-heavy pipelines without a unified Explainable Risk Attribution layer, Gradient "
        "Boosting–style action ranking, and a lightweight ops console that a college-deployable venue pilot "
        "can reproduce. CrowdPulse deliberately scopes a smaller venue pilot while borrowing the same "
        "control-room mindset: zones, risk bands, and authority-facing recommendations.",
        first_line_indent=0.3,
    )

    add_heading_custom(doc, "2.2 Academic Techniques: Detection Counting vs Density Maps", level=2)
    add_para(
        doc,
        "Academic crowd counting broadly splits into detection-based and density-map-based families. "
        "Detection-based pipelines use object detectors (for example YOLO variants) optionally coupled with "
        "multi-object trackers such as DeepSORT or ByteTrack. They work well at sparse-to-moderate density, "
        "provide bounding boxes useful for tracking speed and direction, and integrate cleanly with zone "
        "polygons. Their accuracy degrades under extreme occlusion when individual bodies are no longer "
        "separable. Density-map approaches such as CSRNet regress a continuous density field and integrate "
        "it to obtain a count; they are stronger in extreme density but weaker at yielding per-person "
        "trajectories needed for flow-speed and opposing-flow features.",
        first_line_indent=0.3,
    )

    # Comparison table
    add_para(doc, "Table 2.1 — Comparison of representative academic techniques", size=11, italic=True, align="center")
    table = doc.add_table(rows=4, cols=4)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    fill_table(
        table,
        [
            ["Approach", "Strengths", "Weaknesses", "Relevance to CrowdPulse"],
            [
                "YOLO + tracking (e.g., DeepSORT / centroid-IoU)",
                "Person IDs, speed, direction; moderate-density real-time on CPU/GPU",
                "Fails under extreme occlusion; count underestimation possible",
                "Primary Level A path: enables flow-speed & opposing-flow features",
            ],
            [
                "CSRNet / density-map CNNs",
                "Better extreme-density counting via density regression",
                "Weak per-person trajectories; harder motion semantics",
                "Useful reference; not primary because DCRS needs motion features",
            ],
            [
                "Short-horizon LSTM density forecast",
                "Adds limited prediction beyond instantaneous count",
                "Often density-only; rarely pairs with action recommendations",
                "Motivates predictive early warning beyond reactive thresholds",
            ],
        ],
    )
    add_caption(doc, "Table 2.1. Detection-based vs density-map techniques and project relevance.")

    add_heading_custom(doc, "2.3 Recent IEEE-Oriented Findings (2023–2025)", level=2)
    add_para(
        doc,
        "Recent IEEE and related publications advance hybrid YOLO counting with speed/direction estimation, "
        "IoT+YOLO live density pipelines, encoder–decoder LSTM multi-camera density forecasting, and "
        "conceptual stampede-prevention stacks that couple YOLOv8 with short LSTM horizons. Parallel work "
        "explores digital-twin hazard identification and offline XAI for evacuation optimization. Across this "
        "corpus, perception quality has improved substantially, yet comparatively few systems ship an "
        "operator-facing loop that (a) scores multi-factor risk including flow-speed decay, (b) explains the "
        "score, (c) recommends actions, and (d) logs decisions for audit.",
        first_line_indent=0.3,
    )

    add_para(doc, "Table 2.2 — Selected papers and gaps (condensed)", size=11, italic=True, align="center")
    table2 = doc.add_table(rows=6, cols=4)
    table2.style = "Table Grid"
    fill_table(
        table2,
        [
            ["S.No", "Work / Theme", "Implication", "Gap vs CrowdPulse goal"],
            [
                "1",
                "Hybrid YOLOv4 crowd monitoring (IEEE Access, 2023)",
                "Count + speed + direction feasible",
                "No multi-factor DCRS / action cards",
            ],
            [
                "2",
                "IoT + OpenCV + YOLO counting (2024)",
                "Practical live density pipelines",
                "Detection-centric; weak XAI & what-if",
            ],
            [
                "3",
                "Encoder–Decoder LSTM density forecast (2024)",
                "Prediction beyond instantaneous density",
                "Density-only; no decision engine / twin ops",
            ],
            [
                "4",
                "YOLOv8 + LSTM stampede alerts (2025)",
                "Short-horizon graded alerts",
                "Limited horizon; no Accept/Dismiss DSS",
            ],
            [
                "5",
                "XAI evacuation optimization (2025)",
                "Explanations help planning",
                "Mostly offline; not live CCTV twin",
            ],
        ],
    )
    add_caption(doc, "Table 2.2. Literature snapshot motivating the project gap.")

    add_heading_custom(doc, "2.4 Gap Identified", level=2)
    add_para(
        doc,
        "The central literature gap is reactivity without decision closure. Most existing work alerts only "
        "once density (or a dual density–chaos metric) crosses a threshold. That is necessary but insufficient: "
        "crush risk often builds through slowing flow, bidirectional conflict, and exit pressure before raw "
        "headcount looks catastrophic. CrowdPulse addresses this gap by elevating a predictive flow-speed "
        "signal — speed drop relative to a baseline, together with opposing-flow and exit-pressure features — "
        "inside DCRS, attaching ERA explanations, and ranking interventions with Gradient Boosting under "
        "safety constraints. In short, the literature justifies detection and density estimation; this project "
        "justifies why those alone are not enough for authority decision support.",
        first_line_indent=0.3,
    )

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 3
    # ═══════════════════════════════════════════════════════════════════
    add_heading_custom(doc, "CHAPTER 3 — REQUIREMENT ANALYSIS", level=1)
    add_para(
        doc,
        "Requirement analysis identifies the functional and non-functional capabilities required to build "
        "CrowdPulse as a control-room oriented venue pilot. Requirements are written so that non-technical "
        "officers receive a clear dashboard, while the engineering stack remains modular and replaceable.",
        first_line_indent=0.3,
    )

    add_heading_custom(doc, "3.1 Functional Requirements", level=2)
    add_para(doc, "Table 3.1 — Functional requirements", size=11, italic=True, align="center")
    fr = doc.add_table(rows=9, cols=3)
    fr.style = "Table Grid"
    fill_table(
        fr,
        [
            ["ID", "Requirement", "Description"],
            [
                "FR-1",
                "Authentication",
                "Users log in with JWT-backed credentials; roles distinguish Operator and Admin.",
            ],
            [
                "FR-2",
                "Video input capture",
                "Admin uploads CCTV clips or selects sample sparse/medium/dense footage for processing.",
            ],
            [
                "FR-3",
                "Person detection & tracking",
                "System detects persons (YOLOv8n / HOG) and maintains tracks for zone analytics.",
            ],
            [
                "FR-4",
                "Density / risk calculation",
                "Zone density and multi-factor DCRS (including flow-speed signals) produce G/Y/O/R bands.",
            ],
            [
                "FR-5",
                "Real-time dashboard update",
                "Digital twin map and panels refresh with zone metrics, alerts, and recommendations.",
            ],
            [
                "FR-6",
                "Alert generation",
                "Alerts are raised from DCRS thresholds and include ERA explanations.",
            ],
            [
                "FR-7",
                "Historical logging",
                "Venues, zones, alerts, decisions, videos, and reports are persisted for audit/review.",
            ],
            [
                "FR-8",
                "Decision & simulation",
                "Operators Accept/Dismiss recommended actions; what-if scenarios re-score the twin.",
            ],
        ],
    )
    add_caption(doc, "Table 3.1. Functional requirements of CrowdPulse.")

    add_heading_custom(doc, "3.2 Non-Functional Requirements", level=2)
    add_para(doc, "Table 3.2 — Non-functional requirements", size=11, italic=True, align="center")
    nfr = doc.add_table(rows=8, cols=3)
    nfr.style = "Table Grid"
    fill_table(
        nfr,
        [
            ["ID", "Requirement", "Description"],
            [
                "NFR-1",
                "Real-time performance",
                "Target interactive pipeline latency suitable for demo/ops refresh (order of seconds per sampled-frame batch on laptop CPU; sub-second API reads for twin snapshot).",
            ],
            [
                "NFR-2",
                "Scalability (multi-zone)",
                "Architecture supports multiple zones within a venue; schema ready for Postgres scale-up.",
            ],
            [
                "NFR-3",
                "Usability",
                "Dashboard clarity for non-technical officers: risk colors, short explanations, action cards.",
            ],
            [
                "NFR-4",
                "Security",
                "JWT auth, role checks, secrets via environment variables, validated API inputs (Pydantic).",
            ],
            [
                "NFR-5",
                "Reliability",
                "Graceful handling of empty video, failed detection, and model-load fallback to HOG.",
            ],
            [
                "NFR-6",
                "Maintainability",
                "Clean Architecture modules (perception, risk, decision, simulation, reporting) are replaceable.",
            ],
            [
                "NFR-7",
                "Compatibility",
                "Web ops console usable on modern desktop browsers; backend on Windows/Linux Python 3.x.",
            ],
        ],
    )
    add_caption(doc, "Table 3.2. Non-functional requirements.")

    add_heading_custom(doc, "3.3 Hardware Requirements", level=2)
    add_para(
        doc,
        "CrowdPulse is intentionally feasible on a standard laptop without a dedicated GPU. GPU acceleration "
        "can speed YOLO inference when available, but it is not required for the Level A pilot because OpenCV "
        "HOG provides a CPU fallback and frame sampling keeps compute bounded.",
        first_line_indent=0.3,
    )
    for item in [
        "Processor: Intel Core i5 / AMD Ryzen 5 or higher (i3 minimum for light demo).",
        "RAM: Minimum 8 GB (16 GB recommended when enabling YOLOv8n).",
        "Storage: At least 20 GB free for Python packages, models, sample videos, and database files.",
        "Display: 1366×768 or higher for the ops dashboard.",
        "Network: Localhost demo needs no internet after dependency install; optional for package download.",
        "GPU: Not required (explicit feasibility constraint for college / venue pilot laptops).",
    ]:
        add_bullet(doc, item)

    add_heading_custom(doc, "3.4 Software Requirements", level=2)
    for item in [
        "Python 3.10+ (backend runtime).",
        "OpenCV (opencv-python-headless) for video I/O and HOG fallback detection.",
        "Ultralytics YOLOv8n (optional) for person detection using public COCO person weights.",
        "NumPy, scikit-learn (Gradient Boosting recommender).",
        "FastAPI, Uvicorn, Pydantic, SQLAlchemy, aiosqlite / SQLite (Postgres-ready).",
        "PyJWT + bcrypt for authentication.",
        "Frontend: Node.js LTS toolchain with Next.js, React, TypeScript, Tailwind CSS, Recharts.",
        "Development tools: VS Code, Git & GitHub, Postman or OpenAPI /docs.",
        "Optional: Docker for packaged services; Ollama for enhanced incident narrative (not mandatory).",
    ]:
        add_bullet(doc, item)
    add_para(
        doc,
        "Note: Unlike generic Firebase-centric tutorials, CrowdPulse persists operational state in a "
        "relational schema (SQLite for Level A) behind a typed FastAPI, which better matches production "
        "control-room data modeling for venues, zones, alerts, and decisions.",
        italic=True,
        size=11,
    )

    add_heading_custom(doc, "3.5 Use Case Diagram", level=2)
    add_para(
        doc,
        "Figure 3.1 illustrates the primary actors and use cases. The Officer (Operator) authenticates, "
        "views the digital twin dashboard, receives risk alerts, accepts or dismisses recommended actions, "
        "and may generate incident reports. The Admin shares monitoring use cases and additionally uploads "
        "or processes footage through the pipeline.",
        first_line_indent=0.3,
    )
    if USECASE_IMG.exists():
        doc.add_picture(str(USECASE_IMG), width=Inches(5.8))
        last = doc.paragraphs[-1]
        last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_caption(
        doc,
        "Figure 3.1. Use case diagram (actors: Officer/Operator, Admin; system: CrowdPulse).",
    )

    add_heading_custom(doc, "3.6 Use Case Summaries", level=2)
    for title, body in [
        (
            "UC-1 Login",
            "Actor authenticates with username/password; system issues JWT and enforces role permissions.",
        ),
        (
            "UC-2 View Dashboard",
            "Actor opens the digital twin to inspect zone colors, metrics, alerts, and decision queue.",
        ),
        (
            "UC-3 Upload / Process Footage",
            "Admin selects sample dense footage or uploads a clip; system runs detect→track→DCRS→recommend.",
        ),
        (
            "UC-4 Receive Alert",
            "When DCRS crosses configured bands/thresholds, the dashboard presents an alert with ERA reasons.",
        ),
        (
            "UC-5 Accept / Dismiss Action",
            "Operator records a decision on a Gradient Boosting recommendation for audit logging.",
        ),
        (
            "UC-6 Generate Incident Report",
            "Actor requests an after-action summary combining timeline, risk, and decisions.",
        ),
    ]:
        add_para(doc, title, bold=True, align="left", space_after=2)
        add_para(doc, body, first_line_indent=0.2, space_after=8)

    add_heading_custom(doc, "3.7 Summary", level=2)
    add_para(
        doc,
        "Chapter 3 established the contractual requirements for CrowdPulse: authenticated video-to-decision "
        "workflows, multi-factor risk with early-warning signals, a usable ops dashboard, and historical "
        "logging — all runnable on a CPU-only laptop for a venue pilot. These requirements directly drive "
        "the system design and methodology described in later chapters and in the accompanying research paper.",
        first_line_indent=0.3,
    )

    doc.save(DOC_PATH)
    return DOC_PATH


def build_research_paper() -> Path:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    # IEEE-ish title block
    add_para(
        doc,
        "CrowdPulse: An Intelligent Crowd Analytics and Decision Support Platform "
        "for Explainable Early Warning in Public Venues",
        size=16,
        bold=True,
        align="center",
        space_after=6,
    )
    add_para(
        doc,
        "V. Akshitha\nDepartment of Computer Science and Engineering\n"
        "CVR College of Engineering\nHyderabad, India\n23B81A05K6",
        size=11,
        align="center",
        space_after=4,
    )
    add_para(
        doc,
        "Supervisor: Mr. M. Hanimi Reddy, Sr. Assistant Professor, CSE",
        size=11,
        italic=True,
        align="center",
        space_after=12,
    )

    # Abstract
    add_para(doc, "Abstract", size=12, bold=True, align="left", space_after=4)
    add_para(
        doc,
        "Crush and congestion incidents at stadiums and public gatherings remain preventable when CCTV "
        "is paired with timely decision support rather than counting alone. This paper presents CrowdPulse, "
        "an intelligent crowd analytics and decision support platform that ingests CCTV or sample video, "
        "detects and tracks persons using YOLOv8 (with OpenCV HOG fallback), maps observations to venue "
        "zones, and computes a Dynamic Crowd Risk Score (DCRS). Unlike reactive density-threshold systems, "
        "DCRS incorporates predictive flow-speed cues — including speed drop and opposing flow — together "
        "with exit pressure and related factors. Each alert is accompanied by Explainable Risk Attribution "
        "(ERA). A Gradient Boosting recommender ranks control-room actions under a deterministic safety "
        "filter. Operators interact through a JWT-secured Next.js digital-twin dashboard supporting "
        "Accept/Dismiss decisions, what-if simulation, and incident reporting, with historical logging in a "
        "schema-backed store. This submission covers problem motivation, literature gap, requirements-driven "
        "design intent, and the proposed methodology up to the analytical pipeline; empirical results are "
        "reserved for a subsequent section of the full report.",
        first_line_indent=0.0,
        size=11,
    )
    add_para(
        doc,
        "Keywords — crowd risk scoring; YOLO; digital twin; explainable AI; Gradient Boosting; "
        "decision support; early warning; smart surveillance",
        size=11,
        italic=True,
        space_after=12,
    )

    # I. Introduction
    add_heading_custom(doc, "I. INTRODUCTION", level=1)
    add_para(
        doc,
        "Public-venue safety operations increasingly depend on CCTV, yet many control rooms still lack a "
        "closed loop from perception to explainable action. Counting dashboards and simple density alarms "
        "improve awareness but often warn only after a zone already appears congested. Historical crush "
        "events demonstrate that dangerous compression can emerge quickly when flow slows, opposing streams "
        "collide, or exits queue — conditions that are only partially captured by headcount thresholds.",
        first_line_indent=0.25,
        size=11,
    )
    add_para(
        doc,
        "CrowdPulse is designed as a production-oriented venue pilot that treats crowd analytics as decision "
        "support. The platform’s contributions in this work package are: (1) a multi-factor DCRS with "
        "flow-speed aware early-warning signals; (2) ERA explanations attached to alerts; (3) Gradient "
        "Boosting action ranking with safety constraints; and (4) a centralized digital-twin console with "
        "authentication and historical logging. The remainder of this paper reviews related systems and "
        "techniques, summarizes requirements that shaped the design, and presents the proposed methodology.",
        first_line_indent=0.25,
        size=11,
    )

    # II. Literature Survey
    add_heading_custom(doc, "II. LITERATURE SURVEY", level=1)
    add_para(
        doc,
        "Deployed pilgrimage and mega-event command centers (for example, AI-assisted monitoring associated "
        "with large gatherings such as the Kumbh Mela, and Hajj-oriented integrated crowd-control frameworks) "
        "demonstrate that camera-centric density awareness can be operationalized at scale. Their recurring "
        "limitation is an execution/response gap: alerts and heatmaps are common, while explainable "
        "multi-factor scoring and audited action recommendations are not consistently productized for smaller "
        "venue pilots.",
        first_line_indent=0.25,
        size=11,
    )
    add_para(
        doc,
        "Academically, detection-based counting using YOLO coupled with trackers such as DeepSORT provides "
        "person-level trajectories useful for velocity and direction at moderate density, but degrades under "
        "extreme occlusion. Density-map networks such as CSRNet regress crowd density fields and often "
        "outperform detectors in extreme density, yet they supply weaker per-person motion features. Recent "
        "IEEE studies (2023–2025) advance hybrid YOLO monitoring, IoT+YOLO pipelines, LSTM density "
        "forecasting, and short-horizon stampede alert concepts. Across these lines of work, systems remain "
        "predominantly reactive or perception-centric. The gap motivating CrowdPulse is the missing bridge "
        "from multi-factor, flow-speed aware risk to explainable, recommended control-room actions on a live "
        "zone twin.",
        first_line_indent=0.25,
        size=11,
    )

    add_para(doc, "TABLE I. TECHNIQUE TRADEOFFS (SUMMARY)", size=10, bold=True, align="center", space_after=4)
    t = doc.add_table(rows=3, cols=3)
    t.style = "Table Grid"
    fill_table(
        t,
        [
            ["Family", "Best regime", "Limitation for decision support"],
            ["YOLO + tracking", "Sparse–moderate density, motion features", "Occlusion hurts counts"],
            ["CSRNet-like density maps", "Extreme density counting", "Weak flow-speed trajectories"],
        ],
    )
    add_caption(doc, "")

    # III. Requirement-driven problem framing (brief, ties to Ch3)
    add_heading_custom(doc, "III. REQUIREMENTS DRIVING THE DESIGN", level=1)
    add_para(
        doc,
        "Functional requirements include video ingest, person detection, density/risk calculation, real-time "
        "dashboard update, alert generation, historical logging, and authentication. Non-functional drivers "
        "emphasize interactive latency on commodity hardware, multi-zone scalability within a venue, and "
        "dashboard usability for non-technical officers. Hardware feasibility is explicit: no GPU is required "
        "for Level A operation. Software centers on Python 3.x, OpenCV, optional YOLOv8, FastAPI, SQLite "
        "(Postgres-ready), and a Node.js-based Next.js frontend — chosen for typed APIs and schema-backed "
        "ops data rather than a purely serverless demo stack.",
        first_line_indent=0.25,
        size=11,
    )

    # IV. Proposed Methodology
    add_heading_custom(doc, "IV. PROPOSED METHODOLOGY", level=1)
    add_para(
        doc,
        "CrowdPulse follows Clean Architecture: a Next.js presentation layer calls a FastAPI application "
        "layer, which orchestrates AI modules (perception, risk, explainability, decision, simulation, "
        "reporting) and infrastructure adapters (database, twin store, video files). The end-to-end methodology "
        "is summarized below.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "A. Video Ingest and Perception", level=2)
    add_para(
        doc,
        "An Admin authenticates and selects sample footage or uploads a clip. The pipeline samples frames "
        "with a configurable stride. Persons are detected using Ultralytics YOLOv8n when weights are "
        "available; otherwise OpenCV HOG people detection is used. A centroid-IoU tracker associates "
        "detections across frames to support speed and flow estimates.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "B. Zone Analytics", level=2)
    add_para(
        doc,
        "Tracked persons are assigned to polygonal venue zones. Per-zone features include normalized density, "
        "mean speed, speed drop relative to baseline, opposing-flow conflict, and exit-pressure proxies. These "
        "features deliberately go beyond headcount so that early-warning behavior can emerge before a pure "
        "density threshold trips.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "C. Dynamic Crowd Risk Score (DCRS) and ERA", level=2)
    add_para(
        doc,
        "DCRS maps clipped multi-factor features through a weighted logistic / sigmoid transform to a score "
        "in [0, 100], then to Green / Yellow / Orange / Red bands. Alerts attach Explainable Risk Attribution "
        "listing top positive feature contributions and a short narrative suitable for officers. This design "
        "addresses opaque threshold alarms common in prior reactive systems.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "D. Gradient Boosting Decision Support", level=2)
    add_para(
        doc,
        "A scikit-learn Gradient Boosting classifier, trained on synthetic multi-factor crowd-risk scenarios "
        "with rule-derived multi-label actions, ranks candidate interventions (for example, gate control, "
        "guard redeployment, public-address messaging, zone redirection). A deterministic safety layer filters "
        "unsafe recommendations such as closing the last remaining exit. Operators Accept or Dismiss actions, "
        "producing historical decision logs.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "E. Digital Twin, What-If, and Reporting", level=2)
    add_para(
        doc,
        "The twin store exposes zone metrics and alerts to the dashboard for near-real-time visualization. "
        "What-if simulation perturbs twin state (exit closure, weather, VIP ingress) and re-scores risk. "
        "Incident reporting assembles timeline-aware summaries for after-action review. Persistence uses "
        "SQLAlchemy models for venues, zones, cameras, alerts, decisions, videos, and reports.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "F. Methodological Pipeline (Logical Flow)", level=2)
    for step in [
        "CCTV / sample video → frame sampling",
        "Detect (YOLO / HOG) → Track (centroid-IoU)",
        "Zone assignment → density + flow-speed feature extraction",
        "DCRS scoring → ERA explanation → alert if band/threshold exceeded",
        "Gradient Boosting recommendations → safety filter",
        "Digital twin dashboard update → Accept/Dismiss → optional what-if → incident report + DB log",
    ]:
        add_bullet(doc, step)

    add_para(
        doc,
        "This methodology is intentionally deployable on a standard CPU laptop for academic and venue-pilot "
        "demonstration, while remaining compatible with future Level B extensions such as multi-camera fusion "
        "and stronger forecasting backbones.",
        first_line_indent=0.25,
        size=11,
    )

    # Stop before Results per user request
    add_heading_custom(doc, "V. CONCLUSION OF THIS SUBMISSION PACKAGE", level=1)
    add_para(
        doc,
        "This paper section package introduced CrowdPulse, surveyed deployed and academic crowd-monitoring "
        "approaches, identified the reactive-threshold gap, and detailed a proposed methodology that adds "
        "flow-speed aware early warning, explainability, and Gradient Boosting decision support on a "
        "centralized digital twin. Experimental results, quantitative benchmarks, and full system evaluation "
        "will be reported in the subsequent chapters of the major-project documentation.",
        first_line_indent=0.25,
        size=11,
    )

    add_heading_custom(doc, "REFERENCES (SELECTED)", level=1)
    refs = [
        "[1] Realtime Crowd Monitoring—Estimating Count, Speed and Direction Using Hybridized YOLOv4, IEEE Access, 2023.",
        "[2] Integrated Crowd Counting Using IoT, OpenCV and YOLO, IEEE IC-CGU, 2024.",
        "[3] Crowd Density Forecasting with Distributed Cameras using Encoder–Decoder LSTM, IEEE I2CACIS, 2024.",
        "[4] A Novel AI-Based Predictive Crowd Monitoring and Stampede Prevention, IEEE GIEST, 2025.",
        "[5] Toward an Integrated Intelligent Framework for Crowd Control (IICCM), IEEE Access, 2025.",
        "[6] Li et al., CSRNet: Dilated Convolutional Neural Networks for Understanding the Highly Congested Scenes, CVPR, 2018.",
        "[7] Redmon/Ultralytics YOLO family — real-time object detection (YOLOv8 used in this work).",
        "[8] Wojke et al., Simple Online and Realtime Tracking with a Deep Association Metric (DeepSORT), ICIP, 2017.",
        "[9] Predicting and Optimizing Crowd Evacuations with XAI, Computer Animation and Virtual Worlds, 2025.",
        "[10] D-Shield: Digital Twin Stampede Hazard Identification, 2025.",
    ]
    for r in refs:
        add_para(doc, r, size=10, align="left", space_after=3)

    doc.save(PAPER_PATH)
    return PAPER_PATH


if __name__ == "__main__":
    d = build_documentation()
    p = build_research_paper()
    print("DOC:", d)
    print("PAPER:", p)

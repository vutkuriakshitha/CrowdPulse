"""Build CrowdPulse IOMP slides 1–10 from the sample PPTX template."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

SAMPLE = Path(
    r"c:\Users\akshi\OneDrive\Desktop\ASHU\ALL\PROJECTS\3-2 PROJECT FULL"
    r"\IOMP 23B81A05K6  FINAL.pptx"
)
OUT = Path(r"c:\MAJORPROJECT\docs\CrowdPulse_IOMP_Slides_1-10.pptx")
OUT_DESKTOP = Path(
    r"c:\Users\akshi\OneDrive\Desktop\ASHU\ALL\PROJECTS\3-2 PROJECT FULL"
    r"\CrowdPulse_IOMP_Slides_1-10.pptx"
)


def set_run_text(paragraph, text: str) -> None:
    """Replace paragraph text while keeping the first run's formatting."""
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def set_shape_paragraphs(shape, lines: list[str], clear_extra: bool = True) -> None:
    """Map lines onto existing paragraphs; optionally blank unused ones."""
    tf = shape.text_frame
    paras = list(tf.paragraphs)
    for i, line in enumerate(lines):
        if i < len(paras):
            set_run_text(paras[i], line)
        else:
            p = tf.add_paragraph()
            p.text = line
            if paras:
                # Copy basic level from last original para when possible
                p.level = paras[-1].level
    if clear_extra:
        for j in range(len(lines), len(paras)):
            set_run_text(paras[j], "")


def find_shape(slide, *names: str):
    for sh in slide.shapes:
        if sh.name in names:
            return sh
    return None


def find_content_shape(slide):
    """Largest text-bearing non-title, non-slide-number shape."""
    best = None
    best_area = 0
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        titleish = sh.name.lower().startswith("title") or "slide number" in sh.name.lower()
        if titleish:
            continue
        area = (sh.width or 0) * (sh.height or 0)
        if area > best_area:
            best_area = area
            best = sh
    return best


def set_title(slide, title: str) -> None:
    for sh in slide.shapes:
        if sh.name.lower().startswith("title") and sh.has_text_frame:
            set_shape_paragraphs(sh, [title])
            return


def delete_slides_after(prs: Presentation, keep: int) -> None:
    """Remove slides with index >= keep (0-based)."""
    sldIdLst = prs.slides._sldIdLst
    # Collect rIds to drop
    to_drop = []
    for idx, sldId in enumerate(list(sldIdLst)):
        if idx >= keep:
            rId = sldId.get(qn("r:id"))
            to_drop.append((sldId, rId))
    for sldId, rId in to_drop:
        sldIdLst.remove(sldId)
        if rId and rId in prs.part.rels:
            prs.part.drop_rel(rId)


def fill_table(table, rows: list[list[str]]) -> None:
    for r_i, row_data in enumerate(rows):
        if r_i >= len(table.rows):
            break
        for c_i, cell_text in enumerate(row_data):
            if c_i >= len(table.columns):
                break
            cell = table.cell(r_i, c_i)
            # Keep first paragraph formatting
            paras = list(cell.text_frame.paragraphs)
            if paras:
                set_run_text(paras[0], cell_text)
                for p in paras[1:]:
                    set_run_text(p, "")
            else:
                cell.text = cell_text


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SAMPLE, OUT)
    prs = Presentation(str(OUT))
    slides = list(prs.slides)

    # ── Slide 1: Title ──────────────────────────────────────────────
    s = slides[0]
    title = find_shape(s, "Title 1")
    if title:
        # Soft line break (vertical tab) matches sample title style
        set_shape_paragraphs(
            title,
            [
                "CrowdPulse - Intelligent Crowd Analytics"
                + "\v"
                + "and Decision Support Platform"
            ],
        )
    # College header / supervisor / presented-by stay (student identity)
    sub = find_shape(s, "Subtitle 2")
    if sub:
        set_shape_paragraphs(sub, ["Presented By:-" + "\v" + "V. Akshitha :- 23B81A05K6"])

    # ── Slide 2: Abstract ───────────────────────────────────────────
    s = slides[1]
    set_title(s, "Abstract")
    content = find_content_shape(s)
    abstract = (
        "This project presents CrowdPulse, an Intelligent Crowd Analytics and Decision "
        "Support Platform that converts CCTV video into zone-level risk, explanations, "
        "and recommended control-room actions. Unlike counting-only surveillance tools, "
        "CrowdPulse closes the loop from detection and tracking to Dynamic Crowd Risk "
        "Score (DCRS), Explainable Risk Attribution (ERA), and Gradient Boosting-based "
        "action recommendations for stadium and public-venue operators.\n"
        "\tThe system follows a modular Clean Architecture with a Next.js ops console, "
        "FastAPI backend, JWT role-based access, and SQLite (Postgres-ready) persistence. "
        "It integrates YOLO/HOG person detection, zone analytics, a live digital twin, "
        "what-if simulation, and after-action incident reports—supporting disciplined, "
        "explainable crowd-safety decision making for a venue pilot / panel demo."
    )
    if content:
        # Two paragraphs like sample
        parts = abstract.split("\n\t", 1)
        lines = [parts[0].strip()]
        if len(parts) > 1:
            lines.append("\t" + parts[1].strip())
        set_shape_paragraphs(content, lines)

    # ── Slide 3: Introduction ───────────────────────────────────────
    s = slides[2]
    set_title(s, "Introduction")
    body = find_shape(s, "Rectangle 5") or find_content_shape(s)
    intro_lines = [
        "Large public gatherings still face preventable crush and congestion risks despite widespread CCTV.",
        "Most surveillance tools stop at person counting or simple density alerts.",
        "Operators lack a closed loop from detection -> risk -> explanation -> recommended action.",
        "Critical factors such as speed drop, opposing flow, and exit pressure are rarely combined.",
        "Manual interpretation of video walls is slow, inconsistent, and hard to audit after incidents.",
        "There is a growing need for an explainable, decision-oriented crowd analytics platform for control rooms.",
    ]
    if body:
        set_shape_paragraphs(body, intro_lines)

    # ── Slide 4: Literature table ───────────────────────────────────
    s = slides[3]
    set_title(s, "Literature Review and Objectives:")
    table_shape = None
    for sh in s.shapes:
        if sh.has_table:
            table_shape = sh
            break
    lit_rows = [
        [
            "S.NO",
            "Key Papers & Authors",
            "Implications / Limitations",
            "Major Research Gap Identified",
        ],
        [
            "1",
            "Realtime Crowd Monitoring using Hybridized YOLOv4 (IEEE Access, 2023)",
            "Strong count, speed, and direction estimation with detection + tracking.",
            "No multi-factor risk score, explainability, or actionable decision support.",
        ],
        [
            "2",
            "Integrated Crowd Counting using IoT, OpenCV and YOLO (IEEE IC-CGU, 2024)",
            "Practical real-time density pipeline with YOLO on live camera feeds.",
            "Detection-centric; lacks forecasting, XAI, and what-if simulation.",
        ],
        [
            "3",
            "Crowd Density Forecasting with Encoder-Decoder LSTM (IEEE I2CACIS, 2024)",
            "Shows value of short-horizon multi-camera density prediction.",
            "Density-only forecast without decision engine or digital twin ops loop.",
        ],
        [
            "4",
            "AI-Based Predictive Crowd Monitoring & Stampede Prevention (IEEE GIEST, 2025)",
            "Combines YOLOv8 with short LSTM horizon and graded alerts.",
            "Limited horizon; no explainable actions, accept/dismiss workflow, or reports.",
        ],
        [
            "5",
            "Predicting & Optimizing Crowd Evacuations with XAI (2025)",
            "Uses model explanations for evacuation-related recommendations.",
            "Mostly offline simulation advice; not a live CCTV digital-twin platform.",
        ],
    ]
    if table_shape:
        fill_table(table_shape.table, lit_rows)

    # ── Slide 5: Objectives ─────────────────────────────────────────
    s = slides[4]
    set_title(s, "Literature Review and Objectives:")
    content = find_content_shape(s)
    obj_lines = [
        "Objectives:",
        "Design an end-to-end crowd analytics platform from CCTV ingest to operator decisions.",
        "Detect and track people using YOLO (with HOG fallback) and map them to venue zones.",
        "Compute a Dynamic Crowd Risk Score (DCRS) with Green / Yellow / Orange / Red bands.",
        "Explain every alert using Explainable Risk Attribution (ERA) feature contributions.",
        "Recommend control-room actions with Gradient Boosting plus a safety constraint layer.",
        "Deliver a secured ops dashboard with digital twin, what-if simulation, and incident reports.",
    ]
    if content:
        set_shape_paragraphs(content, obj_lines)

    # ── Slide 6: Existing Systems ───────────────────────────────────
    s = slides[5]
    set_title(s, "Existing Systems")
    content = find_content_shape(s)
    existing = [
        "Commercial CCTV / VMS platforms mainly provide live video walls and basic motion or intrusion alerts without crowd-risk decision support.",
        "YOLO-based academic crowd counters estimate density or headcount but typically stop at perception and do not recommend gate, PA, or redeployment actions.",
        "Learning / IoT density dashboards visualize occupancy yet lack explainable multi-factor risk scoring and operator Accept / Dismiss workflows.",
        "Most existing tools do not combine zone digital twins, what-if simulation, and after-action incident reporting in one stack.",
        "Current platforms rarely enforce role-based control-room access that separates Operator viewing from Admin CCTV ingest and pipeline control.",
    ]
    if content:
        set_shape_paragraphs(content, existing)

    # ── Slide 7: Problem Statement ──────────────────────────────────
    s = slides[6]
    set_title(s, "Problem Statement")
    content = find_content_shape(s)
    problem = (
        "Existing crowd-surveillance systems do not provide an integrated mechanism for converting "
        "CCTV observations into multi-factor risk scores, natural-language explanations, and ranked "
        "operational actions. Most platforms focus only on person counting or threshold density alerts "
        "without considering speed drop, opposing flow, exit pressure, or operator accountability. As a "
        "result, control rooms struggle to prioritize interventions during congestion events.\n"
        "The absence of explainable risk attribution, Gradient Boosting-driven recommendations, live "
        "digital-twin visualization, and what-if simulation makes crowd decision support incomplete and "
        "hard to audit. Important video evidence is not automatically turned into zone analytics and "
        "after-action reports. This creates a strong need for a centralized platform that supports "
        "intelligent, explainable crowd-safety decision making."
    )
    if content:
        parts = problem.split("\n", 1)
        set_shape_paragraphs(content, [p.strip() for p in parts])

    # ── Slide 8: Functional / Non-Functional ────────────────────────
    s = slides[7]
    set_title(s, "Functional And Non-Functional Requirements:")
    # Keep section headers
    fr_header = find_shape(s, "Text Placeholder 2")
    nfr_header = find_shape(s, "Text Placeholder 4")
    if fr_header:
        set_shape_paragraphs(fr_header, ["Functional Requirements"])
    if nfr_header:
        set_shape_paragraphs(nfr_header, ["Non-Functional Requirements"])

    fr_box = find_shape(s, "Rectangle 1")
    nfr_box = find_shape(s, "Rectangle 2")
    functional = [
        "JWT Authentication & Role-Based Access",
        "CCTV / Sample Video Ingest (Admin)",
        "Person Detection, Tracking & Zone Mapping",
        "DCRS Risk Scoring & Alert Generation",
        "ERA Explainability for Every Alert",
        "Gradient Boosting Action Recommendations",
        "Digital Twin, What-If & Incident Reports",
    ]
    non_functional = [
        "Modular, replaceable Clean Architecture",
        "Acceptable near-real-time pipeline latency",
        "Secure auth; secrets via environment config",
        "Graceful handling of empty / failed video",
        "Responsive ops-console user interface",
        "Maintainability with typed APIs & validation",
    ]
    if fr_box:
        set_shape_paragraphs(fr_box, functional)
    if nfr_box:
        set_shape_paragraphs(nfr_box, non_functional)

    # ── Slide 9: Hardware & Software ────────────────────────────────
    s = slides[8]
    set_title(s, "Hardware & Software Requirements")
    content = find_content_shape(s)
    hw_sw = [
        "Hardware Requirements",
        "Minimum 8 GB RAM (16 GB recommended for YOLO)",
        "Intel i5 / Ryzen 5 processor or higher",
        "Stable internet connection (local demo can run offline)",
        "20 GB free disk space for models, videos, and dependencies",
        "Software Requirements",
        "Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts",
        "Backend: Python, FastAPI, Uvicorn, Pydantic, JWT / bcrypt",
        "Database: SQLite (Postgres-ready via SQLAlchemy)",
        "Computer Vision: Ultralytics YOLOv8n / OpenCV HOG, NumPy",
        "Machine Learning: scikit-learn Gradient Boosting",
        "Development Tools: VS Code, Git & GitHub, Docker (optional)",
    ]
    if content:
        set_shape_paragraphs(content, hw_sw)

    # ── Slide 10: Proposed Methodology ──────────────────────────────
    s = slides[9]
    set_title(s, "Proposed Methodology")
    content = find_content_shape(s)
    method = [
        "The system is designed using modular Clean Architecture (API -> use-cases -> AI / data ports).",
        "Admin uploads or selects sample CCTV; the pipeline samples frames and runs detection + tracking.",
        "Detections are assigned to venue zones; density, speed, and flow metrics are computed per zone.",
        "DCRS converts multi-factor signals into a 0-100 risk score and G/Y/O/R band.",
        "ERA attaches top contributing factors and an explanation narrative to each alert.",
        "Gradient Boosting ranks interventions; a safety filter blocks unsafe actions (e.g., last-exit close).",
        "The Next.js digital twin updates zone colors and the operator decision queue in real time.",
        "Operators Accept / Dismiss actions, run what-if scenarios, and generate incident reports.",
    ]
    if content:
        set_shape_paragraphs(content, method)

    delete_slides_after(prs, 10)
    prs.save(str(OUT))
    try:
        shutil.copy2(OUT, OUT_DESKTOP)
    except Exception as exc:
        print("Desktop copy skipped:", exc)
    print("Saved:", OUT)
    print("Slides:", len(list(Presentation(str(OUT)).slides)))
    return OUT


if __name__ == "__main__":
    build()

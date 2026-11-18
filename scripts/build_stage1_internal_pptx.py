"""Build CrowdPulse Stage-I Major Project Internal Evaluation PPT."""

from __future__ import annotations

import shutil
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches, Pt

TEMPLATE = Path(
    r"c:\Users\akshi\Downloads\Stage- I-Major project Internal evaluation-I  PPT template.pptx"
)
OUT = Path(r"c:\MAJORPROJECT\docs\CrowdPulse_Stage1_Internal_Evaluation.pptx")
OUT_DOWNLOADS = Path(
    r"c:\Users\akshi\Downloads\CrowdPulse_Stage1_Internal_Evaluation.pptx"
)
ASSET = Path(r"c:\MAJORPROJECT\docs\assets\ppt_placeholders")
ASSET.mkdir(parents=True, exist_ok=True)

# ── helpers ────────────────────────────────────────────────────────────────


def set_run_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def set_shape_lines(shape, lines: list[str], clear_extra: bool = True) -> None:
    if shape is None:
        return
    tf = shape.text_frame
    paras = list(tf.paragraphs)
    for i, line in enumerate(lines):
        if i < len(paras):
            set_run_text(paras[i], line)
        else:
            p = tf.add_paragraph()
            p.text = line
            if paras:
                p.level = paras[min(i, len(paras) - 1)].level
    if clear_extra:
        for j in range(len(lines), len(paras)):
            set_run_text(paras[j], "")


def find_shape(slide, *names: str):
    for sh in slide.shapes:
        if sh.name in names:
            return sh
    return None


def find_table(slide):
    for sh in slide.shapes:
        if sh.has_table:
            return sh.table
    return None


def set_title(slide, title: str) -> None:
    for sh in slide.shapes:
        if sh.name.lower().startswith("title") and sh.has_text_frame:
            set_shape_lines(sh, [title])
            return


def fill_table(table, rows: list[list[str]]) -> None:
    for r_i, row_data in enumerate(rows):
        if r_i >= len(table.rows):
            break
        for c_i, cell_text in enumerate(row_data):
            if c_i >= len(table.columns):
                break
            cell = table.cell(r_i, c_i)
            paras = list(cell.text_frame.paragraphs)
            if paras:
                set_run_text(paras[0], cell_text)
                for p in paras[1:]:
                    set_run_text(p, "")
            else:
                cell.text = cell_text


def add_table_rows(table, count: int) -> None:
    tbl = table._tbl
    template_row = tbl.tr_lst[-1]
    for _ in range(count):
        tbl.append(deepcopy(template_row))


def remove_hint_textboxes(slide) -> None:
    for sh in list(slide.shapes):
        if not sh.has_text_frame:
            continue
        if sh.name.lower().startswith("textbox") and "**" in (sh.text or ""):
            sp = sh._element
            sp.getparent().remove(sp)


def add_body_box(slide, lines: list[str], *, top=Inches(1.45), font_size: int = 18) -> None:
    left, width, height = Inches(0.65), Inches(11.5), Inches(4.85)
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.level = 0
        p.space_after = Pt(6)
        if p.runs:
            p.runs[0].font.size = Pt(font_size)


def placeholder_image(path: Path, title: str, lines: list[str], size=(1280, 720)) -> Path:
    img = Image.new("RGB", size, (245, 247, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, size[0] - 20, size[1] - 20], outline=(31, 78, 121), width=4)
    try:
        font_t = ImageFont.truetype("arial.ttf", 36)
        font_b = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font_t = ImageFont.load_default()
        font_b = font_t
    draw.text((50, 40), title, fill=(31, 78, 121), font=font_t)
    y = 110
    for line in lines:
        draw.text((50, y), line, fill=(30, 30, 30), font=font_b)
        y += 36
    draw.text((50, size[1] - 60), "CrowdPulse — Stage-I Internal Evaluation", fill=(100, 100, 100), font=font_b)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def add_architecture_picture(slide, image_path: Path) -> None:
    slide.shapes.add_picture(str(image_path), Inches(0.55), Inches(1.35), width=Inches(11.6))


# ── build ────────────────────────────────────────────────────────────────────


def build() -> Path:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE, OUT)
    prs = Presentation(str(OUT))
    slides = list(prs.slides)

    # Slide 1 — Title
    s = slides[0]
    set_shape_lines(
        find_shape(s, "Title 1"),
        [
            "CVR COLLEGE OF ENGINEERING"
            + "\v"
            + "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING"
        ],
    )
    set_shape_lines(
        find_shape(s, "Subtitle 2"),
        [
            "Stage-I Major Project Internal Evaluation - I",
            "on",
            "CrowdPulse: An Intelligent Crowd Analytics and Decision Support Platform",
            "by",
            "V. Akshitha — 23B81A05K6",
            "Under guidance of",
            "Mr. M. Hanimi Reddy, Sr. Assistant Professor, CSE",
        ],
    )

    # Slide 2 — Contents
    s = slides[1]
    set_title(s, "Contents")
    set_shape_lines(
        find_shape(s, "TextBox 3"),
        [
            "1. Abstract",
            "2. Motivation",
            "3. Literature Review",
            "4. Limitations of the Existing Work — Research Gaps",
            "5. Proposed Problem Statement",
            "6. Proposed Approach of the Work",
            "7. User / Stakeholder Requirement Analysis",
            "8. Software Requirements / Technology Stack",
            "9. Hardware Requirements",
            "10. Data Sets Requirement",
            "11. Proposed Architecture of the Model",
            "12. Innovation in the Project",
            "13. Plan of Action to Complete the Project",
            "14. References",
        ],
    )

    # Slide 3 — Abstract
    s = slides[2]
    set_title(s, "Abstract")
    add_body_box(
        s,
        [
            "CrowdPulse is an Intelligent Crowd Analytics and Decision Support Platform designed "
            "for stadium and public-venue control rooms. The system converts CCTV or sample video "
            "into zone-level crowd intelligence, Dynamic Crowd Risk Score (DCRS), explainable alerts, "
            "and Gradient Boosting-based action recommendations.",
            "Unlike conventional counting-only surveillance, CrowdPulse closes the operational loop "
            "from person detection and tracking to risk explanation, recommended interventions, "
            "operator Accept/Dismiss logging, what-if simulation, and after-action reporting. "
            "The platform follows Clean Architecture with FastAPI, Next.js, JWT role-based access, "
            "and schema-backed persistence, supporting a venue pilot demonstration aligned with "
            "real-world crowd-safety decision support.",
        ],
        font_size=17,
    )

    # Slide 4 — Motivation
    s = slides[3]
    set_title(s, "Motivation")
    add_body_box(
        s,
        [
            "Large public gatherings at stadiums, festivals, and transit hubs still face preventable crush and congestion risks.",
            "CCTV is widely deployed, yet control rooms depend on manual monitoring of many feeds with limited decision support.",
            "Most existing tools provide headcount or density alerts but not multi-factor early warning.",
            "Critical signals such as speed drop, opposing flow, and exit pressure are rarely combined into one risk score.",
            "Operators lack explainable guidance on why an alert fired and what safe action to take next.",
            "There is a strong need for a centralized, auditable, AI-assisted crowd analytics platform for authorities.",
        ],
    )

    # Slide 5 — Literature review
    s = slides[4]
    set_title(s, "Literature review")
    remove_hint_textboxes(s)
    table = find_table(s)
    if table:
        needed = 7  # header + 6 papers
        while len(table.rows) < needed:
            add_table_rows(table, 1)
        fill_table(
            table,
            [
                [
                    "S.NO",
                    "Name of the Authors(s)",
                    "Title of the Paper (Published year)",
                    "Observations / Findings",
                    "Limitations",
                ],
                [
                    "1",
                    "J. Redmon et al.",
                    "You Only Look Once: Unified Real-Time Object Detection (CVPR, 2016)",
                    "Foundation for real-time person detection in crowded scenes.",
                    "No zone analytics, risk scoring, or operator decision support.",
                ],
                [
                    "2",
                    "N. Wojke, A. Bewley, D. Paulus",
                    "Simple Online and Realtime Tracking with Deep Association Metric (ICIP, 2017)",
                    "Robust identity-aware tracking through occlusions.",
                    "Heavy for flow-speed analytics; no risk/action pipeline.",
                ],
                [
                    "3",
                    "Y. Li, X. Zhang, D. Chen",
                    "CSRNet: Understanding Highly Congested Scenes (CVPR, 2018)",
                    "Strong extreme-density counting via density maps.",
                    "No per-person motion; cannot compute flow-speed early warning.",
                ],
                [
                    "4",
                    "K. Khan et al.",
                    "Crowd Monitoring and Localization Frameworks: A Review (Sensors, 2020)",
                    "Comprehensive survey of real-time crowd monitoring methods.",
                    "Most surveyed systems remain reactive threshold alerts.",
                ],
                [
                    "5",
                    "E. T. Endalamaw",
                    "Dense Crowd Activity Detection using YOLOv8 and DeepSORT (IET, 2025)",
                    "Accurate detection and tracking in dense crowds.",
                    "Current-state analytics only; no DCRS or recommendations.",
                ],
                [
                    "6",
                    "F. Pedregosa et al.",
                    "Scikit-learn: Machine Learning in Python (JMLR, 2011)",
                    "Enables practical ensemble models such as Gradient Boosting.",
                    "General ML library; not a domain-specific crowd decision system.",
                ],
            ],
        )

    # Slide 6 — Research gaps
    s = slides[5]
    set_title(s, "Limitations of the Existing Work- Research Gaps")
    add_body_box(
        s,
        [
            "Existing CCTV/VMS platforms focus on video viewing and basic motion alerts, not multi-factor crowd-risk decision support.",
            "Academic YOLO-based counters often stop at perception (count/density) without recommending control-room actions.",
            "IoT occupancy dashboards visualize density but lack explainable risk attribution and operator accountability workflows.",
            "Few systems integrate digital twins, what-if simulation, and after-action incident reporting in one stack.",
            "Reactive threshold alerts miss early warning from speed drop, opposing flow, and exit pressure combined.",
            "Research gap: an integrated platform linking detection → DCRS → ERA explanation → Gradient Boosting recommendations → logged operator decisions.",
        ],
    )

    # Slide 7 — Problem statement
    s = slides[6]
    set_title(s, "Proposed Problem statement")
    remove_hint_textboxes(s)
    add_body_box(
        s,
        [
            "To design and develop an intelligent crowd analytics and decision support platform that "
            "analyzes multi-factor crowd risk from CCTV/video, explains alerts to control-room operators, "
            "recommends safe interventions, and maintains an auditable decision loop for public-venue crowd safety.",
        ],
        top=Inches(1.8),
        font_size=20,
    )

    # Slide 8 — Proposed approach
    s = slides[7]
    set_title(s, "Proposed Approach of the work")
    remove_hint_textboxes(s)
    add_body_box(
        s,
        [
            "Video ingest: Admin uploads CCTV clips or runs seeded sample videos (sparse / medium / dense).",
            "Person detection: Ultralytics YOLOv8n (COCO person class) with OpenCV HOG fallback on CPU.",
            "Tracking: Centroid + IoU tracker for short-term movement and flow-speed estimation.",
            "Zone analytics: Map detections to venue zones; compute density, speed drop, opposing flow, exit pressure.",
            "Risk engine: DCRS — weighted logistic/sigmoid over multi-factor features → G/Y/O/R band.",
            "Explainability: ERA (Explainable Risk Attribution) ranks top contributing features per alert.",
            "Recommendations: scikit-learn Gradient Boosting multi-label classifier ranks actions; safety filter blocks unsafe options.",
            "Ops layer: Next.js digital twin, JWT Operator/Admin roles, what-if simulation, incident reports.",
        ],
        font_size=16,
    )

    # Slide 9 — Stakeholder requirements
    s = slides[8]
    set_title(s, "User/Stakeholder Requirement Analysis")
    add_body_box(
        s,
        [
            "Control-room Operator (primary user)",
            "• Monitor live digital twin with zone risk colors and alert queue",
            "• View ERA explanations and ranked recommended actions",
            "• Accept or Dismiss interventions; run what-if scenarios; generate after-action reports",
            "",
            "Venue Admin / System Admin",
            "• Secure login with role-based access (JWT)",
            "• Upload or process CCTV/sample video through the perception pipeline",
            "• Manage venue topology, cameras, and historical alert/decision logs",
            "",
            "Stakeholders: venue security, event managers, safety officers, audit/compliance teams",
        ],
        font_size=17,
    )

    # Slide 10 — Software stack
    s = slides[9]
    set_title(s, "Software  Requirements/Technology stack")
    add_body_box(
        s,
        [
            "Frontend: Next.js 14, React, TypeScript, Tailwind CSS, Recharts",
            "Backend: Python 3.11+, FastAPI, Pydantic, Uvicorn, Clean Architecture use-cases",
            "Authentication: JWT (PyJWT), bcrypt, Operator / Admin RBAC",
            "Database: SQLAlchemy async, SQLite (Postgres-ready schema)",
            "Computer Vision: OpenCV, Ultralytics YOLOv8, NumPy",
            "Machine Learning: scikit-learn GradientBoostingClassifier (multi-label actions)",
            "Reporting: Template markdown with optional Ollama local LLM",
            "DevOps / Tools: Git, Docker-ready layout, pydantic-settings, structured logging",
        ],
        font_size=17,
    )

    # Slide 11 — Hardware
    s = slides[10]
    set_title(s, "Hardware requirements")
    add_body_box(
        s,
        [
            "Processor: Intel i3 / i5 or equivalent (64-bit)",
            "RAM: Minimum 8 GB (16 GB recommended when running YOLO inference)",
            "Storage: 20 GB free disk space (models, demo videos, SQLite DB)",
            "GPU: Not mandatory — CPU inference supported; optional GPU improves YOLO throughput",
            "Network: Stable connection for API/UI; offline-capable for local demo rehearsal",
            "Display: Full HD monitor for control-room dashboard demonstration",
            "Input: Standard keyboard/mouse; sample MP4 or uploaded CCTV clips for processing",
        ],
    )

    # Slide 12 — Datasets
    s = slides[11]
    set_title(s, "Data Sets requirement")
    add_body_box(
        s,
        [
            "Person detection: Public pretrained YOLOv8n weights (COCO person class); OpenCV HOG fallback — no custom detector training for Level A.",
            "Action recommender: ~3000 synthetic multi-factor crowd-risk scenarios with rule-derived multi-label action labels; Gradient Boosting benchmarked vs Random Forest.",
            "Demo video: Procedurally generated sparse / medium / dense CCTV-like MP4 clips (reproducible, copyright-safe for viva).",
            "Venue topology: Seeded schema-backed demo venue (Aether Arena) — zones, exits, cameras in SQLite.",
            "Honest scope: No private police CCTV corpus claimed; real venue footage can be uploaded by Admin when available.",
        ],
        font_size=16,
    )

    # Slide 13 — Architecture
    s = slides[12]
    set_title(s, "Proposed Architecture of the Model ")
    arch_img = placeholder_image(
        ASSET / "stage1_architecture.png",
        "CrowdPulse System Architecture",
        [
            "CCTV / Sample Video",
            "  → Perception (YOLO / HOG + Centroid-IoU Tracker)",
            "  → Zone Analytics (density, speed, flow, exit pressure)",
            "  → DCRS Risk Engine + ERA Explainability",
            "  → Gradient Boosting Action Recommender + Safety Filter",
            "  → FastAPI (JWT) + SQLite + Digital Twin Store",
            "  → Next.js Ops Console (Operator / Admin)",
        ],
    )
    add_architecture_picture(s, arch_img)

    # Slide 14 — Innovation
    s = slides[13]
    set_title(s, "Innovation in the project")
    add_body_box(
        s,
        [
            "Beyond counting: Multi-factor Dynamic Crowd Risk Score (DCRS) with Green/Yellow/Orange/Red bands.",
            "Explainable alerts: ERA feature contributions tell operators why risk is high — not a black-box alert.",
            "Decision support: Gradient Boosting ranks control-room actions with confidence scores.",
            "Safety-aware AI: Deterministic constraint layer blocks unsafe recommendations (e.g., closing last exit).",
            "Digital twin: Live venue map colored by zone risk with alert and decision queue.",
            "What-if simulation: Re-score risk under scenarios (close exit, rain, VIP surge) before acting.",
            "Closed operator loop: Accept/Dismiss logging, historical audit trail, and after-action incident reports.",
        ],
        font_size=16,
    )

    # Slide 15 — Plan of action
    s = slides[14]
    set_title(s, "Plan of action to complete the project")
    remove_hint_textboxes(s)
    table = find_table(s)
    if table:
        rows_needed = 9  # header + 8 modules
        while len(table.rows) < rows_needed:
            add_table_rows(table, 1)
        fill_table(
            table,
            [
                ["S.NO", "ITEM", "Percentage of Completion"],
                ["1", "Requirements, architecture & database schema", "100%"],
                ["2", "Authentication, API layer & Clean Architecture use-cases", "100%"],
                ["3", "Person detection, tracking & zone analytics pipeline", "90%"],
                ["4", "DCRS risk engine & ERA explainability module", "95%"],
                ["5", "Gradient Boosting recommender & safety filter", "95%"],
                ["6", "Next.js digital twin dashboard & decision workflow", "90%"],
                ["7", "What-if simulation & incident reporting", "85%"],
                ["8", "Panel demo rehearsal, documentation & viva preparation", "80%"],
                ["", "Overall project completion (Stage-I baseline)", "~88%"],
            ],
        )
    add_body_box(
        s,
        [
            "Remaining work (Level B): multi-camera fusion, live RTSP ingest, Postgres/Timescale scale-out, mobile alert client.",
        ],
        top=Inches(5.35),
        font_size=14,
    )

    # Slide 16 — References
    s = slides[15]
    set_title(s, "References")
    remove_hint_textboxes(s)
    add_body_box(
        s,
        [
            "[1] J. Redmon, S. Divvala, R. Girshick, and F. Farhadi, \"You Only Look Once: Unified, Real-Time Object Detection,\" Proc. IEEE CVPR, 2016.",
            "[2] N. Wojke, A. Bewley, and D. Paulus, \"Simple Online and Realtime Tracking with a Deep Association Metric,\" Proc. IEEE ICIP, 2017.",
            "[3] Y. Li, X. Zhang, and D. Chen, \"CSRNet: Dilated Convolutional Neural Networks for Understanding the Highly Congested Scenes,\" Proc. IEEE CVPR, 2018.",
            "[4] K. Khan, S. Lee, and S. Kim, \"Crowd Monitoring and Localization Frameworks: A Review,\" Sensors, vol. 20, no. 20, 2020.",
            "[5] E. T. Endalamaw, \"Dense Crowd Activity Detection using YOLOv8 and DeepSORT,\" IET Image Processing, 2025.",
            "[6] F. Pedregosa et al., \"Scikit-learn: Machine Learning in Python,\" JMLR, vol. 12, pp. 2825–2830, 2011.",
            "[7] Ultralytics, YOLOv8 Documentation. [Online]. Available: https://docs.ultralytics.com",
            "[8] I. Sommerville, Software Engineering, 10th ed. Pearson, 2016.",
        ],
        top=Inches(1.35),
        font_size=14,
    )

    prs.save(str(OUT))
    try:
        shutil.copy2(OUT, OUT_DOWNLOADS)
    except Exception as exc:
        print("Downloads copy skipped:", exc)

    print("Saved:", OUT)
    print("Slides:", len(list(Presentation(str(OUT)).slides)))
    return OUT


if __name__ == "__main__":
    build()

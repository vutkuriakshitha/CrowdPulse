"""Build full 31-slide CrowdPulse IOMP PPTX from the sample template."""

from __future__ import annotations

import shutil
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

SAMPLE = Path(
    r"c:\Users\akshi\OneDrive\Desktop\ASHU\ALL\PROJECTS\3-2 PROJECT FULL"
    r"\IOMP 23B81A05K6  FINAL.pptx"
)
OUT = Path(r"c:\MAJORPROJECT\docs\CrowdPulse_IOMP_FULL.pptx")
OUT_DESKTOP = Path(
    r"c:\Users\akshi\OneDrive\Desktop\ASHU\ALL\PROJECTS\3-2 PROJECT FULL"
    r"\CrowdPulse_IOMP_FULL.pptx"
)


def set_run_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def set_shape_paragraphs(shape, lines: list[str], clear_extra: bool = True) -> None:
    tf = shape.text_frame
    paras = list(tf.paragraphs)
    for i, line in enumerate(lines):
        if i < len(paras):
            set_run_text(paras[i], line)
        else:
            p = tf.add_paragraph()
            p.text = line
            if paras:
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
    best = None
    best_area = 0
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        name = sh.name.lower()
        if name.startswith("title") or "slide number" in name:
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


def remove_pictures(slide) -> None:
    """Remove Timely Sync screenshot pictures so wrong UI is not shown."""
    pics = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
    for pic in pics:
        sp = pic._element
        sp.getparent().remove(sp)


def set_content_or_add(slide, lines: list[str]) -> None:
    content = find_content_shape(slide)
    if content and content.has_text_frame:
        set_shape_paragraphs(content, lines)
        return
    # Fallback: add a text box in content area
    box = slide.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(12), Inches(5.2))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.level = 0
        p.font.size = Pt(16)
        p.font.name = "Calibri"


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SAMPLE, OUT)
    prs = Presentation(str(OUT))
    slides = list(prs.slides)

    # 1 Title
    s = slides[0]
    title = find_shape(s, "Title 1")
    if title:
        set_shape_paragraphs(
            title,
            ["CrowdPulse - Intelligent Crowd Analytics" + "\v" + "and Decision Support Platform"],
        )
    sub = find_shape(s, "Subtitle 2")
    if sub:
        set_shape_paragraphs(sub, ["Presented By:-" + "\v" + "V. Akshitha :- 23B81A05K6"])

    # 2 Abstract
    s = slides[1]
    set_title(s, "Abstract")
    set_content_or_add(
        s,
        [
            "This project presents CrowdPulse, an Intelligent Crowd Analytics and Decision Support Platform that converts CCTV video into zone-level risk, explanations, and recommended control-room actions. Unlike counting-only surveillance tools, CrowdPulse closes the loop from detection and tracking to Dynamic Crowd Risk Score (DCRS), Explainable Risk Attribution (ERA), and Gradient Boosting-based action recommendations for stadium and public-venue operators.",
            "\tThe system follows a modular Clean Architecture with a Next.js ops console, FastAPI backend, JWT role-based access, and SQLite (Postgres-ready) persistence. It integrates YOLO/HOG person detection, zone analytics, a live digital twin, what-if simulation, and after-action incident reports for explainable crowd-safety decision making.",
        ],
    )

    # 3 Introduction
    s = slides[2]
    set_title(s, "Introduction")
    body = find_shape(s, "Rectangle 5") or find_content_shape(s)
    if body:
        set_shape_paragraphs(
            body,
            [
                "Large public gatherings still face preventable crush and congestion risks despite widespread CCTV.",
                "Most surveillance tools stop at person counting or simple density alerts.",
                "Operators lack a closed loop from detection -> risk -> explanation -> recommended action.",
                "Critical factors such as speed drop, opposing flow, and exit pressure are rarely combined.",
                "Manual interpretation of video walls is slow, inconsistent, and hard to audit after incidents.",
                "There is a growing need for an explainable, decision-oriented crowd analytics platform for control rooms.",
            ],
        )

    # 4 Literature table
    s = slides[3]
    set_title(s, "Literature Review and Objectives:")
    for sh in s.shapes:
        if sh.has_table:
            fill_table(
                sh.table,
                [
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
                        "Limited horizon; no explainable actions, Accept/Dismiss workflow, or reports.",
                    ],
                    [
                        "5",
                        "Predicting & Optimizing Crowd Evacuations with XAI (2025)",
                        "Uses model explanations for evacuation-related recommendations.",
                        "Mostly offline simulation advice; not a live CCTV digital-twin platform.",
                    ],
                ],
            )

    # 5 Objectives
    s = slides[4]
    set_title(s, "Literature Review and Objectives:")
    set_content_or_add(
        s,
        [
            "Objectives:",
            "Design an end-to-end crowd analytics platform from CCTV ingest to operator decisions.",
            "Detect and track people using YOLO (with HOG fallback) and map them to venue zones.",
            "Compute a Dynamic Crowd Risk Score (DCRS) with Green / Yellow / Orange / Red bands.",
            "Explain every alert using Explainable Risk Attribution (ERA) feature contributions.",
            "Recommend control-room actions with Gradient Boosting plus a safety constraint layer.",
            "Deliver a secured ops dashboard with digital twin, what-if simulation, and incident reports.",
        ],
    )

    # 6 Existing Systems
    s = slides[5]
    set_title(s, "Existing Systems")
    set_content_or_add(
        s,
        [
            "Commercial CCTV / VMS platforms mainly provide live video walls and basic motion or intrusion alerts without crowd-risk decision support.",
            "YOLO-based academic crowd counters estimate density or headcount but typically stop at perception and do not recommend gate, PA, or redeployment actions.",
            "IoT density dashboards visualize occupancy yet lack explainable multi-factor risk scoring and operator Accept / Dismiss workflows.",
            "Most existing tools do not combine zone digital twins, what-if simulation, and after-action incident reporting in one stack.",
            "Current platforms rarely enforce role-based control-room access that separates Operator viewing from Admin CCTV ingest and pipeline control.",
        ],
    )

    # 7 Problem Statement
    s = slides[6]
    set_title(s, "Problem Statement")
    set_content_or_add(
        s,
        [
            "Existing crowd-surveillance systems do not provide an integrated mechanism for converting CCTV observations into multi-factor risk scores, natural-language explanations, and ranked operational actions. Most platforms focus only on person counting or threshold density alerts without considering speed drop, opposing flow, exit pressure, or operator accountability. As a result, control rooms struggle to prioritize interventions during congestion events.",
            "The absence of explainable risk attribution, Gradient Boosting-driven recommendations, live digital-twin visualization, and what-if simulation makes crowd decision support incomplete and hard to audit. Important video evidence is not automatically turned into zone analytics and after-action reports. This creates a strong need for a centralized platform that supports intelligent, explainable crowd-safety decision making.",
        ],
    )

    # 8 FR / NFR
    s = slides[7]
    set_title(s, "Functional And Non-Functional Requirements:")
    fr_header = find_shape(s, "Text Placeholder 2")
    nfr_header = find_shape(s, "Text Placeholder 4")
    if fr_header:
        set_shape_paragraphs(fr_header, ["Functional Requirements"])
    if nfr_header:
        set_shape_paragraphs(nfr_header, ["Non-Functional Requirements"])
    fr_box = find_shape(s, "Rectangle 1")
    nfr_box = find_shape(s, "Rectangle 2")
    if fr_box:
        set_shape_paragraphs(
            fr_box,
            [
                "JWT Authentication & Role-Based Access",
                "CCTV / Sample Video Ingest (Admin)",
                "Person Detection, Tracking & Zone Mapping",
                "DCRS Risk Scoring & Alert Generation",
                "ERA Explainability for Every Alert",
                "Gradient Boosting Action Recommendations",
                "Digital Twin, What-If & Incident Reports",
            ],
        )
    if nfr_box:
        set_shape_paragraphs(
            nfr_box,
            [
                "Modular, replaceable Clean Architecture",
                "Acceptable near-real-time pipeline latency",
                "Secure auth; secrets via environment config",
                "Graceful handling of empty / failed video",
                "Responsive ops-console user interface",
                "Maintainability with typed APIs & validation",
            ],
        )

    # 9 Hardware & Software
    s = slides[8]
    set_title(s, "Hardware & Software Requirements")
    set_content_or_add(
        s,
        [
            "Hardware Requirements",
            "Minimum 8 GB RAM (16 GB recommended for YOLO)",
            "Intel i5 / Ryzen 5 processor or higher",
            "Stable internet connection (local demo can run offline)",
            "20 GB free disk space for models, videos, and dependencies",
            "No dedicated GPU required",
            "Software Requirements",
            "Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts",
            "Backend: Python, FastAPI, Uvicorn, Pydantic, JWT / bcrypt",
            "Database: SQLite (Postgres-ready via SQLAlchemy)",
            "Computer Vision: Ultralytics YOLOv8n / OpenCV HOG, NumPy",
            "Machine Learning: scikit-learn Gradient Boosting",
            "Development Tools: VS Code, Git & GitHub, Docker (optional)",
        ],
    )

    # 10 Methodology
    s = slides[9]
    set_title(s, "Proposed Methodology")
    set_content_or_add(
        s,
        [
            "The system is designed using modular Clean Architecture (API -> use-cases -> AI / data ports).",
            "Admin uploads or selects sample CCTV; the pipeline samples frames and runs detection + tracking.",
            "Detections are assigned to venue zones; density, speed, and flow metrics are computed per zone.",
            "DCRS converts multi-factor signals into a 0-100 risk score and G/Y/O/R band.",
            "ERA attaches top contributing factors and an explanation narrative to each alert.",
            "Gradient Boosting ranks interventions; a safety filter blocks unsafe actions (e.g., last-exit close).",
            "The Next.js digital twin updates zone colors and the operator decision queue in real time.",
            "Operators Accept / Dismiss actions, run what-if scenarios, and generate incident reports.",
        ],
    )

    # 11 System Architecture
    s = slides[10]
    set_title(s, "System Architecture")
    remove_pictures(s)
    set_content_or_add(
        s,
        [
            "Presentation Layer: Next.js Ops Console (Login, Digital Twin, Risk, Decisions, CCTV, What-If, Reports)",
            "API Layer: FastAPI REST (/api/v1) + JWT RBAC (Operator / Admin)",
            "Application Layer: Use-cases - process video, run pipeline, evaluate risk, simulate, report",
            "AI Layer: Detect (YOLO/HOG) -> Track -> Zone Analytics -> DCRS -> ERA -> Gradient Boosting",
            "Data Layer: SQLite/Postgres (venues, zones, cameras, alerts, decisions, videos) + Twin Store",
            "Flow: CCTV/Sample Video -> Pipeline -> Twin Snapshot -> Dashboard Update",
        ],
    )

    # 12 Class Diagram
    s = slides[11]
    set_title(s, "Class Diagram")
    remove_pictures(s)
    set_content_or_add(
        s,
        [
            "Core domain entities modeled in CrowdPulse:",
            "Venue, Zone, Camera - topology of the monitored site",
            "VideoAsset, Detection, Track - perception pipeline entities",
            "ZoneMetric, RiskScore, RiskExplanation (ERA) - analytics entities",
            "Alert, Decision, DecisionAction - operator workflow entities",
            "Simulation, IncidentReport, User - support and auth entities",
            "Relations: Venue 1-* Zone; Zone 1-* Camera/Metric/Alert; Alert 1-* Decision",
        ],
    )

    # 13 Use-Case Diagram
    s = slides[12]
    set_title(s, "Use-Case Diagram")
    remove_pictures(s)
    set_content_or_add(
        s,
        [
            "Actors: Officer (Operator), Admin, CrowdPulse System",
            "Operator: Login, View Digital Twin Dashboard, Receive Alert, Accept/Dismiss Action, What-If, Generate Report",
            "Admin: All Operator use cases + Upload/Process Footage + Run Pipeline",
            "System: Authenticate, Detect/Track, Compute DCRS, Explain Risk, Recommend Actions, Persist Logs",
            "Goal: Closed-loop control-room decision support from video to action",
        ],
    )

    # 14 Sequence Diagram
    s = slides[13]
    set_title(s, "Sequence Diagram")
    remove_pictures(s)
    set_content_or_add(
        s,
        [
            "Admin -> UI: Select Sample Dense / Process Video",
            "UI -> API: POST /pipeline/run (JWT)",
            "API -> Detect/Track: Sample frames (stride N)",
            "Detect/Track -> API: Zone counts + timeline features",
            "API -> DCRS+ERA+GB: Evaluate risk and recommend actions",
            "Risk Engine -> API: DCRS band, explanation, action cards",
            "API -> Twin Store: Update metrics/alerts",
            "API -> UI: Twin snapshot; UI shows map colors + decision queue",
        ],
    )

    # 15 Activity Diagram
    s = slides[14]
    set_title(s, "Activity Diagram")
    remove_pictures(s)
    set_content_or_add(
        s,
        [
            "Start -> Login (JWT) -> Role check (Operator / Admin)",
            "Admin path: Upload/Select video -> Run pipeline -> Detect -> Track -> Zone assign",
            "Compute features -> DCRS score -> Raise alert if threshold/band exceeded",
            "Attach ERA explanation -> Rank actions (Gradient Boosting) -> Safety filter",
            "Update digital twin dashboard -> Operator Accept/Dismiss -> Log decision",
            "Optional: What-If simulation -> Re-score -> Generate incident report -> End",
        ],
    )

    # 16 Deployment Diagram
    s = slides[15]
    set_title(s, "Deployment Diagram")
    remove_pictures(s)
    set_content_or_add(
        s,
        [
            "Client Node: Browser (Chrome/Edge) accessing Next.js ops console on port 3000",
            "App Server: Node.js hosting Next.js frontend",
            "API Server: Python Uvicorn hosting FastAPI on port 8001",
            "AI Runtime: OpenCV + YOLOv8n (optional) + scikit-learn on same API host",
            "Data Store: SQLite file (Level A) / Postgres-ready for scale-up",
            "Optional: Docker packaging for backend/frontend services",
        ],
    )

    # 17 Implementation modules 1
    s = slides[16]
    set_title(s, "Implementation – Module Description")
    set_content_or_add(
        s,
        [
            "Perception & Zone Analytics",
            "Detects people using YOLOv8n with OpenCV HOG fallback and tracks them across frames.",
            "Maps detections to venue zones and computes density, speed, and opposing-flow features.",
            "Risk Intelligence (DCRS + ERA)",
            "Computes Dynamic Crowd Risk Score and classifies zones into G/Y/O/R bands.",
            "Attaches Explainable Risk Attribution so officers understand why risk is high.",
            "Decision Support",
            "Gradient Boosting ranks control-room actions; safety rules block unsafe suggestions.",
        ],
    )

    # 18 Implementation modules 2
    s = slides[17]
    set_title(s, "Implementation – Module Description")
    set_content_or_add(
        s,
        [
            "CCTV Ingest & Pipeline",
            "Admin uploads CCTV clips or selects sample sparse/medium/dense videos.",
            "Pipeline runs detect-track-risk-recommend and updates the live twin store.",
            "Authentication and Security",
            "Supports JWT login with Operator and Admin roles and protected API routes.",
            "Secrets and auth flags are configured through environment variables.",
            "Dashboard, What-If & Reporting",
            "Shows zone risk map, alerts, decision queue, what-if outcomes, and incident reports.",
            "Persists venues, alerts, decisions, videos, and reports for historical review.",
        ],
    )

    # 19 Coding 1
    s = slides[18]
    set_title(s, "Coding")
    set_content_or_add(
        s,
        [
            "Person Detection and Tracking Pipeline",
            "The system processes CCTV/sample video by sampling frames and running person detection with Ultralytics YOLOv8n. If YOLO weights are unavailable, OpenCV HOG people detection is used as a reliable CPU fallback. A centroid-IoU tracker associates detections across frames to support speed and flow estimation.",
            "Detected persons are assigned to polygonal venue zones. Per-zone analytics then compute density, mean speed, speed drop, and opposing-flow conflict, which become inputs to the Dynamic Crowd Risk Score.",
        ],
    )

    # 20 Coding 2
    s = slides[19]
    set_title(s, "Coding")
    set_content_or_add(
        s,
        [
            "DCRS Risk Scoring and Gradient Boosting Recommendations",
            "CrowdPulse includes a risk intelligence layer that evaluates each zone using multi-factor signals such as density, speed drop, opposing flow, and exit pressure. The DCRS engine produces a 0-100 score and maps it to Green, Yellow, Orange, or Red bands, with ERA explanations attached to alerts.",
            "A scikit-learn Gradient Boosting classifier ranks recommended actions. A deterministic safety filter then blocks unsafe suggestions, for example closing the last remaining exit, before actions appear in the operator decision queue.",
        ],
    )

    # 21 Coding 3
    s = slides[20]
    set_title(s, "Coding")
    set_content_or_add(
        s,
        [
            "Digital Twin Dashboard and Operator Workflow",
            "The Next.js dashboard presents a live digital twin of venue zones with risk colors, alert cards, explanations, and recommended actions. Operators can Accept or Dismiss actions, run what-if scenarios such as exit closure or weather change, and generate incident reports for after-action review.",
            "JWT authentication separates Operator and Admin access. Admin can run the CCTV pipeline, while all key events are logged in a schema-backed database for accountability.",
        ],
    )

    # 22-27 Outcome slides
    outcome_blocks = [
        [
            "Outcome - Control Room Login & Access Control",
            "Secure JWT login with Operator and Admin roles.",
            "Admin can ingest/process CCTV; Operator monitors and decides.",
            "Unauthorized users cannot access the ops console.",
        ],
        [
            "Outcome - Digital Twin Dashboard",
            "Live zone map colored by DCRS risk bands (G/Y/O/R).",
            "Zone metrics and alerts update after pipeline processing.",
            "Control-room view is clear for non-technical officers.",
        ],
        [
            "Outcome - Detection to Risk Pipeline",
            "Sample Dense / uploaded video produces person detections and zone counts.",
            "Multi-factor DCRS identifies high-risk zones beyond density alone.",
            "ERA explanations show top contributing risk factors.",
        ],
        [
            "Outcome - Decision Support",
            "Gradient Boosting recommends ranked actions with confidence.",
            "Safety filter prevents unsafe interventions.",
            "Operators can Accept or Dismiss actions with audit logging.",
        ],
        [
            "Outcome - What-If Simulation",
            "Officers can test scenarios such as closing an exit or weather change.",
            "Twin state is re-scored to show impact before real action.",
            "Supports proactive planning during high-crowd events.",
        ],
        [
            "Outcome - Historical Logging & Reports",
            "Alerts, decisions, videos, and reports are persisted in the database.",
            "Incident reports summarize timeline, risk, and actions taken.",
            "Supports after-action review and academic demonstration.",
        ],
    ]
    for offset, lines in enumerate(outcome_blocks):
        s = slides[21 + offset]
        set_title(s, "Outcome")
        remove_pictures(s)
        set_content_or_add(s, lines)

    # 28 Conclusion
    s = slides[27]
    set_title(s, "Conclusion")
    set_content_or_add(
        s,
        [
            "CrowdPulse - An Intelligent Crowd Analytics and Decision Support Platform is developed to improve control-room decision making during large public gatherings.",
            "It overcomes limitations of counting-only CCTV tools by providing zone risk scoring, explainable alerts, recommended actions, and historical logging.",
            "The system supports CCTV/sample video ingest, YOLO/HOG detection, DCRS risk bands, ERA explanations, Gradient Boosting recommendations, and digital-twin visualization.",
            "It offers a simple ops interface for monitoring zones, accepting actions, running what-if scenarios, and generating incident reports.",
            "Multi-factor early warning using density and flow-speed signals improves usefulness compared with reactive density-threshold systems.",
            "Major modules are implemented and demonstrated as a venue pilot with a modular design that supports future enhancements.",
            "Overall, CrowdPulse enhances crowd-safety awareness, explainability, and decision support through an intelligent web-based platform.",
        ],
    )

    # 29 Future Course of Action
    s = slides[28]
    set_title(s, "Future Course of Action")
    set_content_or_add(
        s,
        [
            "Multi-Camera Fusion: Geometric/appearance fusion to reduce double counting across overlapping cameras.",
            "Live RTSP Integration: Direct streaming from venue cameras into the ops console.",
            "Advanced Forecasting: Stronger short-horizon occupancy/risk prediction on the zone graph.",
            "Scale-up Data Plane: PostgreSQL/Timescale metrics and Redis streams for production load.",
            "Edge Deployment: ONNX-optimized detection nodes closer to cameras.",
            "Mobile Alert Client: Push critical alerts to on-ground officers.",
            "Richer Resource Optimization: Guard/medical/evac placement suggestions tied to predicted congestion.",
            "These enhancements will strengthen CrowdPulse toward city-scale, production control-room use.",
        ],
    )

    # 30 References
    s = slides[29]
    set_title(s, "References")
    set_content_or_add(
        s,
        [
            "1. J. Redmon et al., You Only Look Once: Unified, Real-Time Object Detection, IEEE CVPR, 2016.",
            "2. N. Wojke, A. Bewley, and D. Paulus, Simple Online and Realtime Tracking with a Deep Association Metric (DeepSORT), IEEE ICIP, 2017.",
            "3. Y. Li, X. Zhang, and D. Chen, CSRNet: Dilated Convolutional Neural Networks for Understanding Highly Congested Scenes, IEEE CVPR, 2018.",
            "4. Realtime Crowd Monitoring using Hybridized YOLOv4, IEEE Access, 2023.",
            "5. Integrated Crowd Counting Using IoT, OpenCV and YOLO, IEEE IC-CGU, 2024.",
            "6. Crowd Density Forecasting with Encoder-Decoder LSTM, IEEE I2CACIS, 2024.",
            "7. AI-Based Predictive Crowd Monitoring and Stampede Prevention, IEEE GIEST, 2025.",
            "8. Ultralytics, YOLOv8 Documentation. [Online]. Available: https://docs.ultralytics.com/",
            "9. FastAPI Documentation. [Online]. Available: https://fastapi.tiangolo.com/",
            "10. Next.js Documentation. [Online]. Available: https://nextjs.org/docs",
        ],
    )

    # 31 Thank You
    s = slides[30]
    content = find_content_shape(s) or find_shape(s, "Content Placeholder 1")
    if content:
        set_shape_paragraphs(content, ["THANK YOU"])

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

"""Build full 31-slide CrowdPulse IOMP PPT from sample template."""

from __future__ import annotations

import shutil
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from PIL import Image, ImageDraw, ImageFont

SAMPLE = Path(
    r"c:\Users\akshi\OneDrive\Desktop\ASHU\ALL\PROJECTS\3-2 PROJECT FULL"
    r"\IOMP 23B81A05K6  FINAL.pptx"
)
OUT = Path(r"c:\MAJORPROJECT\docs\CrowdPulse_IOMP_FULL_31.pptx")
OUT_DESK = Path(
    r"c:\Users\akshi\OneDrive\Desktop\ASHU\ALL\PROJECTS\3-2 PROJECT FULL"
    r"\CrowdPulse_IOMP_FULL_31.pptx"
)
ASSET = Path(r"c:\MAJORPROJECT\docs\assets\ppt_placeholders")
ASSET.mkdir(parents=True, exist_ok=True)


def set_run_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def set_shape_lines(shape, lines: list[str], clear_extra: bool = True) -> None:
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


def find_content(slide):
    best = None
    best_area = 0
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        n = sh.name.lower()
        if n.startswith("title") or "slide number" in n:
            continue
        area = (sh.width or 0) * (sh.height or 0)
        if area > best_area:
            best_area = area
            best = sh
    return best


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
    draw.text((50, size[1] - 60), "CrowdPulse — replace with real screenshot/diagram", fill=(100, 100, 100), font=font_b)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def replace_pictures(slide, image_path: Path) -> None:
    """Replace each picture on slide with the same image at same position."""
    pics = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
    for pic in pics:
        left, top, width, height = pic.left, pic.top, pic.width, pic.height
        sp = pic._element
        sp.getparent().remove(sp)
        slide.shapes.add_picture(str(image_path), left, top, width=width, height=height)


def fill_empty_content(slide, lines: list[str]) -> None:
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        n = sh.name.lower()
        if n.startswith("title") or "slide number" in n:
            continue
        if "content" in n or "placeholder" in n or "rectangle" in n:
            # only fill if empty-ish
            existing = (sh.text or "").strip()
            if not existing or len(existing) < 5:
                set_shape_lines(sh, lines)
                return
    content = find_content(slide)
    if content and not (content.text or "").strip():
        set_shape_lines(content, lines)


def build() -> Path:
    shutil.copy2(SAMPLE, OUT)
    prs = Presentation(str(OUT))
    slides = list(prs.slides)

    # ── 1 Title ──
    s = slides[0]
    set_shape_lines(
        find_shape(s, "Title 1"),
        ["CrowdPulse - Intelligent Crowd Analytics" + "\v" + "and Decision Support Platform"],
    )
    set_shape_lines(
        find_shape(s, "Subtitle 2"),
        ["Presented By:-" + "\v" + "V. Akshitha :- 23B81A05K6"],
    )
    # keep college box; update supervisor to current guide if needed - keep sample layout name field
    set_shape_lines(
        find_shape(s, "TextBox 5"),
        [
            "PROJECT SUPERVISOR:",
            "Mr. Nayani Sateesh",
            "Assistant Professor",
            "CSE Department",
        ],
    )

    # ── 2 Abstract ──
    s = slides[1]
    set_title(s, "Abstract")
    set_shape_lines(
        find_content(s),
        [
            "This project presents CrowdPulse, an Intelligent Crowd Analytics and Decision Support Platform that helps control-room officers manage stadium and public-venue crowd safety effectively. It overcomes the limitations of counting-only CCTV tools by providing Dynamic Crowd Risk Score (DCRS), explainable alerts, Gradient Boosting action recommendations, and what-if simulation. The system supports CCTV/sample video ingest, person detection and tracking, and zone-level density analytics.",
            "\tThe system follows a modular Clean Architecture with a responsive Next.js frontend, secure FastAPI backend, and schema-backed SQLite database (Postgres-ready). It integrates digital-twin visualization, risk explanations (ERA), decision Accept/Dismiss logging, and incident reporting. By combining perception with decision support in one platform, CrowdPulse promotes proactive crowd safety and improves operational readiness.",
        ],
    )

    # ── 3 Introduction ──
    s = slides[2]
    set_title(s, "Introduction")
    body = find_shape(s, "Rectangle 5") or find_content(s)
    set_shape_lines(
        body,
        [
            "Large public gatherings create serious crush and congestion risks despite widespread CCTV deployment.",
            "Control rooms still depend on manual monitoring of many camera feeds at the same time.",
            "Most tools raise alerts only after density becomes critical and give little action guidance.",
            "Density alone misses early signals such as speed drop, opposing flow, and exit pressure.",
            "Manual interpretation is slow, inconsistent, and hard to audit after incidents.",
            "There is a growing need for an intelligent, centralized crowd analytics and decision support platform.",
        ],
    )

    # ── 4 Literature table ──
    s = slides[3]
    set_title(s, "Literature Review and Objectives:")
    for sh in s.shapes:
        if sh.has_table:
            fill_table(
                sh.table,
                [
                    ["S.NO", "Key Papers & Authors", "Implications / Limitations", "Major Research Gap Identified"],
                    [
                        "1",
                        "J. Redmon et al. - YOLO (IEEE CVPR, 2016)",
                        "Real-time detection foundation for crowd vision systems.",
                        "No density, risk scoring, or decision support layer.",
                    ],
                    [
                        "2",
                        "N. Wojke et al. - DeepSORT (IEEE ICIP, 2017)",
                        "Strong identity tracking through occlusions.",
                        "Heavy for flow-speed needs; no risk/action pipeline.",
                    ],
                    [
                        "3",
                        "Y. Li et al. - CSRNet (IEEE CVPR, 2018)",
                        "Better extreme-density counting via density maps.",
                        "No per-person motion; cannot compute flow-speed early warning.",
                    ],
                    [
                        "4",
                        "E. T. Endalamaw - YOLOv8 + DeepSORT (IET, 2025)",
                        "Accurate dense-crowd detection and tracking.",
                        "Current-state only; no predictive DCRS or recommendations.",
                    ],
                    [
                        "5",
                        "K. Khan et al. - Crowd Analysis Survey (Sensors, 2020)",
                        "Broad comparison of real-time crowd methods.",
                        "Confirms most systems remain reactive threshold alerts.",
                    ],
                ],
            )
            break

    # ── 5 Objectives ──
    s = slides[4]
    set_title(s, "Literature Review and Objectives:")
    set_shape_lines(
        find_content(s),
        [
            "Objectives:",
            "Design an intelligent crowd analytics and decision support platform for venue control rooms.",
            "Enable CCTV/sample video ingest with person detection and tracking (YOLOv8 / HOG).",
            "Implement Dynamic Crowd Risk Score (DCRS) with flow-speed aware early warning.",
            "Develop a centralized digital-twin dashboard with explainable alerts and actions.",
            "Support historical logging, Accept/Dismiss decisions, what-if simulation, and reports.",
            "Build a secure, modular full-stack system using FastAPI, Next.js, and SQLite.",
        ],
    )

    # ── 6 Existing Systems ──
    s = slides[5]
    set_title(s, "Existing Systems")
    set_shape_lines(
        find_content(s),
        [
            "Commercial CCTV / VMS platforms mainly provide video walls and basic motion alerts without multi-factor crowd-risk decision support.",
            "YOLO-based academic counters estimate density or headcount but typically stop at perception and do not recommend control-room actions.",
            "IoT density dashboards visualize occupancy yet lack explainable risk scoring and Accept/Dismiss workflows.",
            "Most existing systems do not combine digital twins, what-if simulation, and after-action incident reporting in one stack.",
            "Current platforms rarely separate Operator monitoring from Admin CCTV ingest using role-based authentication.",
        ],
    )

    # ── 7 Problem Statement ──
    s = slides[6]
    set_title(s, "Problem Statement")
    set_shape_lines(
        find_content(s),
        [
            "Existing crowd-surveillance systems do not provide an integrated mechanism for analyzing multi-factor crowd risk, explaining alerts, and recommending safe interventions. Most platforms focus only on video viewing or density counting without considering speed drop, opposing flow, exit pressure, and operator accountability. As a result, authorities often detect danger late and lack clear next-step guidance.",
            "The absence of predictive early-warning signals, explainable risk attribution, Gradient Boosting-based recommendations, and historical decision logging makes crowd management inefficient during large gatherings. This creates a strong need for a centralized decision-support platform such as CrowdPulse.",
        ],
    )

    # ── 8 FR / NFR ──
    s = slides[7]
    set_title(s, "Functional And Non-Functional Requirements:")
    set_shape_lines(find_shape(s, "Text Placeholder 2"), ["Functional Requirements"])
    set_shape_lines(find_shape(s, "Text Placeholder 4"), ["Non-Functional Requirements"])
    set_shape_lines(
        find_shape(s, "Rectangle 1"),
        [
            "User Authentication & Authorization",
            "Video Input Capture (CCTV / Sample)",
            "Person Detection & Tracking",
            "Density & DCRS Risk Scoring",
            "Real-Time Digital Twin Dashboard",
            "Alert Generation with ERA",
            "Historical Logging & Reports",
        ],
    )
    set_shape_lines(
        find_shape(s, "Rectangle 2"),
        [
            "System scalability (multi-zone)",
            "Performance (near real-time)",
            "Data security and secure authentication",
            "High availability and reliability",
            "Responsive and user-friendly interface",
            "Maintainability and modular design",
        ],
    )

    # ── 9 Hardware & Software ──
    s = slides[8]
    set_title(s, "Hardware & Software Requirements")
    set_shape_lines(
        find_content(s),
        [
            "Hardware Requirements",
            "Minimum 8 GB RAM (16 GB recommended for YOLO)",
            "Intel i3 / i5 processor or higher",
            "Stable internet connection",
            "20 GB free disk space",
            "No dedicated GPU required",
            "Software Requirements",
            "Frontend: Next.js, React, TypeScript, Tailwind, Recharts",
            "Backend: Python, FastAPI, REST APIs, JWT Authentication",
            "Database: SQLite (Postgres-ready)",
            "Computer Vision: OpenCV, Ultralytics YOLOv8",
            "Machine Learning: scikit-learn Gradient Boosting",
            "Development Tools: VS Code, Git & GitHub",
        ],
    )

    # ── 10 Methodology ──
    s = slides[9]
    set_title(s, "Proposed Methodology")
    set_shape_lines(
        find_content(s),
        [
            "The system is designed using modular Clean Architecture (API, use-cases, AI, data).",
            "The frontend provides login, digital twin, alerts, decisions, what-if, and reports.",
            "The backend handles authentication, video processing, risk calculation, and logging.",
            "CCTV/sample frames are processed using YOLOv8 or OpenCV HOG for person detection.",
            "Tracks are mapped to venue zones; density and flow-speed features are computed.",
            "DCRS generates risk bands and ERA explanations for each alert.",
            "Gradient Boosting ranks actions; a safety filter blocks unsafe suggestions.",
            "Dashboard updates in near real time and stores decisions for historical review.",
        ],
    )

    # ── 11 System Architecture ──
    s = slides[10]
    set_title(s, "System Architecture")
    arch_img = placeholder_image(
        ASSET / "arch.png",
        "CrowdPulse System Architecture",
        [
            "CCTV / Sample Video",
            "    -> Perception (YOLO / HOG + Tracker)",
            "    -> Zone Analytics (density, speed, flow)",
            "    -> DCRS + ERA (risk + explanation)",
            "    -> Gradient Boosting Recommendations",
            "    -> FastAPI + JWT + SQLite",
            "    -> Next.js Digital Twin Dashboard",
            "Actors: Operator (monitor/decide) | Admin (ingest/pipeline)",
        ],
    )
    fill_empty_content(
        s,
        [
            "Presentation: Next.js Ops Console (JWT Login)",
            "API: FastAPI REST /api/v1 + RBAC",
            "AI: Detect -> Track -> Zone -> DCRS -> ERA -> GB",
            "Data: SQLite venues/zones/alerts/decisions + Twin store",
            "Flow: Admin process video -> Risk update -> Operator dashboard",
        ],
    )
    # if no picture, add one
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s.shapes):
        s.shapes.add_picture(str(arch_img), Inches(0.8), Inches(1.5), width=Inches(8.5))
    else:
        replace_pictures(s, arch_img)

    # ── 12 Class Diagram ──
    s = slides[11]
    set_title(s, "Class Diagram")
    class_img = placeholder_image(
        ASSET / "class.png",
        "CrowdPulse Class / Module View",
        [
            "User | Venue | Zone | Camera | VideoAsset",
            "DetectionTrack | ZoneMetric | RiskScore",
            "Alert | RiskExplanation | Decision | Report",
            "Services: Detector, Tracker, DCRSEngine,",
            "ERAExplainer, GBRecommender, TwinStore",
        ],
    )
    replace_pictures(s, class_img)

    # ── 13 Use-Case ──
    s = slides[12]
    set_title(s, "Use-Case Diagram")
    uc_img = placeholder_image(
        ASSET / "usecase.png",
        "CrowdPulse Use-Case Diagram",
        [
            "Actors: Officer (Operator), Admin",
            "Login / Authenticate",
            "View Digital Twin Dashboard",
            "Upload / Process Footage (Admin)",
            "Receive Risk Alert",
            "Accept / Dismiss Action",
            "Run What-If | Generate Incident Report",
        ],
    )
    fill_empty_content(
        s,
        [
            "Actors: Officer (Operator) and Admin",
            "Use cases: Login, View Dashboard, Upload Footage,",
            "Receive Alert, Accept/Dismiss Action, Generate Report",
        ],
    )
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s.shapes):
        s.shapes.add_picture(str(uc_img), Inches(1.2), Inches(1.6), width=Inches(7.8))
    else:
        replace_pictures(s, uc_img)

    # ── 14 Sequence ──
    s = slides[13]
    set_title(s, "Sequence Diagram")
    seq_img = placeholder_image(
        ASSET / "sequence.png",
        "CrowdPulse Sequence (Pipeline)",
        [
            "Admin -> UI: Sample Dense / Process",
            "UI -> API: POST /pipeline/run (JWT)",
            "API -> CV: detect + track frames",
            "API -> Risk: DCRS + ERA + GB",
            "API -> Twin: update metrics/alerts",
            "API -> UI: twin snapshot / decisions",
        ],
    )
    replace_pictures(s, seq_img)

    # ── 15 Activity ──
    s = slides[14]
    set_title(s, "Activity Diagram")
    act_img = placeholder_image(
        ASSET / "activity.png",
        "CrowdPulse Activity Flow",
        [
            "Start -> Authenticate",
            "Select/Upload Video -> Detect People",
            "Track + Zone Map -> Compute Features",
            "Calculate DCRS -> Alert? -> Explain (ERA)",
            "Recommend Actions -> Operator Decision",
            "Log History / Report -> End",
        ],
    )
    fill_empty_content(
        s,
        [
            "Start -> Login -> Ingest Video -> Detect/Track",
            "Zone Analytics -> DCRS -> ERA Alert",
            "Recommend -> Accept/Dismiss -> Log/Report",
        ],
    )
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s.shapes):
        s.shapes.add_picture(str(act_img), Inches(1.2), Inches(1.6), width=Inches(7.8))
    else:
        replace_pictures(s, act_img)

    # ── 16 Deployment ──
    s = slides[15]
    set_title(s, "Deployment Diagram")
    dep_img = placeholder_image(
        ASSET / "deploy.png",
        "CrowdPulse Deployment (Level A)",
        [
            "Client Browser (Next.js UI) :3000",
            "App Server (FastAPI/Uvicorn) :8001",
            "AI Modules on same host (YOLO/HOG/GB)",
            "SQLite DB file / Postgres-ready",
            "Sample/Upload video storage folder",
            "Runs on standard laptop (CPU OK)",
        ],
    )
    fill_empty_content(
        s,
        [
            "Browser -> Next.js Frontend",
            "Frontend -> FastAPI Backend (JWT)",
            "Backend -> AI modules + SQLite + video files",
        ],
    )
    if not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s.shapes):
        s.shapes.add_picture(str(dep_img), Inches(1.2), Inches(1.6), width=Inches(7.8))
    else:
        replace_pictures(s, dep_img)

    # ── 17 Implementation module 1 ──
    s = slides[16]
    set_title(s, "Implementation – Module Description")
    set_shape_lines(
        find_content(s),
        [
            "Helps officers monitor venue zones through a centralized digital-twin platform.",
            "Supports CCTV/sample video processing for detection, tracking, and zone analytics.",
            "Predicts crowd risk using DCRS and highlights Green / Yellow / Orange / Red bands.",
            "Explains every alert using ERA feature contributions for faster understanding.",
            "Recommends control-room actions with Gradient Boosting and a safety filter.",
            "Logs decisions and reports for accountability and after-action review.",
        ],
    )

    # ── 18 Implementation module 2 ──
    s = slides[17]
    set_title(s, "Implementation – Module Description")
    set_shape_lines(
        find_content(s),
        [
            "Perception & Risk Modules",
            "Accepts CCTV clips and sample sparse/medium/dense videos.",
            "Detects people using YOLOv8 (OpenCV HOG fallback) and tracks movement.",
            "Maps detections to zones and computes density, speed drop, and opposing flow.",
            "DCRS converts multi-factor signals into risk score and alert band.",
            "ERA and GB modules produce explanations and ranked interventions for operators.",
        ],
    )

    # ── 19 Coding 1 ──
    s = slides[18]
    set_title(s, "Coding")
    set_shape_lines(
        find_content(s),
        [
            "Video Ingest, Detection, and Tracking",
            "The system supports CCTV/sample video processing through Admin pipeline APIs. Frames are sampled and passed to Ultralytics YOLOv8 person detection, with OpenCV HOG as fallback. A centroid-IoU tracker maintains short-term movement estimates needed for flow-speed features without heavy DeepSORT cost.",
            "Zone assignment converts detections into venue-level occupancy and motion metrics used by DCRS.",
        ],
    )
    code1 = placeholder_image(
        ASSET / "code_detect.png",
        "Coding Snapshot - Detection Pipeline",
        ["POST /api/v1/pipeline/run", "detect -> track -> zone metrics", "YOLO person class / HOG fallback"],
        size=(1100, 500),
    )
    replace_pictures(s, code1)

    # ── 20 Coding 2 ──
    s = slides[19]
    set_title(s, "Coding")
    set_shape_lines(
        find_content(s),
        [
            "AI-Based Risk Analysis and Action Recommendation",
            "CrowdPulse includes an intelligence layer that evaluates each zone using density, speed drop, opposing flow, exit pressure, and related factors. DCRS produces a 0-100 score and risk band. ERA attaches top contributing factors as explanation text.",
            "Gradient Boosting ranks recommended actions; unsafe options are blocked by deterministic safety constraints before showing them to officers.",
        ],
    )
    code2 = placeholder_image(
        ASSET / "code_risk.png",
        "Coding Snapshot - DCRS + GB",
        ["DCRS = sigmoid(weighted features)", "ERA top-k contributions", "GB multi-label actions + safety filter"],
        size=(1100, 500),
    )
    replace_pictures(s, code2)

    # ── 21 Coding 3 ──
    s = slides[20]
    set_title(s, "Coding")
    set_shape_lines(
        find_content(s),
        [
            "Dashboard Analytics and Control-Room Tracking",
            "The dashboard module gives officers a complete operational overview by showing zone risk colors, live alerts, recommended actions, what-if outcomes, and incident reports. JWT roles separate Operator monitoring from Admin ingest.",
            "Historical logging stores alerts and decisions for accountability and viva demonstration of the closed decision loop.",
        ],
    )
    code3 = placeholder_image(
        ASSET / "code_dash.png",
        "Coding Snapshot - Ops Dashboard",
        ["Next.js digital twin", "Alert queue + Accept/Dismiss", "What-if + incident report panels"],
        size=(1100, 500),
    )
    replace_pictures(s, code3)

    # ── 22-27 Outcomes ──
    outcome_captions = [
        ("Login / Auth Screen", ["JWT control-room login", "Operator and Admin roles"]),
        ("Digital Twin Dashboard", ["Zone map colored by DCRS", "Live metrics and alerts"]),
        ("Risk + ERA Explanation", ["Why risk is high", "Feature contributions shown"]),
        ("Decision Recommendations", ["Gradient Boosting actions", "Accept / Dismiss logging"]),
        ("What-If Simulation", ["Close exit / weather / VIP", "Re-scored twin risk"]),
        ("Incident Report Outcome", ["Timeline + risk summary", "After-action review output"]),
    ]
    for idx, (title, lines) in enumerate(outcome_captions):
        s = slides[21 + idx]
        set_title(s, "Outcome")
        img = placeholder_image(ASSET / f"outcome_{idx+1}.png", f"Outcome - {title}", lines, size=(1280, 720))
        if any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in s.shapes):
            replace_pictures(s, img)
        else:
            s.shapes.add_picture(str(img), Inches(0.9), Inches(1.4), width=Inches(8.2))
        fill_empty_content(s, [title] + lines)

    # ── 28 Conclusion ──
    s = slides[27]
    set_title(s, "Conclusion")
    set_shape_lines(
        find_content(s),
        [
            "CrowdPulse - An Intelligent Crowd Analytics and Decision Support Platform is developed as a venue-oriented system for managing crowd risk from CCTV/video efficiently.",
            "It overcomes limitations of traditional counting-only surveillance by combining detection, DCRS early warning, ERA explanations, and Gradient Boosting recommendations.",
            "The modular FastAPI + Next.js architecture with JWT roles and historical logging supports practical control-room demonstration and future scale-up.",
            "Overall, CrowdPulse improves proactive decision-making and strengthens public-safety preparedness for large gatherings.",
        ],
    )

    # ── 29 Future ──
    s = slides[28]
    set_title(s, "Future Course of Action")
    set_shape_lines(
        find_content(s),
        [
            "Multi-Camera Fusion: De-duplicated counting across overlapping live cameras.",
            "Advanced Forecasting: Longer-horizon risk prediction on zone graphs.",
            "Live RTSP Integration: Direct streaming from venue CCTV networks.",
            "Mobile Alert Client: Push critical alerts to on-ground officers.",
            "Postgres/Timescale Scale-Out: Production metrics storage for city-scale pilots.",
            "Richer GenAI Reports: Automated after-action PDF narratives with charts.",
        ],
    )

    # ── 30 References ──
    s = slides[29]
    set_title(s, "References")
    set_shape_lines(
        find_content(s),
        [
            "1. J. Redmon et al., You Only Look Once: Unified, Real-Time Object Detection, IEEE CVPR, 2016.",
            "2. N. Wojke, A. Bewley, and D. Paulus, Simple Online and Realtime Tracking with a Deep Association Metric, IEEE ICIP, 2017.",
            "3. Y. Li, X. Zhang, and D. Chen, CSRNet: Dilated Convolutional Neural Networks for Understanding Highly Congested Scenes, IEEE CVPR, 2018.",
            "4. K. Khan et al., Crowd Monitoring and Localization Frameworks: A Review, Sensors (MDPI), 2020.",
            "5. E. T. Endalamaw, Dense Crowd Activity Detection using YOLOv8 and DeepSORT, IET Image Processing, 2025.",
            "6. Ultralytics YOLOv8 Documentation. [Online]. Available: https://docs.ultralytics.com",
            "7. scikit-learn GradientBoostingClassifier Documentation. [Online]. Available: https://scikit-learn.org",
        ],
    )

    # ── 31 Thank you ──
    s = slides[30]
    for sh in s.shapes:
        if sh.has_text_frame and "THANK" in (sh.text or "").upper():
            set_shape_lines(sh, ["THANK YOU"])
            break

    prs.save(str(OUT))
    try:
        shutil.copy2(OUT, OUT_DESK)
    except Exception as exc:
        print("desktop copy skipped:", exc)
    print("Saved:", OUT)
    print("Slides:", len(list(Presentation(str(OUT)).slides)))
    return OUT


if __name__ == "__main__":
    build()

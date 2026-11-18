"""Draw CrowdPulse architecture diagram (SOCIOCONNECT-style)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"c:\MAJORPROJECT\docs\assets\CrowdPulse_Architecture_Diagram.png")
OUT_DL = Path(r"c:\Users\akshi\Downloads\CrowdPulse_Architecture_Diagram.png")

W, H = 1400, 980
BG = (255, 255, 255)
BLUE = (52, 103, 178)
LIGHT_BLUE = (210, 228, 245)
GREEN = (198, 224, 180)
YELLOW = (255, 242, 204)
PURPLE = (216, 210, 231)
RED = (220, 80, 80)
TEXT = (20, 20, 20)
SUB = (50, 50, 50)
ARROW = (80, 80, 80)


def load_font(size: int, bold: bool = False):
    names = ["arialbd.ttf", "Arial Bold.ttf", "arial.ttf"] if bold else ["arial.ttf", "Arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def center_text(draw, box, text, font, fill=TEXT, line_gap=4):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    heights = []
    widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + line_gap * (len(lines) - 1)
    cy = y1 + (y2 - y1 - total_h) // 2
    for i, line in enumerate(lines):
        tw = widths[i]
        tx = x1 + (x2 - x1 - tw) // 2
        draw.text((tx, cy), line, font=font, fill=fill)
        cy += heights[i] + line_gap


def draw_box(draw, box, fill, outline=BLUE, width=2, radius=8):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow_down(draw, x, y1, y2):
    draw.line((x, y1, x, y2 - 12), fill=ARROW, width=3)
    draw.polygon([(x, y2), (x - 8, y2 - 14), (x + 8, y2 - 14)], fill=ARROW)


def arrow_right(draw, x1, y, x2):
    draw.line((x1, y, x2 - 12, y), fill=ARROW, width=3)
    draw.polygon([(x2, y), (x2 - 14, y - 8), (x2 - 14, y + 8)], fill=ARROW)


def cylinder(draw, cx, top, width, height, fill=(255, 220, 220), outline=RED):
    rx = width // 2
    ell_h = 24
    left, right = cx - rx, cx + rx
    bottom = top + height
    draw.ellipse((left, top, right, top + ell_h * 2), fill=fill, outline=outline, width=2)
    draw.rectangle((left, top + ell_h, right, bottom - ell_h), fill=fill, outline=outline, width=0)
    draw.ellipse((left, bottom - ell_h * 2, right, bottom), fill=fill, outline=outline, width=2)
    draw.arc((left, top, right, top + ell_h * 2), 180, 360, fill=outline, width=2)
    draw.line((left, top + ell_h, left, bottom - ell_h), fill=outline, width=2)
    draw.line((right, top + ell_h, right, bottom - ell_h), fill=outline, width=2)


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_title = load_font(28, bold=True)
    f_sub = load_font(16, bold=True)
    f_body = load_font(13)
    f_small = load_font(12)
    f_flow = load_font(14, bold=True)

    # Title
    draw_box(draw, (120, 20, W - 120, 90), LIGHT_BLUE, BLUE, 3)
    center_text(draw, (120, 20, W - 120, 90), "CROWDPULSE\nAn Intelligent Crowd Analytics and Decision Support Platform", f_title)

    # Frontend
    draw_box(draw, (120, 110, W - 120, 175), GREEN, (70, 120, 70), 2)
    center_text(
        draw,
        (130, 110, W - 130, 175),
        "Next.js / React / TypeScript Frontend\nDigital Twin | Risk Alerts | Decisions | What-If | Reports",
        f_sub,
    )
    arrow_down(draw, W // 2, 175, 205)

    # Backend
    draw_box(draw, (120, 205, W - 120, 265), YELLOW, (180, 150, 60), 2)
    center_text(
        draw,
        (130, 205, W - 130, 265),
        "FastAPI Backend — RESTful API Server (Python, Uvicorn, Pydantic)",
        f_sub,
    )
    arrow_down(draw, W // 2, 265, 295)

    # Four modules
    mod_y1, mod_y2 = 295, 455
    mods = [
        (
            40,
            390,
            "Authentication",
            "• JWT + bcrypt\n• Operator / Admin RBAC\n• Secure API access",
        ),
        (
            370,
            720,
            "Perception Module",
            "• YOLOv8 / HOG detection\n• Centroid-IoU tracking\n• Zone analytics",
        ),
        (
            730,
            1080,
            "Risk & Explainability",
            "• DCRS risk engine\n• ERA feature attribution\n• G/Y/O/R risk bands",
        ),
        (
            1090,
            1360,
            "Decision Support",
            "• Gradient Boosting actions\n• Safety constraint filter\n• What-if simulation",
        ),
    ]
    for x1, x2, title, body in mods:
        draw_box(draw, (x1, mod_y1, x2, mod_y2), LIGHT_BLUE, BLUE, 2)
        draw.text((x1 + 12, mod_y1 + 10), title, font=f_sub, fill=BLUE)
        draw.multiline_text((x1 + 12, mod_y1 + 42), body, font=f_body, fill=SUB, spacing=6)
        arrow_down(draw, (x1 + x2) // 2, mod_y2, 500)

    # Video ingest side flow
    draw_box(draw, (40, 500, 300, 640), YELLOW, (180, 150, 60), 2)
    center_text(
        draw,
        (50, 505, 290, 635),
        "Video Ingest Flow\nUpload CCTV / Sample MP4\nAdmin Pipeline Processing\nAnnotated Output",
        f_small,
    )
    arrow_right(draw, 300, 570, 560)

    # Database cylinder
    cx, top = 700, 500
    cylinder(draw, cx, top, 300, 150, fill=(255, 225, 225), outline=RED)
    center_text(
        draw,
        (550, 530, 850, 640),
        "SQLite Database\nVenues | Zones | Cameras\nAlerts | Decisions | Videos",
        f_sub,
        fill=TEXT,
    )

    # Twin store
    draw_box(draw, (880, 500, 1180, 640), YELLOW, (180, 150, 60), 2)
    center_text(
        draw,
        (890, 505, 1170, 635),
        "Digital Twin Store\nLive zone metrics\nAlert state\nRecommended actions",
        f_small,
    )
    arrow_right(draw, 850, 570, 880)

    # Bottom services
    services = [
        (120, 690, 430, 770, PURPLE, "Sample / Upload Video Storage\n(sparse | medium | dense clips)"),
        (470, 690, 780, 770, PURPLE, "Gradient Boosting Model\n(gb_action_recommender.joblib)"),
        (820, 690, 1130, 770, PURPLE, "Optional Ollama LLM\nAfter-action incident reports"),
    ]
    for x1, y1, x2, y2, color, text in services:
        draw_box(draw, (x1, y1, x2, y2), color, (120, 90, 160), 2)
        center_text(draw, (x1 + 8, y1 + 8, x2 - 8, y2 - 8), text, f_small)

    arrow_down(draw, W // 2, 770, 810)

    # Pipeline flow footer
    draw_box(draw, (80, 810, W - 80, 940), YELLOW, (180, 150, 60), 2)
    flow = (
        "End-to-End Pipeline Flow\n"
        "CCTV / Sample Video  →  Detect (YOLO/HOG)  →  Track  →  Zone Metrics  →  "
        "DCRS  →  ERA Explain  →  GB Recommend  →  Dashboard  →  Accept/Dismiss  →  Report"
    )
    center_text(draw, (90, 815, W - 90, 935), flow, f_flow)

    # Actors note
    draw.text(
        (80, 952),
        "Actors: Control-Room Operator (monitor & decide)  |  Admin (video ingest & pipeline)",
        font=f_small,
        fill=SUB,
    )

    img.save(OUT, quality=95)
    try:
        img.save(OUT_DL, quality=95)
    except OSError:
        pass
    print("Saved:", OUT)
    return OUT


if __name__ == "__main__":
    main()

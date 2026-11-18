"""Generate a single-slide Literature Review table PPT for CrowdPulse."""

from __future__ import annotations

import shutil
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

TEMPLATE = Path(
    r"c:\Users\akshi\Downloads\Stage- I-Major project Internal evaluation-I  PPT template.pptx"
)
OUT = Path(r"c:\MAJORPROJECT\docs\CrowdPulse_Literature_Review_Table.pptx")
OUT_DL = Path(r"c:\Users\akshi\Downloads\CrowdPulse_Literature_Review_Table.pptx")

ROWS = [
    [
        "S.NO",
        "Name of the Authors(s)",
        "Title of the Paper (Published year)",
        "Observations / Findings",
        "Limitations",
    ],
    [
        "1",
        "J. Redmon, S. Divvala, R. Girshick, A. Farhadi",
        "You Only Look Once: Unified, Real-Time Object Detection (IEEE CVPR, 2016)",
        "Real-time person/object detection from full images in one pass",
        "Detection only; no tracking, risk scoring, or decision support",
    ],
    [
        "2",
        "N. Wojke, A. Bewley, D. Paulus",
        "Simple Online and Realtime Tracking with a Deep Association Metric (IEEE ICIP, 2017)",
        "DeepSORT reduces identity switches during occlusions in tracking",
        "Tracking focused; no crowd-risk analysis or operator recommendations",
    ],
    [
        "3",
        "Y. Li, X. Zhang, D. Chen",
        "CSRNet: Dilated CNNs for Understanding Highly Congested Scenes (IEEE CVPR, 2018)",
        "Accurate crowd counting and density-map generation in dense scenes",
        "Counting/density only; no individual motion or action guidance",
    ],
    [
        "4",
        "T. Li, H. Chang, M. Wang, B. Ni, R. Hong, S. Yan",
        "Crowded Scene Analysis: A Survey (IEEE TCSVT, 2015)",
        "Surveys crowd motion, behavior, anomaly detection, and datasets",
        "Survey paper; not an integrated decision-support system",
    ],
    [
        "5",
        "A. M. Al-Shaery, S. Alshehri, N. Farooqi, M. O. Khozium",
        "In-Depth Survey to Detect, Monitor and Manage Crowd (IEEE Access, 2020)",
        "Reviews crowd detection, monitoring, tracking, and management methods",
        "Most methods remain stand-alone; limited closed-loop decision support",
    ],
    [
        "6",
        "X. Li, Q. Yu, B. Alzahrani, A. Barnawi, A. Alhindi, D. Alghazzawi, Y. Miao",
        "Data Fusion for Intelligent Crowd Monitoring and Management Systems: A Survey (IEEE Access, 2021)",
        "Reviews multi-sensor/data-fusion approaches for crowd monitoring systems",
        "Fusion survey; does not provide DCRS, ERA, or action recommendation layer",
    ],
    [
        "7",
        "A. Adege, M. Admas, Y. Tehone, B. Tulu, E. Endalamaw",
        "AI-Powered Human Activity Detection and Tracking in Dense Crowds Using YOLOv8-DeepSORT (IET Image Processing, 2025)",
        "Strong YOLOv8 + DeepSORT detection/tracking in dense crowd environments",
        "Perception/tracking only; no explainable risk scoring or GB recommendations",
    ],
]


def set_run_text(paragraph, text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def fill_table(table, rows: list[list[str]]) -> None:
    tbl = table._tbl
    while len(table.rows) < len(rows):
        tbl.append(deepcopy(tbl.tr_lst[-1]))
    for r_i, row_data in enumerate(rows):
        for c_i, cell_text in enumerate(row_data):
            cell = table.cell(r_i, c_i)
            paras = list(cell.text_frame.paragraphs)
            if paras:
                set_run_text(paras[0], cell_text)
                for p in paras[1:]:
                    set_run_text(p, "")
            else:
                cell.text = cell_text
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9 if r_i else 10)
                    run.font.bold = r_i == 0


def build() -> Path:
    shutil.copy2(TEMPLATE, OUT)
    prs = Presentation(str(OUT))

    # Keep only literature slide (index 4 = slide 5)
    sld_id_lst = prs.slides._sldIdLst
    keep = sld_id_lst[4]
    for sld_id in list(sld_id_lst):
        if sld_id is not keep:
            r_id = sld_id.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            sld_id_lst.remove(sld_id)
            if r_id and r_id in prs.part.rels:
                prs.part.drop_rel(r_id)

    slide = prs.slides[0]

    # Remove hint textbox
    for sh in list(slide.shapes):
        if sh.has_text_frame and "**" in (sh.text or ""):
            sh._element.getparent().remove(sh._element)

    for sh in slide.shapes:
        if sh.has_table:
            fill_table(sh.table, ROWS)
            break

    prs.save(str(OUT))
    shutil.copy2(OUT, OUT_DL)
    print("Saved:", OUT)
    print("Saved:", OUT_DL)
    return OUT


if __name__ == "__main__":
    build()

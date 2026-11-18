"""Analyze and compare IEEE template vs Crowd docx."""
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_docx_info(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)

    paragraphs = []
    for p in root.iter(f"{W}p"):
        texts = []
        style = None
        fonts = []
        sizes = []
        bold = False
        italic = False
        pPr = p.find(f"{W}pPr")
        if pPr is not None:
            pStyle = pPr.find(f"{W}pStyle")
            if pStyle is not None:
                style = pStyle.get(f"{W}val")
        for r in p.findall(f"{W}r"):
            rPr = r.find(f"{W}rPr")
            if rPr is not None:
                if rPr.find(f"{W}b") is not None:
                    bold = True
                if rPr.find(f"{W}i") is not None:
                    italic = True
                rFonts = rPr.find(f"{W}rFonts")
                if rFonts is not None:
                    for attr in ["ascii", "hAnsi", "cs", "eastAsia"]:
                        v = rFonts.get(f"{W}{attr}")
                        if v:
                            fonts.append(v)
                sz = rPr.find(f"{W}sz")
                if sz is not None:
                    sizes.append(int(sz.get(f"{W}val")) / 2)
            for t in r.findall(f"{W}t"):
                if t.text:
                    texts.append(t.text)
        text = "".join(texts).strip()
        if text or style:
            paragraphs.append(
                {
                    "text": text,
                    "style": style,
                    "fonts": list(set(fonts)),
                    "sizes": list(set(sizes)),
                    "bold": bold,
                    "italic": italic,
                }
            )
    return paragraphs


def word_count(text):
    return len(text.split())


def main():
    template = Path(r"c:\Users\akshi\Downloads\IEEE conference-template-a4.docx")
    crowd = Path(r"c:\Users\akshi\Downloads\Crowd.docx")

    for label, p in [("TEMPLATE", template), ("CROWD", crowd)]:
        print("=" * 80)
        print("FILE:", label, p)
        print("=" * 80)
        paras = extract_docx_info(p)
        style_counts = Counter(para["style"] for para in paras)
        print("Style counts:", dict(style_counts))
        total_words = sum(word_count(para["text"]) for para in paras)
        print(f"Total paragraphs: {len(paras)}, Total words: {total_words}")
        print()
        for i, para in enumerate(paras):
            t = para["text"][:150] + ("..." if len(para["text"]) > 150 else "")
            print(
                f"{i+1:3d} | style={para['style']} | sizes={para['sizes']} | "
                f"fonts={para['fonts']} | bold={para['bold']} | wc={word_count(para['text'])} | {t}"
            )
        print()


if __name__ == "__main__":
    main()

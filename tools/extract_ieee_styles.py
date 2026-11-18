"""Extract IEEE template styles and paragraph specs."""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Both namespace variants seen in IEEE/Crowd docx files
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w2": "http://purl.oclc.org/ooxml/wordprocessingml/main",
}


def wtag(local):
    return f"{{{NS['w']}}}{local}"


def find_all(root, local):
    out = list(root.iter(wtag(local)))
    if not out:
        out = list(root.iter(f"{{{NS['w2']}}}{local}"))
    return out


def read_xml_from_docx(path, inner):
    with zipfile.ZipFile(path) as z:
        return z.read(inner)


def style_map(styles_xml_bytes):
    root = ET.fromstring(styles_xml_bytes)
    styles = {}
    for st in find_all(root, "style"):
        sid = st.get(wtag("styleId")) or st.get(f"{{{NS['w2']}}}styleId")
        name_el = st.find(wtag("name"))
        if name_el is None:
            name_el = st.find(f"{{{NS['w2']}}}name")
        name = name_el.get(wtag("val")) if name_el is not None else sid
        rpr = st.find(wtag("rPr"))
        if rpr is None:
            rpr = st.find(f"{{{NS['w2']}}}rPr")
        ppr = st.find(wtag("pPr"))
        if ppr is None:
            ppr = st.find(f"{{{NS['w2']}}}pPr")
        info = {"id": sid, "name": name}
        if rpr is not None:
            fonts = rpr.find(wtag("rFonts"))
            if fonts is None:
                fonts = rpr.find(f"{{{NS['w2']}}}rFonts")
            if fonts is not None:
                info["font"] = fonts.get(wtag("ascii")) or fonts.get(f"{{{NS['w2']}}}ascii")
            sz = rpr.find(wtag("sz"))
            if sz is None:
                sz = rpr.find(f"{{{NS['w2']}}}sz")
            if sz is not None:
                info["size_half_pt"] = sz.get(wtag("val")) or sz.get(f"{{{NS['w2']}}}val")
            b = rpr.find(wtag("b"))
            if b is None:
                b = rpr.find(f"{{{NS['w2']}}}b")
            info["bold"] = b is not None
            i = rpr.find(wtag("i"))
            if i is None:
                i = rpr.find(f"{{{NS['w2']}}}i")
            info["italic"] = i is not None
        if ppr is not None:
            jc = ppr.find(wtag("jc"))
            if jc is None:
                jc = ppr.find(f"{{{NS['w2']}}}jc")
            if jc is not None:
                info["align"] = jc.get(wtag("val")) or jc.get(f"{{{NS['w2']}}}val")
            ind = ppr.find(wtag("ind"))
            if ind is None:
                ind = ppr.find(f"{{{NS['w2']}}}ind")
            if ind is not None:
                for k in ["firstLine", "left", "hanging"]:
                    v = ind.get(wtag(k)) or ind.get(f"{{{NS['w2']}}}{k}")
                    if v:
                        info[k] = v
        styles[sid] = info
        if name:
            styles[name] = info
    return styles


def extract_paragraphs(document_xml_bytes):
    root = ET.fromstring(document_xml_bytes)
    paras = []
    for p in find_all(root, "p"):
        ppr = p.find(wtag("pPr"))
        if ppr is None:
            ppr = p.find(f"{{{NS['w2']}}}pPr")
        style = None
        if ppr is not None:
            ps = ppr.find(wtag("pStyle"))
            if ps is None:
                ps = ppr.find(f"{{{NS['w2']}}}pStyle")
            if ps is not None:
                style = ps.get(wtag("val")) or ps.get(f"{{{NS['w2']}}}val")
        texts = []
        fonts, sizes = set(), set()
        bold = italic = False
        for r in find_all(p, "r"):
            rpr = r.find(wtag("rPr"))
            if rpr is None:
                rpr = r.find(f"{{{NS['w2']}}}rPr")
            if rpr is not None:
                if rpr.find(wtag("b")) is not None or rpr.find(f"{{{NS['w2']}}}b") is not None:
                    bold = True
                if rpr.find(wtag("i")) is not None or rpr.find(f"{{{NS['w2']}}}i") is not None:
                    italic = True
                rf = rpr.find(wtag("rFonts"))
                if rf is None:
                    rf = rpr.find(f"{{{NS['w2']}}}rFonts")
                if rf is not None:
                    f = rf.get(wtag("ascii")) or rf.get(f"{{{NS['w2']}}}ascii")
                    if f:
                        fonts.add(f)
                sz = rpr.find(wtag("sz"))
                if sz is None:
                    sz = rpr.find(f"{{{NS['w2']}}}sz")
                if sz is not None:
                    val = sz.get(wtag("val")) or sz.get(f"{{{NS['w2']}}}val")
                    if val:
                        sizes.add(float(val) / 2)
            for br in find_all(r, "br"):
                texts.append("\n")
            for t in find_all(r, "t"):
                if t.text:
                    texts.append(t.text)
                if t.tail:
                    texts.append(t.tail)
        text = "".join(texts)
        if text.strip() or style:
            paras.append(
                {
                    "style": style,
                    "text": text,
                    "fonts": sorted(fonts),
                    "sizes": sorted(sizes),
                    "bold": bold,
                    "italic": italic,
                }
            )
    return paras


def main():
    template = Path(r"c:\Users\akshi\Downloads\IEEE conference-template-a4.docx")
    crowd = Path(r"c:\Users\akshi\Downloads\Crowd.docx")

    for label, path in [("TEMPLATE", template), ("CROWD", crowd)]:
        print("=" * 90)
        print(label, path.name)
        styles = style_map(read_xml_from_docx(path, "word/styles.xml"))
        key_styles = [
            "papertitle", "paper title", "Author", "Abstract", "Keywords",
            "BodyText", "Body Text", "Heading1", "Heading 1", "Heading2", "Heading 2",
            "bulletlist", "bullet list", "figurecaption", "figure caption", "references",
        ]
        print("Key style definitions:")
        for ks in key_styles:
            if ks in styles:
                s = styles[ks]
                sz = s.get("size_half_pt")
                pt = float(sz) / 2 if sz else None
                print(
                    f"  {ks:15s} id={s.get('id')} font={s.get('font')} "
                    f"size={pt} bold={s.get('bold')} align={s.get('align')}"
                )
        paras = extract_paragraphs(read_xml_from_docx(path, "word/document.xml"))
        print(f"\nParagraphs: {len(paras)}, words: {sum(len(p['text'].split()) for p in paras)}")
        for i, p in enumerate(paras[:60]):
            t = p["text"].replace("\n", "\\n")[:120]
            print(
                f"{i+1:3d} | {p['style']} | sz={p['sizes']} | b={p['bold']} | "
                f"wc={len(p['text'].split())} | {t}"
            )
        if len(paras) > 60:
            print(f"... +{len(paras)-60} more")
        print()


if __name__ == "__main__":
    main()

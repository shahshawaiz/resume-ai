"""Turn a CV (PDF or plain text) into lines grouped by section."""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .glossary import load_rules

BULLET_RE = re.compile(r"^\s*([-•*–·▪●◦‣]|\d+[.)])\s+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d ()/-]{7,}\d")


@dataclass
class Line:
    index: int
    text: str
    section: str
    is_heading: bool = False
    is_bullet: bool = False
    page: Optional[int] = None


@dataclass
class CV:
    lines: List[Line]
    name: str = ""
    email: str = ""
    phone: str = ""
    pages: int = 0
    sections: Dict[str, List[int]] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines)

    def bullets(self, section: Optional[str] = None) -> List[Line]:
        return [l for l in self.lines if l.is_bullet and (section is None or l.section == section)]


def _heading_lookup() -> Dict[str, str]:
    out = {}
    for section, names in load_rules()["section_headings"].items():
        for n in names:
            out[n] = section
    return out


def classify_heading(text: str, bold_or_large: bool = False) -> Optional[str]:
    """Return the section a heading line opens, or None if it is not a heading."""
    t = text.strip().rstrip(":").strip()
    if not t or len(t) > 40:
        return None
    lookup = _heading_lookup()
    key = re.sub(r"\s+", " ", t.lower())
    if key in lookup:
        return lookup[key]
    # all-caps or emphasised short line that starts with a known heading word
    if t.isupper() or bold_or_large:
        for name, section in lookup.items():
            if key.startswith(name):
                return section
    return None


def parse_text(text: str, page_of_line: Optional[List[int]] = None,
               emphasis: Optional[List[bool]] = None, pages: int = 0) -> CV:
    raw = [l.rstrip() for l in text.replace("\r\n", "\n").split("\n")]
    lines: List[Line] = []
    section = "header"
    sections: Dict[str, List[int]] = {}
    for i, t in enumerate(raw):
        if not t.strip():
            continue
        emph = bool(emphasis[i]) if emphasis and i < len(emphasis) else False
        sec = classify_heading(t, emph)
        idx = len(lines)
        if sec:
            section = sec
            lines.append(Line(idx, t.strip(), section, is_heading=True,
                              page=page_of_line[i] if page_of_line else None))
            continue
        is_bullet = bool(BULLET_RE.match(t))
        if section == "header" and (is_bullet or idx >= 4):
            section = "other"  # header is only the name/contact block at the top
        lines.append(Line(idx, t.strip(), section, is_bullet=is_bullet,
                          page=page_of_line[i] if page_of_line else None))
        sections.setdefault(section, []).append(idx)
    cv = CV(lines=lines, sections=sections, pages=pages)
    header = [l.text for l in lines if l.section == "header"] or [l.text for l in lines[:3]]
    cv.name = header[0] if header else ""
    m = EMAIL_RE.search(cv.text)
    cv.email = m.group(0) if m else ""
    p = PHONE_RE.search("\n".join(header))
    cv.phone = p.group(0).strip() if p else ""
    return cv


def parse_pdf(path_or_bytes) -> CV:
    """Extract lines from a PDF with PyMuPDF, using font size/weight to spot headings."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=path_or_bytes, filetype="pdf") if isinstance(path_or_bytes, (bytes, bytearray)) \
        else fitz.open(path_or_bytes)
    texts: List[str] = []
    page_of: List[int] = []
    emph: List[bool] = []
    sizes: List[float] = []
    rows = []
    for pno, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in line["spans"]).strip()
                size = max(s["size"] for s in spans)
                bold = all(s["flags"] & 16 or "bold" in s["font"].lower() for s in spans)
                rows.append((pno, text, size, bold))
                sizes.append(size)
    body = sorted(sizes)[len(sizes) // 2] if sizes else 0
    for pno, text, size, bold in rows:
        texts.append(text)
        page_of.append(pno)
        emph.append(bold or size > body * 1.15)
    n = len(doc)
    doc.close()
    return parse_text("\n".join(texts), page_of_line=page_of, emphasis=emph, pages=n)

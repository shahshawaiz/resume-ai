"""Export to PDF and DOCX, and write accepted changes back into the original PDF."""
import io
from typing import Dict, List, Tuple

import fitz  # PyMuPDF

A4 = fitz.paper_rect("a4")
MARGIN = 56


def text_to_pdf(text: str) -> bytes:
    """Simple, ATS-friendly single-column PDF: first line as title, CAPS lines bold."""
    doc = fitz.open()
    page = doc.new_page(width=A4.width, height=A4.height)
    y = MARGIN
    width = A4.width - 2 * MARGIN
    for i, raw in enumerate(text.split("\n")):
        line = raw.rstrip()
        heading = i == 0 or (line.isupper() and 3 < len(line) < 40)
        size = 16 if i == 0 else 11.5 if heading else 10.5
        font = "hebo" if heading else "helv"
        lead = size * 1.45
        # wrap by measured width
        words, rows, cur = line.split(" "), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if fitz.get_text_length(trial, fontname=font, fontsize=size) <= width or not cur:
                cur = trial
            else:
                rows.append(cur)
                cur = w
        rows.append(cur)
        for r in rows:
            if y + lead > A4.height - MARGIN:
                page = doc.new_page(width=A4.width, height=A4.height)
                y = MARGIN
            page.insert_text((MARGIN, y + size), r, fontname=font, fontsize=size)
            y += lead
        if heading and i:
            y += 2
    data = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return data


def text_to_docx(text: str) -> bytes:
    from docx import Document
    from docx.shared import Pt

    d = Document()
    d.styles["Normal"].font.name = "Calibri"
    d.styles["Normal"].font.size = Pt(11)
    for i, raw in enumerate(text.split("\n")):
        line = raw.rstrip()
        if i == 0:
            d.add_heading(line, level=0)
        elif line.isupper() and 3 < len(line) < 40:
            d.add_heading(line.title(), level=1)
        elif line.lstrip().startswith(("- ", "• ", "* ")):
            d.add_paragraph(line.lstrip()[2:], style="List Bullet")
        else:
            d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def _span_style(page, rect) -> Tuple[float, Tuple[float, float, float]]:
    """Font size and colour of the first text span inside rect."""
    for block in page.get_text("dict", clip=rect)["blocks"]:
        for line in block.get("lines", []):
            for s in line["spans"]:
                if s["text"].strip():
                    c = s["color"]
                    return s["size"], ((c >> 16 & 255) / 255, (c >> 8 & 255) / 255, (c & 255) / 255)
    return 10.0, (0, 0, 0)


def rewrite_pdf(pdf_bytes: bytes, replacements: Dict[str, str]) -> Tuple[bytes, List[str], List[str]]:
    """Replace whole lines in the original PDF, keeping position, size and colour.

    Each original line is removed with a redaction (which deletes the text,
    not just covers it) and the new text is placed in the same box, shrinking
    the font if needed. Returns (pdf, applied_originals, skipped_originals).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    applied, skipped = [], []
    for original, new in replacements.items():
        done = False
        for page in doc:
            rects = page.search_for(original)
            if not rects:
                continue
            # a long line can come back as several rects; take their union
            box = rects[0]
            for r in rects[1:]:
                if abs(r.y0 - box.y0) < 2 or r.y0 - box.y1 < 2:
                    box |= r
            size, color = _span_style(page, box)
            page.add_redact_annot(box, fill=False)
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            room = fitz.Rect(box.x0, box.y0 - 1, page.rect.width - MARGIN / 2, box.y1 + 1)
            fs = size
            while fs > 6 and fitz.get_text_length(new, "helv", fs) > room.width:
                fs -= 0.25
            page.insert_text((box.x0, box.y1 - (box.height - fs) / 2 - fs * 0.2), new, fontname="helv",
                             fontsize=fs, color=color)
            done = True
            break
        (applied if done else skipped).append(original)
    data = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return data, applied, skipped

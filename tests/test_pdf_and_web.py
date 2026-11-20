import io

import fitz
from docx import Document

from resume_ai.cv_parser import parse_pdf
from resume_ai.export import rewrite_pdf, text_to_docx, text_to_pdf
from resume_ai.web import create_app


def test_parse_pdf_finds_sections(cv_pdf):
    cv = parse_pdf(cv_pdf)
    assert cv.name == "Alex Morgan"
    assert cv.email == "alex.morgan@example.com"
    assert {"summary", "experience", "education", "skills"} <= {l.section for l in cv.lines if l.is_heading}
    assert len(cv.bullets("experience")) == 7


def test_rewrite_pdf_replaces_text_in_place(cv_pdf):
    old = "- Worked on a recommendation system for the online shop"
    new = "- Built a recommendation system for the online shop"
    out, applied, skipped = rewrite_pdf(cv_pdf, {old: new, "not in the pdf": "x"})
    assert applied == [old] and skipped == ["not in the pdf"]
    text = fitz.open(stream=out, filetype="pdf")[0].get_text()
    assert new in text and old not in text
    assert "Alex Morgan" in text  # the rest of the page is untouched


def test_text_exports_roundtrip():
    pdf = text_to_pdf("Alex\nSKILLS\n- Python\n" + "word " * 2000)
    doc = fitz.open(stream=pdf, filetype="pdf")
    assert doc.page_count > 1 and "Python" in doc[0].get_text()
    d = Document(io.BytesIO(text_to_docx("Alex\nSKILLS\n- Python")))
    assert [p.text for p in d.paragraphs] == ["Alex", "Skills", "Python"]


def test_web_flow(cv_pdf, job_text):
    c = create_app().test_client()
    assert c.get("/").status_code == 200
    assert any(g["id"] == "finance" for g in c.get("/api/industries").get_json())
    r = c.post("/api/analyze", data={"job_text": job_text, "cv_file": (io.BytesIO(cv_pdf), "cv.pdf")},
               content_type="multipart/form-data")
    assert r.status_code == 200
    data = r.get_json()
    assert data["upload_id"] and data["match"]["industry"] == "data" and data["suggestions"]
    s = data["suggestions"][0]
    e = c.post("/api/export", json={"kind": "cv", "format": "pdf-original", "upload_id": data["upload_id"],
                                    "replacements": {s["original"]: s["improved"]}})
    assert e.status_code == 200 and e.headers["X-Applied"] == "1"
    assert c.post("/api/export", json={"kind": "letter", "format": "docx", "text": "Hi"}).status_code == 200


def test_web_rejects_bad_input(job_text):
    c = create_app().test_client()
    assert c.post("/api/analyze", data={"job_text": job_text}).status_code == 400
    r = c.post("/api/analyze", data={"job_text": job_text, "cv_file": (io.BytesIO(b"hello"), "x.pdf")},
               content_type="multipart/form-data")
    assert r.status_code == 400

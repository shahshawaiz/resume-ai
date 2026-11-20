"""Local web UI. Runs on 127.0.0.1 only; nothing leaves the machine."""
import io
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from .analysis import analyze
from .cv_parser import parse_pdf, parse_text
from .export import rewrite_pdf, text_to_docx, text_to_pdf
from .glossary import load_glossaries

STATIC = Path(__file__).parent / "static"
MAX_UPLOAD = 10 * 1024 * 1024


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD
    pdfs = {}  # upload id -> original PDF bytes, kept in memory for this process only

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/static/<path:name>")
    def static_file(name):
        return send_from_directory(STATIC, name)

    @app.get("/api/sample")
    def sample():
        d = Path(__file__).parent.parent / "samples"
        return jsonify(cv=(d / "cv_data_scientist.txt").read_text(encoding="utf-8"),
                       job=(d / "job_ml_engineer.txt").read_text(encoding="utf-8"))

    @app.get("/api/industries")
    def industries():
        return jsonify([{"id": g.industry, "label": g.label, "terms": len(g.terms)}
                        for g in load_glossaries().values()])

    @app.post("/api/analyze")
    def api_analyze():
        job_text = (request.form.get("job_text") or "").strip()
        industry = request.form.get("industry") or "auto"
        lang = request.form.get("lang") or "en"
        upload_id = None
        f = request.files.get("cv_file")
        if f and f.filename:
            data = f.read()
            if not data.startswith(b"%PDF"):
                return jsonify(error="The file is not a PDF."), 400
            cv = parse_pdf(data)
            upload_id = uuid.uuid4().hex
            pdfs[upload_id] = data
        else:
            cv_text = (request.form.get("cv_text") or "").strip()
            if not cv_text:
                return jsonify(error="Add a CV (PDF or text)."), 400
            cv = parse_text(cv_text)
        if not job_text:
            return jsonify(error="Paste a job ad."), 400
        if not cv.lines:
            return jsonify(error="No text found in the CV. Scanned PDFs are not supported."), 400
        result = analyze(cv, job_text, industry, lang)
        result["upload_id"] = upload_id
        return jsonify(result)

    @app.post("/api/export")
    def api_export():
        body = request.get_json(force=True)
        kind, fmt = body.get("kind"), body.get("format")
        text = body.get("text") or ""
        name = "CV-tailored" if kind == "cv" else "Cover-letter"
        if fmt == "docx":
            return send_file(io.BytesIO(text_to_docx(text)), as_attachment=True, download_name=name + ".docx",
                             mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if fmt == "pdf-original":
            original = pdfs.get(body.get("upload_id") or "")
            if not original:
                return jsonify(error="Original PDF not available. Upload it again."), 400
            data, applied, skipped = rewrite_pdf(original, body.get("replacements") or {})
            resp = send_file(io.BytesIO(data), as_attachment=True, download_name=name + ".pdf",
                             mimetype="application/pdf")
            resp.headers["X-Applied"] = str(len(applied))
            resp.headers["X-Skipped"] = str(len(skipped))
            return resp
        return send_file(io.BytesIO(text_to_pdf(text)), as_attachment=True, download_name=name + ".pdf",
                         mimetype="application/pdf")

    return app

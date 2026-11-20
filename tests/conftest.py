from pathlib import Path

import fitz
import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


@pytest.fixture
def cv_text():
    return (SAMPLES / "cv_data_scientist.txt").read_text(encoding="utf-8")


@pytest.fixture
def job_text():
    return (SAMPLES / "job_ml_engineer.txt").read_text(encoding="utf-8")


@pytest.fixture
def cv_pdf(cv_text):
    """Render the sample CV into a PDF with bold headings, like a real CV."""
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for i, line in enumerate(cv_text.split("\n")):
        if not line.strip():
            y += 8
            continue
        heading = line.isupper()
        page.insert_text((50, y), line, fontname="hebo" if heading or i == 0 else "helv",
                         fontsize=16 if i == 0 else 12 if heading else 10)
        y += 15
    data = doc.tobytes()
    doc.close()
    return data

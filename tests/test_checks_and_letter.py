from resume_ai.analysis import analyze
from resume_ai.checks import run_checks
from resume_ai.cv_parser import parse_text
from resume_ai.job_parser import parse_job


def _ids(checks):
    return {c.id: c for c in checks}


def test_sample_checks(cv_text, job_text):
    c = _ids(run_checks(parse_text(cv_text), parse_job(job_text)))
    assert c["email"].level == "ok"
    assert c["numbers"].level == "warning"
    assert c["years"].level == "ok"
    assert "section-experience" not in c


def test_missing_sections_and_mixed_dates():
    cv = parse_text("Sam\n- I did stuff 01/2020\n- More stuff Jan 2021")
    c = _ids(run_checks(cv))
    assert c["email"].level == "error"
    assert {"section-experience", "section-education", "section-skills", "dates", "first-person"} <= set(c)


def test_cover_letter_uses_only_cv_lines(cv_text, job_text):
    r = analyze(parse_text(cv_text), job_text)
    letter = r["cover_letter"]
    assert letter.startswith("Dear Hiring Team at Nordlicht Health GmbH,")
    assert "Machine Learning Engineer" in letter and letter.rstrip().endswith("Alex Morgan")
    assert "Kubernetes" not in letter  # a missing skill is never claimed


def test_german_letter(cv_text, job_text):
    letter = analyze(parse_text(cv_text), job_text, lang="de")["cover_letter"]
    assert letter.startswith("Sehr geehrtes Recruiting-Team der Nordlicht Health GmbH,")
    assert "Mit freundlichen Grüßen" in letter

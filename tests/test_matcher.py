from resume_ai.cv_parser import parse_text
from resume_ai.job_parser import parse_job
from resume_ai.matcher import match


def _terms(r):
    return {t.term: t for t in r.terms}


def test_weighted_score(cv_text, job_text):
    r = match(parse_text(cv_text), parse_job(job_text))
    t = _terms(r)
    assert r.industry == "data"
    assert t["scikit-learn"].found and t["scikit-learn"].importance == "required"
    assert not t["Kubernetes"].found and t["Kubernetes"].importance == "required"
    assert t["Airflow"].importance == "preferred"
    assert t["Google Cloud"].importance in ("required", "other")
    assert 0 < r.score < 100


def test_required_counts_more_than_preferred():
    job = parse_job("Role - Co\n\nRequirements\n- Python\n\nNice to have\n- Spark\n")
    only_req = match(parse_text("Skills\nPython"), job, "data")
    only_pref = match(parse_text("Skills\nSpark"), job, "data")
    assert only_req.score == 75 and only_pref.score == 25


def test_alias_in_cv_counts_as_hit():
    job = parse_job("Engineer - Co\n\nRequirements\n- Kubernetes and scikit-learn\n")
    r = match(parse_text("Experience\n- Deployed sklearn models on k8s"), job, "data")
    assert r.score == 100
    assert _terms(r)["Kubernetes"].cv_forms == ["k8s"]


def test_industry_override(cv_text, job_text):
    r = match(parse_text(cv_text), parse_job(job_text), "software")
    assert r.industry == "software"

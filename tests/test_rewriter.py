from resume_ai.cv_parser import parse_text
from resume_ai.glossary import load_rules
from resume_ai.job_parser import parse_job
from resume_ai.matcher import match
from resume_ai.rewriter import apply, strengthen_opener, suggest


def test_weak_openers():
    rules = load_rules()
    assert strengthen_opener("Worked on a recommendation system", rules) == ("Built a recommendation system", True)
    assert strengthen_opener("Responsible for managing 4 people", rules) == ("Managed 4 people", True)
    assert strengthen_opener("Responsible for the data platform", rules) == ("Owned the data platform", True)
    assert strengthen_opener("Built a thing", rules) == ("Built a thing", False)


def test_job_terminology_swap_only_for_existing_skill():
    cv = parse_text("Jane Doe\n\nEXPERIENCE\n- Deployed sklearn models on k8s\n- Wrote reports")
    job = parse_job("ML Engineer - Co\n\nRequirements\n- Kubernetes, scikit-learn, PyTorch\n")
    s = suggest(cv, match(cv, job, "data"))
    assert len(s) == 1
    assert s[0].improved == "- Deployed scikit-learn models on Kubernetes"
    # never adds a skill the CV does not show
    assert "PyTorch" not in apply(cv, s)


def test_no_swap_when_keyword_already_present(cv_text, job_text):
    cv = parse_text(cv_text)
    s = suggest(cv, match(cv, parse_job(job_text)))
    improved = {x.original: x.improved for x in s}
    assert "- Built demand forecasting models in Python that improved stock planning" not in improved
    assert improved["- Worked on a recommendation system for the online shop"] == "- Built a recommendation system for the online shop"
    assert improved["- Helped with an A/B testing framework"] == "- Supported an A/B testing framework"


def test_headers_and_education_untouched(cv_text, job_text):
    cv = parse_text(cv_text)
    lines = {x.line for x in suggest(cv, match(cv, parse_job(job_text)))}
    for l in cv.lines:
        if l.section in ("header", "education") or l.is_heading:
            assert l.index not in lines


def test_apply_respects_accepted(cv_text, job_text):
    cv = parse_text(cv_text)
    s = suggest(cv, match(cv, parse_job(job_text)))
    assert apply(cv, s, accepted=set()).replace("\n\n", "\n") == cv.text

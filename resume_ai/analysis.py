"""One call that runs the whole pipeline: parse, match, suggest, check, letter."""
from typing import Optional

from .checks import run_checks
from .cover_letter import write_letter
from .cv_parser import CV
from .job_parser import parse_job
from .matcher import match
from .rewriter import apply, suggest


def analyze(cv: CV, job_text: str, industry: Optional[str] = None, lang: str = "en") -> dict:
    job = parse_job(job_text)
    m = match(cv, job, industry)
    sugg = suggest(cv, m)
    tailored = apply(cv, sugg)
    tailored_lines = {s.line: s.improved for s in sugg}
    letter = write_letter(cv, job, m, [tailored_lines.get(l.index, l.text) for l in cv.lines], lang=lang)
    return {
        "candidate": {"name": cv.name, "email": cv.email, "phone": cv.phone, "pages": cv.pages},
        "job": {"role": job.role, "company": job.company, "min_years": job.min_years},
        "match": m.as_dict(),
        "cv_lines": [{"index": l.index, "text": l.text, "section": l.section,
                      "heading": l.is_heading, "bullet": l.is_bullet} for l in cv.lines],
        "suggestions": [s.as_dict() for s in sugg],
        "checks": [c.as_dict() for c in run_checks(cv, job)],
        "tailored_cv": tailored,
        "cover_letter": letter,
    }

"""ATS-style and quality checks on a parsed CV. Each check is a small rule."""
import re
from dataclasses import dataclass
from typing import List, Optional

from .cv_parser import CV
from .glossary import load_rules
from .job_parser import JobAd

DATE_FORMATS = [
    ("MM/YYYY", re.compile(r"\b(0?[1-9]|1[0-2])/(19|20)\d{2}\b")),
    ("MM.YYYY", re.compile(r"\b(0?[1-9]|1[0-2])\.(19|20)\d{2}\b")),
    ("Mon YYYY", re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.? (19|20)\d{2}\b")),
]
FIRST_PERSON = re.compile(r"\b(I|me|my|I'm|I've)\b")


@dataclass
class Check:
    id: str
    level: str        # "error" | "warning" | "info" | "ok"
    message: str
    lines: Optional[List[int]] = None

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def run_checks(cv: CV, job: Optional[JobAd] = None) -> List[Check]:
    rules = load_rules()
    verbs = set(rules["action_verbs"])
    out: List[Check] = []
    present = {l.section for l in cv.lines if l.is_heading}

    # 1. Contact details an ATS needs to create a candidate record
    out.append(Check("email", "ok", "Email address found.") if cv.email
               else Check("email", "error", "No email address found. ATS systems need one to contact you."))
    if not cv.phone:
        out.append(Check("phone", "info", "No phone number found in the header."))

    # 2. Standard section headings, which ATS parsers rely on
    for sec in ("experience", "education", "skills"):
        if sec not in present:
            out.append(Check("section-" + sec, "warning",
                             "No '%s' heading found. Use a standard heading so ATS parsers file it correctly." % sec.capitalize()))

    # 3. Length
    words = len(cv.text.split())
    if words > 900 or cv.pages > 2:
        out.append(Check("length", "warning", "CV is long (%d words%s). Aim for 1–2 pages." %
                         (words, ", %d pages" % cv.pages if cv.pages else "")))
    elif words < 150:
        out.append(Check("length", "warning", "CV is very short (%d words). Is all text extractable?" % words))

    # 4. One date format throughout
    used = [name for name, pat in DATE_FORMATS if pat.search(cv.text)]
    if len(used) > 1:
        out.append(Check("dates", "warning", "Mixed date formats (%s). Pick one." % ", ".join(used)))

    bullets = cv.bullets()
    exp_bullets = [b for b in bullets if b.section in ("experience", "projects")] or bullets

    # 5. Bullets should start with an action verb
    weak = [b.index for b in exp_bullets
            if re.sub(r"^\W+", "", b.text).split(" ")[0].lower().rstrip(",") not in verbs]
    if weak:
        out.append(Check("action-verbs", "info", "%d bullet(s) do not start with an action verb." % len(weak), weak))

    # 6. Quantified results
    unq = [b.index for b in exp_bullets if not re.search(r"\d", b.text)]
    if exp_bullets and len(unq) > len(exp_bullets) / 2:
        out.append(Check("numbers", "warning",
                         "%d of %d experience bullets have no number. Add results you can back up (%%, €, time saved, users)."
                         % (len(unq), len(exp_bullets)), unq))

    # 7. Overlong bullets
    long_ = [b.index for b in bullets if len(b.text.split()) > 35]
    if long_:
        out.append(Check("long-bullets", "info", "%d bullet(s) are over 35 words." % len(long_), long_))

    # 8. First person
    fp = [l.index for l in cv.lines if l.section != "header" and FIRST_PERSON.search(l.text)]
    if fp:
        out.append(Check("first-person", "info", "CV uses 'I'/'my'. CVs usually leave the pronoun out.", fp))

    # 9. Characters that often break ATS parsing
    odd = [l.index for l in cv.lines if re.search(r"[-▀-▟]", l.text)]
    if odd:
        out.append(Check("symbols", "warning", "Icon-font or block characters found; ATS parsers may drop them.", odd))

    # 10. Years of experience asked for
    if job and job.min_years:
        exp_text = "\n".join(l.text for l in cv.lines if l.section == "experience") or cv.text
        years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", exp_text)]
        if years:
            span = max(years) - min(years)
            if re.search(r"\b(present|now|current|heute)\b", exp_text, re.I):
                import datetime
                span = datetime.date.today().year - min(years)
            level = "ok" if span >= job.min_years else "warning"
            out.append(Check("years", level, "Job asks for %d+ years; your CV dates span about %d years."
                             % (job.min_years, span)))
    return out

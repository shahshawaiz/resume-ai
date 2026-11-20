"""Split a job ad into required, preferred and other lines; guess role and company."""
import re
from dataclasses import dataclass, field
from typing import List

REQUIRED_HEAD = re.compile(
    r"^(requirements|required|qualifications|your profile|profile|who you are|what you (will )?need|what we('re| are) looking for|"
    r"you (have|bring|should have)|must[- ]haves?|skills|dein profil|ihr profil|das bringst du mit|anforderungen)\b", re.I)
PREFERRED_HEAD = re.compile(
    r"^(nice[- ]to[- ]haves?|bonus( points)?|preferred( qualifications)?|(definite )?plus( points)?|good to have|"
    r"it'?s a plus|wünschenswert|von vorteil)\b", re.I)
OTHER_HEAD = re.compile(
    r"^(your tasks|tasks|responsibilities|what you('ll| will) do|what we will do together|the role|about (us|the role)|"
    r"we offer|benefits|what we offer|deine aufgaben|ihre aufgaben|wir bieten)\b", re.I)
PREFERRED_INLINE = re.compile(r"\b(is a plus|are a plus|a plus|nice to have|preferred|ideally|bonus|advantage|von vorteil|wünschenswert)\b", re.I)
YEARS_RE = re.compile(r"(\d+)\s*\+?\s*(?:-\s*\d+\s*)?(?:years|yrs|jahre)", re.I)
TITLE_SPLIT = re.compile(r"\s+[–—|-]\s+|\s+at\s+|\s+@\s+")
GENDER_TAG = re.compile(r"\s*\((m/w/d|w/m/d|m/f/d|f/m/x|all genders?)\)", re.I)


@dataclass
class JobLine:
    text: str
    kind: str  # "required" | "preferred" | "other"


@dataclass
class JobAd:
    text: str
    role: str = ""
    company: str = ""
    lines: List[JobLine] = field(default_factory=list)
    min_years: int = 0

    def text_of(self, kind: str) -> str:
        return "\n".join(l.text for l in self.lines if l.kind == kind)


def _is_heading(t: str) -> bool:
    return len(t) <= 60 and not t.endswith(".") and not re.match(r"^\s*[-•*]", t)


def parse_job(text: str) -> JobAd:
    raw = [l.strip() for l in text.replace("\r\n", "\n").split("\n")]
    nonempty = [l for l in raw if l]
    job = JobAd(text=text)
    kind = "other"
    for t in nonempty:
        stripped = re.sub(r"^[-•*]\s*", "", t)
        if _is_heading(t):
            if PREFERRED_HEAD.match(stripped):
                kind = "preferred"
                continue
            if REQUIRED_HEAD.match(stripped):
                kind = "required"
                continue
            if OTHER_HEAD.match(stripped):
                kind = "other"
                continue
        line_kind = kind
        if kind == "required" and PREFERRED_INLINE.search(t):
            # "Docker and Kubernetes; Airflow is a plus": keep it required, the
            # matcher splits the clause after the separator.
            line_kind = "mixed"
        job.lines.append(JobLine(t, line_kind))
    years = [int(m.group(1)) for m in YEARS_RE.finditer(job.text_of("required") or text)]
    job.min_years = max(years) if years else 0

    if nonempty:
        first = GENDER_TAG.sub("", nonempty[0])
        parts = TITLE_SPLIT.split(first, maxsplit=1)
        if len(parts) == 2 and len(first) < 120:
            job.role = parts[0].strip()
            job.company = parts[1].split(",")[0].strip()
        elif len(first) < 80:
            job.role = first.strip()
    if not job.role:
        m = re.search(r"looking for an? (?:highly motivated and detail oriented |talented |experienced )?([A-Z][\w /&-]{2,50}?) to\b", text)
        if m:
            job.role = m.group(1).strip()
    if not job.company:
        m = re.search(r"\b([A-Z][\w&.]*(?: [A-Z][\w&.]*){0,3}) (?:is looking|is hiring|are looking|is a )", text)
        if m:
            job.company = m.group(1).strip()
    return job


def split_preferred_clause(line: str):
    """Split a mixed line into (required_part, preferred_part)."""
    req, pref = [], []
    # "(GCP preferred)" -> the parenthetical is preferred, the rest is not
    for m in re.finditer(r"\(([^)]*)\)", line):
        if PREFERRED_INLINE.search(m.group(1)):
            pref.append(m.group(1))
    line = re.sub(r"\(([^)]*)\)", lambda m: "" if PREFERRED_INLINE.search(m.group(1)) else m.group(0), line)
    parts = re.split(r"[;,]", line)
    for p in parts:
        (pref if PREFERRED_INLINE.search(p) else req).append(p)
    return " ".join(req), " ".join(pref)

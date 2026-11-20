"""Cover letter from a fixed template, filled with matched skills and CV lines.

The letter only quotes the candidate's own CV lines as evidence, so it never
claims anything the CV does not say. It is a starting draft to edit.
"""
import re
from typing import List

from .cv_parser import BULLET_RE, CV
from .job_parser import JobAd
from .matcher import MatchResult

TEMPLATES = {
    "en": {
        "greeting": "Dear Hiring Team{at_company},",
        "intro": "I am applying for the {role} position{at_company_short}. {skills_sentence}",
        "skills": "My experience covers several of the points in your job ad, in particular {skills}.",
        "evidence": "A few examples from my work:",
        "closing": "I would welcome the chance to discuss how I can contribute{to_company}. Thank you for your time and consideration.",
        "signoff": "Kind regards,",
        "and": "and",
        "role_fallback": "advertised",
    },
    "de": {
        "greeting": "Sehr geehrtes Recruiting-Team{at_company},",
        "intro": "hiermit bewerbe ich mich auf die Position {role}{at_company_short}. {skills_sentence}",
        "skills": "Meine Erfahrung deckt mehrere Punkte Ihrer Ausschreibung ab, insbesondere {skills}.",
        "evidence": "Einige Beispiele aus meiner Arbeit:",
        "closing": "Ich freue mich darauf, in einem persönlichen Gespräch zu zeigen, wie ich{to_company} beitragen kann.",
        "signoff": "Mit freundlichen Grüßen",
        "and": "und",
        "role_fallback": "ausgeschriebene Stelle",
    },
}


def _join(items: List[str], word: str) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " " + word + " " + items[-1]


def _clean_bullet(text: str) -> str:
    t = BULLET_RE.sub("", text).strip().rstrip(".")
    return t + "."


def write_letter(cv: CV, job: JobAd, match: MatchResult, cv_text_lines: List[str] = None,
                 lang: str = "en", max_skills: int = 4, max_examples: int = 3) -> str:
    T = TEMPLATES.get(lang, TEMPLATES["en"])
    lines = cv_text_lines or [l.text for l in cv.lines]
    hits = [t for t in match.hits() if t.category not in ("language", "education")]
    # required skills first; within that, skills with more evidence first
    order = {"required": 0, "other": 1, "preferred": 2}
    hits.sort(key=lambda t: (order[t.importance], -len(t.evidence)))
    skills = [t.job_form for t in hits[:max_skills]]

    examples, used = [], set()
    for t in hits:
        for i in t.evidence:
            l = cv.lines[i]
            if i in used or not (l.is_bullet or l.section in ("experience", "projects")):
                continue
            used.add(i)
            examples.append(_clean_bullet(lines[i] if i < len(lines) else l.text))
            break
        if len(examples) >= max_examples:
            break

    company = job.company
    role = job.role or T["role_fallback"]
    out = [
        T["greeting"].format(at_company=(" at " if lang == "en" else " der ") + company if company else ""),
        "",
        T["intro"].format(role=role, at_company_short=(" at " + company if lang == "en" else " bei " + company) if company else "",
                          skills_sentence=T["skills"].format(skills=_join(skills, T["and"])) if skills else "").strip(),
    ]
    if examples:
        out += ["", T["evidence"]] + ["• " + e for e in examples]
    out += ["", T["closing"].format(to_company=(" to " + company if lang == "en" else " zu " + company) if company else ""),
            "", T["signoff"], cv.name]
    text = "\n".join(out)
    return re.sub(r"[ \t]{2,}", " ", text)

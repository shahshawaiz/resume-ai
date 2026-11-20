"""Rule-based CV line suggestions.

Every rule only rephrases what is already on the CV. No rule adds a skill,
employer, number or claim the CV does not already contain.
"""
import re
from dataclasses import dataclass
from typing import List

from .cv_parser import BULLET_RE, CV
from .glossary import load_rules
from .matcher import MatchResult


@dataclass
class Suggestion:
    line: int
    original: str
    improved: str
    rules: List[str]
    reason: str

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def _split_bullet(text: str):
    m = BULLET_RE.match(text)
    return (text[:m.end()], text[m.end():]) if m else ("", text)


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def strengthen_opener(body: str, rules: dict):
    """'Worked on a recommender' -> 'Built a recommender'. Returns (new_body, changed)."""
    low = body.lower()
    for phrase in sorted(rules["weak_openers"], key=len, reverse=True):
        if low.startswith(phrase + " ") or low == phrase:
            rest = body[len(phrase):].lstrip()
            # "Responsible for managing X" -> "Managed X"
            for ger in sorted(rules["gerunds"], key=len, reverse=True):
                if rest.lower().startswith(ger + " "):
                    return rules["gerunds"][ger] + rest[len(ger):], True
            return rules["weak_openers"][phrase] + (" " + rest if rest else ""), True
    return body, False


def trim_wordy(body: str, rules: dict):
    changed = False
    for phrase, repl in rules["wordy_phrases"].items():
        pat = re.compile(r"(?<![A-Za-z])" + re.escape(phrase.strip()) + r"(?![A-Za-z])" + (r"\s*" if phrase.endswith(" ") else ""), re.I)
        new = pat.sub(repl, body)
        if new != body:
            body, changed = new, True
    return re.sub(r"\s{2,}", " ", body).strip(), changed


def align_terms(body: str, match: MatchResult):
    """Use the job ad's spelling for a skill the CV already shows ('k8s' -> 'Kubernetes')."""
    changed: List[str] = []
    for t in match.hits():
        for form in t.cv_forms:
            a, b = form.lower(), t.job_form.lower()
            # skip when one already contains the other ("demand forecasting" vs
            # "forecasting"): the keyword is there and swapping would lose detail
            if a in b or b in a:
                continue
            # only swap true synonyms, never replace a specific tool with a broad category
            if len(t.job_form) > 3 * max(len(form), 4):
                continue
            pat = re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(form) + r"(?![A-Za-z0-9+#])")
            if pat.search(body):
                body = pat.sub(t.job_form, body)
                changed.append("%s → %s" % (form, t.job_form))
    return body, changed


def suggest(cv: CV, match: MatchResult) -> List[Suggestion]:
    rules = load_rules()
    out: List[Suggestion] = []
    for line in cv.lines:
        if line.is_heading or line.section in ("header", "education"):
            continue
        prefix, body = _split_bullet(line.text)
        applied, reasons = [], []
        if line.is_bullet or line.section in ("experience", "projects", "summary"):
            body, ch = strengthen_opener(body, rules)
            if ch:
                applied.append("action-verb")
                reasons.append("start with a strong action verb")
            body, ch = trim_wordy(body, rules)
            if ch:
                applied.append("concise")
                reasons.append("cut filler words")
        body, swaps = align_terms(body, match)
        if swaps:
            applied.append("job-terminology")
            reasons.append("use the job ad's wording: " + ", ".join(swaps))
        new = prefix + _cap(body) if prefix or applied else body
        if applied and new != line.text:
            out.append(Suggestion(line.index, line.text, new, applied, "; ".join(reasons).capitalize() + "."))
    return out


def apply(cv: CV, suggestions: List[Suggestion], accepted=None) -> str:
    chosen = {s.line: s.improved for i, s in enumerate(suggestions) if accepted is None or i in accepted}
    out = []
    for l in cv.lines:
        if l.is_heading and out:
            out.append("")  # keep a blank line before each section
        out.append(chosen.get(l.index, l.text))
    return "\n".join(out)

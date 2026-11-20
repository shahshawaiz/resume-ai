"""Industry glossaries: canonical terms, their aliases, and matching rules.

Each glossary is a JSON file in ``resume_ai/glossaries``. A term is matched
when its canonical name or any alias occurs as a whole word. Short or
ambiguous words ("Go", "R", "ML") can be marked case-sensitive so that
"go to market" does not count as the Go language.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

GLOSSARY_DIR = Path(__file__).parent / "glossaries"
RULES_PATH = Path(__file__).parent / "rules.json"

# Characters that count as "part of a word" for boundary checks, so that
# "C" does not match inside "C++" and "Node" does not match "Node.js".
_WORD = r"A-Za-z0-9+#"


@dataclass
class Term:
    term: str
    category: str
    industry: str
    aliases: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    case_sensitive_aliases: List[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.term.lower()

    def surface_forms(self) -> List[str]:
        """Canonical name first, then aliases, longest first within aliases."""
        return [self.term] + sorted(self.aliases, key=len, reverse=True)

    def _is_cs(self, form: str) -> bool:
        if form == self.term:
            return self.case_sensitive
        return self.case_sensitive or form in self.case_sensitive_aliases


@dataclass
class Glossary:
    industry: str
    label: str
    signals: List[str]
    terms: List[Term]


def _pattern(form: str, case_sensitive: bool) -> "re.Pattern[str]":
    body = re.escape(form).replace(r"\ ", r"[\s-]+")
    # allow a simple plural on purely alphabetic forms ("dashboard(s)")
    plural = "(?:s|es)?" if not case_sensitive and re.fullmatch(r"[A-Za-z][A-Za-z ]*[a-z]", form) else ""
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(r"(?<![" + _WORD + r"])" + body + plural + r"(?![" + _WORD + r"]|\.[A-Za-z])", flags)


class Matcher:
    """Finds glossary terms in text. Builds its regexes once."""

    def __init__(self, terms: Iterable[Term]):
        self.terms: Dict[str, Term] = {}
        for t in terms:
            # first glossary wins for a shared term, but aliases are merged
            if t.key in self.terms:
                existing = self.terms[t.key]
                for a in t.aliases:
                    if a not in existing.aliases:
                        existing.aliases.append(a)
                for a in t.case_sensitive_aliases:
                    if a not in existing.case_sensitive_aliases:
                        existing.case_sensitive_aliases.append(a)
            else:
                self.terms[t.key] = Term(**{**t.__dict__, "aliases": list(t.aliases),
                                            "case_sensitive_aliases": list(t.case_sensitive_aliases)})
        self._patterns: List[Tuple[str, str, "re.Pattern[str]"]] = []
        for t in self.terms.values():
            for form in t.surface_forms():
                self._patterns.append((t.key, form, _pattern(form, t._is_cs(form))))
        # longest forms first so "Google Cloud Platform" wins over "Google Cloud"
        self._patterns.sort(key=lambda p: len(p[1]), reverse=True)

    def find(self, text: str) -> Dict[str, List[Tuple[str, int, int]]]:
        """Return {term_key: [(matched_text, start, end), ...]} without overlaps."""
        taken: List[Tuple[int, int]] = []
        found: Dict[str, List[Tuple[str, int, int]]] = {}
        for key, _form, pat in self._patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                if any(s < te and e > ts for ts, te in taken):
                    continue
                taken.append((s, e))
                found.setdefault(key, []).append((m.group(0), s, e))
        return found

    def contains(self, text: str, key: str) -> bool:
        return key in self.find(text)


def _load_file(path: Path) -> Glossary:
    data = json.loads(path.read_text(encoding="utf-8"))
    industry = data["industry"]
    terms = [Term(term=t["term"], category=t.get("category", ""), industry=industry,
                  aliases=t.get("aliases", []), case_sensitive=t.get("case_sensitive", False),
                  case_sensitive_aliases=t.get("case_sensitive_aliases", []))
             for t in data["terms"]]
    return Glossary(industry=industry, label=data["label"], signals=data.get("signals", []), terms=terms)


_CACHE: Dict[str, Glossary] = {}


def load_glossaries(directory: Optional[Path] = None) -> Dict[str, Glossary]:
    directory = directory or GLOSSARY_DIR
    if directory == GLOSSARY_DIR and _CACHE:
        return _CACHE
    out = {g.industry: g for g in (_load_file(p) for p in sorted(directory.glob("*.json")))}
    if directory == GLOSSARY_DIR:
        _CACHE.update(out)
    return out


def load_rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def detect_industry(job_text: str, glossaries: Optional[Dict[str, Glossary]] = None) -> List[Tuple[str, float]]:
    """Rank industries for a job ad. Signals (job-title words) count 3x a term hit."""
    glossaries = glossaries or load_glossaries()
    low = job_text.lower()
    scores = []
    for g in glossaries.values():
        if g.industry == "general":
            continue
        signal_hits = sum(1 for s in g.signals if re.search(r"(?<![a-z])" + re.escape(s) + r"(?![a-z])", low))
        term_hits = len(Matcher(g.terms).find(job_text))
        scores.append((g.industry, float(3 * signal_hits + term_hits)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def matcher_for(industry: str, glossaries: Optional[Dict[str, Glossary]] = None) -> Matcher:
    """Industry glossary plus the general (cross-industry) glossary."""
    glossaries = glossaries or load_glossaries()
    if industry not in glossaries:
        raise ValueError("Unknown industry %r. Known: %s" % (industry, ", ".join(sorted(glossaries))))
    terms = list(glossaries[industry].terms)
    if industry != "general" and "general" in glossaries:
        terms += glossaries["general"].terms
    return Matcher(terms)

"""Compare a CV with a job ad using an industry glossary."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .cv_parser import CV
from .glossary import Matcher, detect_industry, load_glossaries, matcher_for
from .job_parser import JobAd, split_preferred_clause

WEIGHTS = {"required": 3.0, "preferred": 1.0, "other": 1.5}


@dataclass
class TermResult:
    term: str            # canonical glossary name
    category: str
    importance: str      # required | preferred | other
    job_form: str        # how the job ad writes it
    found: bool
    cv_forms: List[str] = field(default_factory=list)   # how the CV writes it
    evidence: List[int] = field(default_factory=list)   # CV line indexes

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class MatchResult:
    industry: str
    industry_label: str
    industry_ranking: List[tuple]
    terms: List[TermResult]
    score: int
    required_score: int

    def hits(self) -> List[TermResult]:
        return [t for t in self.terms if t.found]

    def misses(self) -> List[TermResult]:
        return [t for t in self.terms if not t.found]

    def as_dict(self) -> dict:
        return {
            "industry": self.industry, "industry_label": self.industry_label,
            "industry_ranking": [{"industry": i, "score": s} for i, s in self.industry_ranking],
            "score": self.score, "required_score": self.required_score,
            "terms": [t.as_dict() for t in self.terms],
        }


def _job_terms(job: JobAd, m: Matcher) -> Dict[str, tuple]:
    """{key: (importance, job_form)}; the most important mention wins."""
    rank = {"required": 0, "other": 1, "preferred": 2}
    out: Dict[str, tuple] = {}

    def add(text: str, kind: str):
        for key, hits in m.find(text).items():
            if key not in out or rank[kind] < rank[out[key][0]]:
                out[key] = (kind, hits[0][0])

    for line in job.lines:
        if line.kind == "mixed":
            req, pref = split_preferred_clause(line.text)
            add(req, "required")
            add(pref, "preferred")
        else:
            add(line.text, line.kind)
    return out


def match(cv: CV, job: JobAd, industry: Optional[str] = None) -> MatchResult:
    glossaries = load_glossaries()
    ranking = detect_industry(job.text, glossaries)
    if not industry or industry == "auto":
        industry = ranking[0][0] if ranking and ranking[0][1] > 0 else "general"
    m = matcher_for(industry, glossaries)

    job_terms = _job_terms(job, m)
    cv_hits_by_line = [m.find(l.text) for l in cv.lines]

    results: List[TermResult] = []
    for key, (importance, job_form) in job_terms.items():
        t = m.terms[key]
        evidence = [i for i, hits in enumerate(cv_hits_by_line) if key in hits]
        forms = sorted({h[0] for i in evidence for h in cv_hits_by_line[i][key]})
        results.append(TermResult(term=t.term, category=t.category, importance=importance,
                                  job_form=job_form, found=bool(evidence), cv_forms=forms, evidence=evidence))
    order = {"required": 0, "other": 1, "preferred": 2}
    results.sort(key=lambda r: (order[r.importance], not r.found, r.term.lower()))

    total = sum(WEIGHTS[r.importance] for r in results)
    got = sum(WEIGHTS[r.importance] for r in results if r.found)
    req = [r for r in results if r.importance == "required"]
    score = round(100 * got / total) if total else 0
    req_score = round(100 * sum(r.found for r in req) / len(req)) if req else score
    return MatchResult(industry=industry, industry_label=glossaries[industry].label,
                       industry_ranking=ranking, terms=results, score=score, required_score=req_score)

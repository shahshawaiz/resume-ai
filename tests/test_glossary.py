from resume_ai.glossary import detect_industry, load_glossaries, matcher_for


def test_all_glossaries_load():
    g = load_glossaries()
    assert {"general", "software", "data", "finance", "healthcare", "marketing"} <= set(g)
    for gl in g.values():
        assert gl.terms, gl.industry


def test_alias_maps_to_canonical_term():
    m = matcher_for("software")
    assert "kubernetes" in m.find("Deployed services on k8s")
    assert "postgresql" in m.find("Postgres and Redis")


def test_case_sensitive_terms_avoid_false_positives():
    m = matcher_for("software")
    assert "go" not in m.find("We go to market fast")
    assert "go" in m.find("Wrote services in Go and Python")


def test_symbols_and_word_boundaries():
    m = matcher_for("software")
    found = m.find("C++, C# and Node.js")
    assert {"c++", "c#", "node.js"} <= set(found)
    assert "javascript" not in m.find("Wrote a JSON parser")


def test_longest_form_wins_without_double_counting():
    m = matcher_for("software")
    hits = m.find("Google Cloud Platform")
    assert list(hits) == ["google cloud"]


def test_detect_industry(job_text):
    assert detect_industry(job_text)[0][0] == "data"
    assert detect_industry("Senior Accountant: month-end close, IFRS, SAP FI, reconciliations")[0][0] == "finance"
    assert detect_industry("Registered nurse for our ICU, BLS required, patient care")[0][0] == "healthcare"

from resume_ai.job_parser import parse_job, split_preferred_clause


def test_role_company_and_years(job_text):
    job = parse_job(job_text)
    assert job.role == "Machine Learning Engineer"
    assert job.company == "Nordlicht Health GmbH"
    assert job.min_years == 3


def test_sections_are_classified(job_text):
    job = parse_job(job_text)
    req = job.text_of("required")
    assert "scikit-learn" in req
    assert "Vertex AI" in job.text_of("other")


def test_preferred_heading():
    job = parse_job("Data Analyst - Acme\n\nRequirements\n- SQL\n\nNice to have\n- dbt\n")
    assert job.text_of("required") == "- SQL"
    assert job.text_of("preferred") == "- dbt"


def test_inline_plus_is_split():
    req, pref = split_preferred_clause("Docker and Kubernetes; Airflow is a plus")
    assert "Kubernetes" in req and "Airflow" in pref
    req, pref = split_preferred_clause("Strong SQL and cloud platforms (GCP preferred)")
    assert "SQL" in req and "GCP" in pref and "GCP" not in req

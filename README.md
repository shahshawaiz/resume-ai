# Resume AI

_By [Shawaiz Shah](https://shawaiz.de) · [more side projects](https://shawaiz.de/projects/)_

Tailor your CV to a specific job ad, fully offline. Resume AI compares your CV (PDF or text) with a job description using **industry-specific glossaries** and **deterministic rules**. It shows a weighted match score, suggests line-by-line changes that use the job ad's wording without inventing experience, runs ATS-style checks, and fills in a cover letter template. You can export to PDF (including your original PDF layout) or Word.

**Who it's for:** job seekers who send many applications and want each CV to fit the role, without uploading their CV to a third-party service.

**Runs offline:** plain Python with no network calls, no accounts and no external services. Your CV stays on your machine.

## How it works

1. **Parse the CV.** PyMuPDF reads the PDF. Font size and weight, together with standard heading names, split it into header, summary, experience, education, skills and other sections. Bullets are detected.
2. **Parse the job ad.** Lines are sorted into *required*, *nice to have* and *other*, based on headings ("Your profile", "Nice to have") and inline markers ("… is a plus", "(GCP preferred)"). Role, company and minimum years of experience are pulled out.
3. **Pick a glossary.** The industry is detected from the job ad, or you choose it. Each glossary lists canonical terms with aliases (`k8s` → Kubernetes, `sklearn` → scikit-learn), categories and case rules, so "go to market" does not count as the Go language. A cross-industry glossary (soft skills, languages, degrees) is always added.
4. **Score the match.** Each job-ad term counts as found if the CV contains the term or any alias. Weights: required ×3, other mentions ×1.5, nice to have ×1. You get an overall score, the share of required skills covered, and the CV lines that back each term.
5. **Suggest changes.** These are rules that only rephrase what is already there:
   - weak openers become action verbs ("Responsible for managing" → "Managed", "Worked on" → "Built")
   - filler words are cut ("in order to" → "to", "utilized" → "used")
   - the job ad's spelling is used for a skill the CV already shows ("k8s" → "Kubernetes")
   No rule adds a skill, number or employer.
6. **Check the CV.** ATS-style checks: contact details, standard section headings, length, mixed date formats, action verbs, numbers in results, overlong bullets, first-person pronouns, icon-font characters, and years of experience against the job ad.
7. **Draft a cover letter.** An English or German template filled with the role, the company, the best-matched required skills and your own CV lines as examples.
8. **Export.** Accepted changes are written back into the **original PDF** in place (position, size and colour are kept), or exported as a clean single-column PDF or a Word document.

### Glossaries

| File | Industry |
|---|---|
| `resume_ai/glossaries/software.json` | Software engineering |
| `resume_ai/glossaries/data.json` | Data science and machine learning |
| `resume_ai/glossaries/finance.json` | Finance and accounting |
| `resume_ai/glossaries/healthcare.json` | Healthcare and life sciences |
| `resume_ai/glossaries/marketing.json` | Marketing and growth |
| `resume_ai/glossaries/general.json` | Cross-industry (always on) |

To add an industry, drop in a JSON file with `industry`, `label`, `signals` (job-title words used for detection) and `terms` (`term`, `aliases`, `category`, optional `case_sensitive` / `case_sensitive_aliases`). Rewrite rules live in `resume_ai/rules.json`.

## Built with

Python 3.9+, [PyMuPDF](https://pymupdf.readthedocs.io/) (PDF parsing, in-place rewriting and PDF export), [Flask](https://flask.palletsprojects.com/) (local web UI on 127.0.0.1), [python-docx](https://python-docx.readthedocs.io/) (Word export), pytest. The frontend is plain HTML, CSS and JavaScript with no CDN or external fonts.

## How to run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# web UI at http://127.0.0.1:8000
.venv/bin/python -m resume_ai serve

# or the command line
.venv/bin/python -m resume_ai analyze samples/cv_data_scientist.txt samples/job_ml_engineer.txt
.venv/bin/python -m resume_ai analyze my_cv.pdf job.txt --industry finance --lang de --json

# tests
.venv/bin/python -m pytest
```

In the web UI, click **Load sample** to try it with fictional data.

## Limits

- The PDF has to have a text layer. Scanned or image-only CVs are not supported (no OCR).
- The parser is tuned for single-column CVs. Multi-column layouts may mix up the line order.
- Writing back into the original PDF uses Helvetica for changed lines. If a line cannot be found as one piece of text in the PDF, it is skipped and reported.
- Matching only knows the terms in the glossaries. A skill that is not listed is not scored.
- The cover letter is a template to edit, not finished prose.

## Privacy and data

- The repository contains only fictional sample data (`samples/`).
- The web UI listens on 127.0.0.1 only. An uploaded PDF is kept in memory for the running process and never written to disk.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Author

Built and maintained by **[Shawaiz Shah](https://shawaiz.de)** · [GitHub](https://github.com/shahshawaiz) · [LinkedIn](https://www.linkedin.com/in/shawaiz-shah-32b40537).

## License

[MIT](LICENSE) © Shawaiz Shah

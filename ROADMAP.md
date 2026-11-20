# Roadmap

Resume AI is an offline, rule-based CV tailoring tool. Everything below keeps that constraint: plain Python, no network, no external services.

## Done (base version)

- [x] PDF and text CV parsing into sections and bullets (PyMuPDF)
- [x] Job-ad parsing into required, nice-to-have and other lines; role, company, minimum years
- [x] Five industry glossaries plus a cross-industry one, with aliases and case rules
- [x] Term matching: found and missing job-ad terms, with the CV lines that back each one
- [x] Rewrite rules: action verbs, filler words, the job ad's terminology for existing skills
- [x] Cover letter template (English, German)
- [x] Export: in-place rewrite of the original PDF, plain PDF, DOCX

## 1. ATS compatibility report

Show how an applicant tracking system would read the file, not only what the text says.

- [ ] **Basic checks:** contact details, standard section headings (Experience, Education, Skills), length, mixed date formats, bullets that don't start with an action verb, results without numbers, overlong bullets, first-person pronouns, icon-font characters, years of experience vs the job ad
- [ ] **Parse simulation:** extract the text the way a simple ATS does (reading order, no layout) and show it next to the original, with lost or reordered content highlighted
- [ ] **Layout risks:** detect multi-column layouts, tables, text in headers and footers, text boxes, images of text and missing text layers
- [ ] **File checks:** fonts not embedded, unusual encodings or ligatures that break copy and paste, file size, page count
- [ ] **Field extraction test:** can name, email, phone, job titles, employers and dates be pulled out reliably? Report each field as found, ambiguous or missing
- [ ] **ATS score:** a 0–100 compatibility score built from the checks, with each deduction explained and a fix suggested
- **Done when:** a test set of at least 20 fictional CV PDFs (single-column, two-column, table-based, scanned) gets the expected verdict for every known layout risk

## 2. Weighted keyword optimization

Make the score reflect what the recruiter actually cares about.

- [ ] **Weighted match score:** required ×3, other mentions ×1.5, nice to have ×1, giving an overall score and the share of required skills covered
- [ ] **Importance weights:** extra weight for terms in the job title, terms repeated in the ad, and terms in the first requirement bullets
- [ ] **Either/or groups:** "scikit-learn or PyTorch" is satisfied by one of them, not counted as two separate requirements
- [ ] **Evidence weights:** a skill used in an experience bullet counts more than one only listed under Skills; recent roles count more than old ones
- [ ] **Keyword stuffing guard:** flag terms repeated too often, and skills listed with no supporting bullet
- [ ] **Optimization plan:** a ranked list of "highest-value edits", meaning missing or weakly evidenced required terms the CV could honestly cover, with the line where each fits best
- [ ] **Configurable weights:** per-glossary weight profile in JSON, so finance and software can weigh certifications vs tools differently
- **Done when:** on a hand-labelled set of 30 fictional CV/job pairs, the ranking of CVs by score matches the human ranking (Spearman ≥ 0.7), and either/or requirements are never double-counted

## 3. Keyword scoring and explanations

- [ ] Score breakdown per term: weight, where it appears in the ad, where it was found in the CV, and how many points it adds
- [ ] "What if" view: tick the missing skills you really have and see the new score before editing
- [ ] Category view: score per category (languages, tools, cloud, methods, soft skills)
- [ ] Seniority signals: compare the job ad's level words (junior, senior, lead) and years with the CV's titles and date spans

## 4. Data persistence, import and export

Keep everything local, in one file the user owns.

- [ ] **SQLite store** (`~/.resume_ai/resume_ai.db`): CVs, CV versions, job ads, analyses, accepted changes, cover letters
- [ ] **Application tracker:** company, role, date applied, status (draft, applied, interview, offer, rejected), notes, linked CV version and letter
- [ ] **CV versions with diff:** each tailored CV is saved as a version; side-by-side diff against the base CV
- [ ] **Export:** full backup as JSON (schema-versioned) and the tracker as CSV
- [ ] **Import:** restore a JSON backup (merge or replace, with conflict detection), and import job ads in bulk from `.txt`/`.md` files
- [ ] **Schema migrations** so old backups still import after upgrades
- **Done when:** export → wipe → import reproduces the database exactly (round-trip test), and a backup from the previous schema version imports cleanly

## 5. Glossaries

- [ ] More industries: legal, HR, sales, logistics and supply chain, education, engineering and manufacturing, design
- [ ] German-language glossaries (job ads in German, mixed German/English CVs)
- [ ] User glossaries: add your own terms and aliases in the UI, stored locally, exported with the backup
- [ ] Glossary linter: duplicate aliases, aliases shared across terms, terms that never match the test corpus
- [ ] Related terms (e.g. "PostgreSQL" partly evidences "SQL") with a lower weight than an exact match

## 6. Better tailoring

- [ ] Bullet reordering: put the most job-relevant bullets first in each role
- [ ] Summary builder: a summary line from a template, using title, years and top matched required skills
- [ ] Batch mode: one CV against many job ads, ranked by score (CLI and UI)
- [ ] One job ad against several CV variants, side by side
- [ ] Country presets: German CV conventions (photo, date of birth, Lebenslauf section names) vs US/UK (no photo, no personal data), with a privacy check that flags personal data before export

## 7. Interfaces

- [ ] **Local web UI:** Flask on 127.0.0.1 with plain HTML/CSS/JS (no CDN, no external fonts); CV upload or paste, job ad, glossary picker; tabs for match, changes (accept/reject each), checks and cover letter; downloads for every export
- [ ] **Command line:** `python -m resume_ai analyze CV JOB` with a readable report and `--json` output for scripting; `serve` to start the web UI
- [ ] **Done when:** the full flow (upload PDF → analyze → accept changes → download original-layout PDF) works end to end in the browser and is covered by tests

## 8. Quality and tooling

- [ ] **pytest suite:** unit tests for glossary matching (aliases, case rules, word boundaries), job-ad parsing, matching, each rewrite rule, the cover letter, PDF/DOCX export and the in-place PDF rewrite; web and CLI tests once those exist

- [ ] Fictional benchmark corpus with labelled expected terms, sections and checks; CI runs the benchmark and fails on precision/recall regressions
- [ ] Multi-column PDF reading order
- [ ] Better in-place PDF rewriting: reuse the original font when it is embedded, and reflow when the new line is longer
- [ ] Packaging: `pip install .` with a `resume-ai` command
- [ ] Accessibility pass on the web UI (keyboard, screen reader, contrast)

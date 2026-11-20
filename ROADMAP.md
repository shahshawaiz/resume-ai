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

## 7. Career timeline and skill-duration engine

Turn the free-text experience section into structured, dated data, so requirements like "3+ years of Python" or "2 years in a lead role" can be checked per skill, not just for the whole CV.

- [ ] **Role segmentation:** split the experience section into roles (title, employer, location, start, end, bullets), whatever the layout: title-first, employer-first, dates on the left, right or on their own line
- [ ] **Date normalisation:** parse every common format ("03/2021", "Mar 2021", "März 2021", "2021–present", "seit 2021", "Q1 2021", year only) into month ranges, with an explicit precision flag (month vs year only)
- [ ] **Timeline checks:** gaps over a configurable length, overlapping roles (concurrent jobs vs date errors), roles in reverse order, end dates in the future
- [ ] **Skill duration:** for every glossary term, add up the months of the roles whose bullets give evidence for it, merging overlapping roles so time is not counted twice. Report years per skill and the date of last use
- [ ] **Seniority track:** classify each title (intern, junior, mid, senior, lead, head) with rule tables per industry, and compute months at each level
- [ ] **Requirement check:** pull structured experience requirements out of the job ad ("3+ years Python", "at least 5 years in accounting", "mindestens 2 Jahre Führungserfahrung") and compare them with the computed durations: met, close (within 6 months), not met
- [ ] **Done when:** on 40 hand-labelled fictional CVs (English and German, at least 5 layouts), role fields reach F1 ≥ 0.9, parsed date ranges match exactly for ≥ 95% of roles, and per-skill durations are within one month of the labels

## 8. One-page CV optimizer

Choose and arrange the CV content that best fits a given job within a page budget, measured on the real rendered layout rather than by word count.

- [ ] **Content model:** every bullet, skill line and summary sentence becomes a block with a measured rendered height (PyMuPDF text metrics at the CV's font and width), its glossary terms, its role and its date
- [ ] **Objective:** maximise weighted coverage of the job's requirements (required > other > nice to have, using the section 2 weights), with diminishing returns for evidence repeated for the same term, a bonus for recent roles and a penalty for dropping a role entirely
- [ ] **Constraints:** total height ≤ page budget (1 or 2 pages), at least N bullets per kept role, role order stays chronological, fixed blocks (header, education, contact) always kept, user-pinned or banned bullets respected
- [ ] **Solver:** exact branch-and-bound for typical CV sizes (up to ~60 blocks), with a greedy plus local-search fallback for larger ones and a time limit. Both are pure Python, so it runs offline
- [ ] **Explain the result:** which bullets were dropped and what each one would have added, which requirements are left uncovered, and how much space is left
- [ ] **Render:** produce the optimised CV through the PDF/DOCX exporters and check after rendering that it really fits the page budget. If it doesn't, tighten the budget and solve again
- [ ] **Done when:** on 20 fictional CV/job pairs the exact solver finds the proven optimum within 2 seconds, the greedy fallback reaches ≥ 95% of it, and every rendered output fits the page budget

## 9. Interfaces

- [ ] **Local web UI:** Flask on 127.0.0.1 with plain HTML/CSS/JS (no CDN, no external fonts); CV upload or paste, job ad, glossary picker; tabs for match, changes (accept/reject each), checks and cover letter; downloads for every export
- [ ] **Command line:** `python -m resume_ai analyze CV JOB` with a readable report and `--json` output for scripting; `serve` to start the web UI
- [ ] **Done when:** the full flow (upload PDF → analyze → accept changes → download original-layout PDF) works end to end in the browser and is covered by tests

## 10. Quality and tooling

- [ ] **pytest suite:** unit tests for glossary matching (aliases, case rules, word boundaries), job-ad parsing, matching, each rewrite rule, the cover letter, PDF/DOCX export and the in-place PDF rewrite; web and CLI tests once those exist

- [ ] Fictional benchmark corpus with labelled expected terms, sections and checks; CI runs the benchmark and fails on precision/recall regressions
- [ ] Multi-column PDF reading order
- [ ] Better in-place PDF rewriting: reuse the original font when it is embedded, and reflow when the new line is longer
- [ ] Packaging: `pip install .` with a `resume-ai` command
- [ ] Accessibility pass on the web UI (keyboard, screen reader, contrast)

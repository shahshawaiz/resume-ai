# Roadmap

## Next
- [ ] Web demo: keep the original PDF layout by writing accepted changes back into the PDF (pdf-lib), like the server version does
- [ ] Web demo: real `.docx` export instead of Word-compatible HTML
- [ ] Server: replace the OpenAI call with a local model (Ollama / llama.cpp), keeping the paid API optional
- [ ] Server: upgrade the Python 3.8 / Flask stack and pin dependencies
- [ ] Automated tests for PDF text extraction and line replacement

## Later
- [ ] Multiple CV variants per job ad, with a side-by-side comparison
- [ ] German and English UI
- [ ] ATS-style checks: section order, date formats, length
- [ ] Track applications (job ad, tailored CV, letter) locally in IndexedDB

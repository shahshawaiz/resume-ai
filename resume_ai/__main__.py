"""Command line: `python -m resume_ai serve` or `python -m resume_ai analyze CV JOB`."""
import argparse
import json
import sys
from pathlib import Path


def _load_cv(path: str):
    from .cv_parser import parse_pdf, parse_text
    p = Path(path)
    return parse_pdf(str(p)) if p.suffix.lower() == ".pdf" else parse_text(p.read_text(encoding="utf-8"))


def _print_report(r: dict) -> None:
    m = r["match"]
    print("Role: %s · Company: %s" % (r["job"]["role"] or "?", r["job"]["company"] or "?"))
    print("Industry glossary: %s" % m["industry_label"])
    print("Match score: %d%% (required skills: %d%%)\n" % (m["score"], m["required_score"]))
    for imp in ("required", "other", "preferred"):
        ts = [t for t in m["terms"] if t["importance"] == imp]
        if ts:
            print("%s:" % {"required": "Required", "other": "Also mentioned", "preferred": "Nice to have"}[imp])
            for t in ts:
                print("  %s %s" % ("✓" if t["found"] else "✗", t["job_form"]))
    if r["suggestions"]:
        print("\nSuggested changes:")
        for s in r["suggestions"]:
            print("  - %s\n    + %s\n      (%s)" % (s["original"], s["improved"], s["reason"]))
    print("\nChecks:")
    for c in r["checks"]:
        print("  [%s] %s" % (c["level"], c["message"]))
    print("\nCover letter draft:\n")
    print(r["cover_letter"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="resume_ai", description="Offline, rule-based CV tailoring.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="start the local web UI")
    s.add_argument("--port", type=int, default=8000)
    a = sub.add_parser("analyze", help="compare a CV (PDF or .txt) with a job ad (.txt)")
    a.add_argument("cv")
    a.add_argument("job")
    a.add_argument("--industry", default="auto")
    a.add_argument("--lang", default="en", choices=["en", "de"])
    a.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = ap.parse_args(argv)

    if args.cmd == "serve":
        from .web import create_app
        print("Resume AI running at http://127.0.0.1:%d" % args.port)
        create_app().run(host="127.0.0.1", port=args.port)
        return 0

    from .analysis import analyze
    r = analyze(_load_cv(args.cv), Path(args.job).read_text(encoding="utf-8"), args.industry, args.lang)
    if args.json:
        json.dump(r, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        _print_report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())

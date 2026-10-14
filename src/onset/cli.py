
"""CLI: onset find <test-id> --ref <good-ref>"""

import argparse
import json
import sys
from pathlib import Path

from onset import __version__
from onset.bisect import find_onset
from onset.report import render_report


def cmd_find(args):
    finding = find_onset(
        test_id=args.test_id,
        good_ref=args.ref,
        runs=args.runs,
        cwd=args.cwd,
        verbose=not args.quiet,
    )

    print()
    print("=" * 60)
    if finding.status == "found":
        c = finding.culprit
        print("ONSET FOUND")
        print("=" * 60)
        print("  Commit:    " + c.sha)
        print("  Author:    " + c.author)
        print("  Date:      " + c.date)
        print("  Message:   " + c.message)
        print()
        print("  Flake rate before:  "
              + str(finding.before.failures) + "/" + str(finding.before.runs)
              + "  (" + str(round(finding.before.rate * 100)) + "%)")
        print("  Flake rate after:   "
              + str(finding.after.failures) + "/" + str(finding.after.runs)
              + "  (" + str(round(finding.after.rate * 100)) + "%)")
        print("  p-value:            " + str(round(finding.p_value, 4)))
        if c.files:
            print()
            print("  Changed files:")
            for f in c.files[:10]:
                print("    " + f)
        print()
        print("  Reproduce:")
        print("    git checkout " + c.short)
        print("    pytest " + args.test_id + " --count " + str(finding.after.runs))
    elif finding.status == "not_found":
        print("NO SINGLE CULPRIT")
        print("=" * 60)
        print("  " + finding.message)
        print("  Investigate the range: " + finding.range_from + " .. " + finding.range_to)
    elif finding.status == "no_flake":
        print("NOT FLAKY")
        print("=" * 60)
        print("  " + finding.message)
    else:
        print("ERROR")
        print("=" * 60)
        print("  " + finding.message)

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(finding.to_dict(), indent=2), encoding="utf-8")
        print()
        print("JSON: " + args.json)

    if args.html or args.open:
        html_path = render_report(finding, args.html)
        print("HTML: " + html_path)
        if args.open:
            import webbrowser
            webbrowser.open("file:///" + str(Path(html_path).resolve()))

    if finding.status == "error":
        sys.exit(2)
    if finding.status == "found":
        sys.exit(0)
    sys.exit(1)


def cmd_version(args):
    print("onset " + __version__)


def main():
    parser = argparse.ArgumentParser(
        prog="onset",
        description="Find the commit that made a test flaky",
    )
    parser.add_argument("--version", action="version", version="onset " + __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("find", help="find the onset commit of a flaky test")
    p.add_argument("test_id", help="pytest test ID, e.g. tests/test_x.py::test_y")
    p.add_argument("--ref", required=True, help="known-good reference (tag, branch, or SHA)")
    p.add_argument("--runs", type=int, default=None, help="runs per commit (default: from .env)")
    p.add_argument("--cwd", default=".", help="path to git repo (default: current dir)")
    p.add_argument("--quiet", action="store_true", help="no progress output")
    p.add_argument("--json", help="write JSON results here")
    p.add_argument("--html", help="write HTML report here")
    p.add_argument("--open", action="store_true", help="open HTML report in browser")
    p.set_defaults(func=cmd_find)

    pv = sub.add_parser("version")
    pv.set_defaults(func=cmd_version)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

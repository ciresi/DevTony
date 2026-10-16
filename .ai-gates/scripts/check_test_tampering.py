#!/usr/bin/env python3
"""Gate 3 deterministic checks B4 and B5.

B4 (blocking): no Apex test method was deleted or renamed away in this PR,
    and no test newly uses SeeAllData=true.
B5 (advisory): every AC ID in the story (AC1, AC2, ...) has a test method
    whose name contains it, e.g. test_AC2_rejectsBlankEmail.

Usage: check_test_tampering.py BASE_SHA STORY_FILE OUT_COMMENT_FILE
Exit 1 if B4 fails.
"""
import re
import subprocess
import sys

TEST_METHOD = re.compile(
    r"(?:@IsTest\b(?:\s*\([^)]*\))?[\s\w]*?\bvoid\s+(\w+)\s*\()"
    r"|(?:\btestMethod\b[\s\w]*?\bvoid\s+(\w+)\s*\()",
    re.I)
SEE_ALL = re.compile(r"SeeAllData\s*=\s*true", re.I)
AC_ID = re.compile(r"\bAC\s*-?\s*(\d+)\b", re.I)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def methods(src):
    return {(a or b) for a, b in TEST_METHOD.findall(src)}


def is_test_class(src):
    return re.search(r"@IsTest", src, re.I) is not None


def main():
    base, story_file, out = sys.argv[1], sys.argv[2], sys.argv[3]
    changed = git("diff", "--name-status", "%s...HEAD" % base).splitlines()

    removed, see_all = [], []
    for line in changed:
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        old_path = parts[1] if status.startswith("R") else path
        if not old_path.endswith(".cls") and not path.endswith(".cls"):
            continue
        before = git("show", "%s:%s" % (base, old_path)) if status != "A" else ""
        after = "" if status == "D" else git("show", "HEAD:%s" % path)
        if is_test_class(before):
            for m in sorted(methods(before) - methods(after)):
                removed.append("%s: %s" % (old_path, m))
        if SEE_ALL.search(after) and not SEE_ALL.search(before):
            see_all.append(path)

    # B5: AC coverage across all test classes in HEAD
    try:
        with open(story_file, encoding="utf-8") as f:
            acs = sorted({int(n) for n in AC_ID.findall(f.read())})
    except FileNotFoundError:
        acs = []
    all_tests = set()
    for path in git("ls-files", "*.cls").splitlines():
        src = git("show", "HEAD:%s" % path)
        if is_test_class(src):
            all_tests |= methods(src)
    uncovered = [n for n in acs
                 if not any(re.search(r"AC_?%d(?!\d)" % n, t, re.I) for t in all_tests)]

    b4_fail = bool(removed or see_all)
    lines = ["<!-- ai-gate:build -->", "### Gate 3 build checks (deterministic)", ""]
    lines.append("- **B4 test tampering:** %s" % ("FAIL" if b4_fail else "pass"))
    for r in removed:
        lines.append("  - removed test method `%s`" % r)
    for s in see_all:
        lines.append("  - new `SeeAllData=true` in `%s`" % s)
    if acs:
        lines.append("- **B5 AC-to-test mapping (advisory):** %s"
                     % ("pass" if not uncovered else "missing tests for " + ", ".join("AC%d" % n for n in uncovered)))
    else:
        lines.append("- **B5 AC-to-test mapping (advisory):** no AC IDs found in the story")
    lines.append("")
    lines.append("If a test removal is intentional, a reviewer can approve it and re-run with the label `ai-gate:allow-test-removal`.")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if b4_fail else 0)


if __name__ == "__main__":
    main()

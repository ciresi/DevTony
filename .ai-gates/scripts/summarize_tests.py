#!/usr/bin/env python3
"""Turn `sf apex run test --result-format json` output into compact inputs
for Gate 5, and enforce the coverage threshold (check B3).

Usage: summarize_tests.py RESULT_JSON MIN_COVERAGE OUT_RESULTS OUT_COVERAGE
Exit 1 if any test failed or coverage < MIN_COVERAGE.

The JSON shape of sf CLI output can change between CLI versions. This
script reads the fields defensively; if your CLI version differs, check
the raw file in the job's uploaded artifacts.
"""
import json
import sys


def main():
    src, min_cov, out_res, out_cov = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
    with open(src, encoding="utf-8") as f:
        raw = json.load(f)
    data = raw.get("result", raw)
    summary = data.get("summary", {})
    tests = data.get("tests", [])

    failed = [t for t in tests if str(t.get("Outcome", t.get("outcome", ""))).lower() not in ("pass", "passed")]
    lines = ["Outcome: %s" % summary.get("outcome", "unknown"),
             "Tests run: %s, failing: %s" % (summary.get("testsRan", len(tests)), summary.get("failing", len(failed))),
             "", "Test methods:"]
    for t in tests:
        name = t.get("FullName") or "%s.%s" % (t.get("ApexClass", {}).get("Name", "?"), t.get("MethodName", "?"))
        outcome = t.get("Outcome", t.get("outcome", "?"))
        msg = (t.get("Message") or "").replace("\n", " ")[:300]
        lines.append("- %s: %s%s" % (name, outcome, (" | " + msg) if msg else ""))
    with open(out_res, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    org_cov = summary.get("orgWideCoverage") or summary.get("testRunCoverage") or "0%"
    try:
        cov_value = float(str(org_cov).rstrip("%"))
    except ValueError:
        cov_value = 0.0
    cov_lines = ["Threshold: %.0f%%" % min_cov, "Run coverage: %s" % org_cov, "", "Per class:"]
    for c in data.get("coverage", {}).get("coverage", []) or []:
        cov_lines.append("- %s: %s%%" % (c.get("name"), c.get("coveredPercent")))
    with open(out_cov, "w", encoding="utf-8") as f:
        f.write("\n".join(cov_lines) + "\n")

    print("\n".join(lines[:2] + cov_lines[:2]))
    ok = not failed and cov_value >= min_cov
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

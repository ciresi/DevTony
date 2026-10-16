#!/usr/bin/env python3
"""GitHub helpers for the AI gates. Standard library only.

Needs GITHUB_TOKEN and GITHUB_REPOSITORY (both set automatically in Actions).

  gh.py story-for-pr PR_NUMBER OUT_FILE
      Writes the linked story (issue referenced as "Closes #12", "Fixes #12",
      "Resolves #12" or "Story: #12" in the PR body). Falls back to the PR body.
  gh.py issue ISSUE_NUMBER OUT_FILE
      Writes an issue's title and body.
  gh.py comment NUMBER COMMENT_FILE [VERDICT]
      Creates or updates the gate's comment on a PR or issue (matched by its
      hidden marker). VERDICT=needs_human adds the label ai-gate:needs-human.
  gh.py collect-verdicts BASE_REF OUT_JSON OUT_SCOPE
      For every PR merged into the default branch after BASE_REF (a tag or
      ISO date), gathers the gate verdicts from its comments.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
LABEL = "ai-gate:needs-human"
ALL_GATES = ["requirements", "design", "code_review", "test", "security"]


def gh(method, path, payload=None):
    token = os.environ.get("GITHUB_TOKEN")
    if not token or not REPO:
        sys.exit("GITHUB_TOKEN and GITHUB_REPOSITORY must be set")
    url = path if path.startswith("http") else "%s/repos/%s%s" % (API, REPO, path)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        sys.exit("GitHub %s %s failed: %s %s" % (method, path, e.code, e.read()[:300]))


def paged(path):
    sep = "&" if "?" in path else "?"
    page = 1
    while True:
        items = gh("GET", "%s%sper_page=100&page=%d" % (path, sep, page))
        if not items:
            return
        yield from items
        if len(items) < 100:
            return
        page += 1


def linked_issue(body):
    m = re.search(r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|story:)\s*#(\d+)", body or "", re.I)
    return int(m.group(1)) if m else None


def write_issue(number, out):
    issue = gh("GET", "/issues/%d" % number)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# #%d %s\n\n%s\n" % (number, issue["title"], issue.get("body") or ""))


def story_for_pr(pr, out):
    p = gh("GET", "/pulls/%d" % pr)
    n = linked_issue(p.get("body"))
    if n:
        write_issue(n, out)
        print("story: issue #%d" % n)
    else:
        with open(out, "w", encoding="utf-8") as f:
            f.write("# PR #%d %s\n\n(No linked story issue found; using the PR description.)\n\n%s\n"
                    % (pr, p["title"], p.get("body") or ""))
        print("story: PR body (no linked issue)")


def upsert_comment(number, comment_file, verdict=None):
    with open(comment_file, encoding="utf-8") as f:
        body = f.read()
    marker = body.splitlines()[0]
    existing = next((c for c in paged("/issues/%d/comments" % number)
                     if (c.get("body") or "").startswith(marker)), None)
    if existing:
        gh("PATCH", "/issues/comments/%d" % existing["id"], {"body": body})
    else:
        gh("POST", "/issues/%d/comments" % number, {"body": body})
    if verdict == "needs_human":
        gh("POST", "/issues/%d/labels" % number, {"labels": [LABEL]})


def parse_verdicts(comments):
    found = {}
    for c in comments:
        m = re.search(r"<!-- ai-gate-json (.*?) -->", c.get("body") or "", re.S)
        if m:
            try:
                v = json.loads(m.group(1))
                found[v["gate"]] = v
            except (ValueError, KeyError):
                pass
    return found


def collect_verdicts(base_ref, out_json, out_scope):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", base_ref):
        since = base_ref
    else:
        since = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", base_ref], text=True).strip()
    default = gh("GET", "")["default_branch"]
    results, scope = [], ["# Release scope (PRs merged after %s)" % base_ref, ""]
    for p in paged("/pulls?state=closed&base=%s&sort=updated&direction=desc" % default):
        if not p.get("merged_at") or p["merged_at"] <= since:
            continue
        num = p["number"]
        gates = parse_verdicts(paged("/issues/%d/comments" % num))
        story = linked_issue(p.get("body"))
        if story:
            gates.update({k: v for k, v in parse_verdicts(paged("/issues/%d/comments" % story)).items()
                          if k not in gates})
        missing = [g for g in ALL_GATES if g not in gates]
        results.append({"pr": num, "title": p["title"], "story_issue": story,
                        "merged_at": p["merged_at"], "verdicts": gates,
                        "missing_gates": missing})
        scope.append("- PR #%d %s (story: %s)" % (num, p["title"], "#%d" % story if story else "none linked"))
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with open(out_scope, "w", encoding="utf-8") as f:
        f.write("\n".join(scope) + "\n")
    print("collected %d PRs" % len(results))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, a = sys.argv[1], sys.argv[2:]
    if cmd == "story-for-pr":
        story_for_pr(int(a[0]), a[1])
    elif cmd == "issue":
        write_issue(int(a[0]), a[1])
    elif cmd == "comment":
        upsert_comment(int(a[0]), a[1], a[2] if len(a) > 2 else None)
    elif cmd == "collect-verdicts":
        collect_verdicts(a[0], a[1], a[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

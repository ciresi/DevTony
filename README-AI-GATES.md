# AI quality gates for a Salesforce DX project on GitHub

This kit adds eight quality gates to your SDLC. AI agents review the work at
each gate; deterministic checks and people make the decisions that matter.

| Gate           | Runs when                             | Judged by                                              | Workflow                 |
| -------------- | ------------------------------------- | ------------------------------------------------------ | ------------------------ |
| 1 Requirements | Story issue labeled `ready-for-dev`   | AI (advisory)                                          | ai-gate-requirements.yml |
| 2 Design       | PR changes a file in `docs/design/`   | AI prepares, architect decides                         | ai-gates-pr.yml          |
| 3 Build        | Every PR touching `force-app/`        | Scratch org deploy, Apex tests, coverage, tamper check | ai-gates-pr.yml          |
| 4 Code review  | Every PR touching `force-app/`        | AI, then a human PR approval                           | ai-gates-pr.yml          |
| 5 Test         | After Gate 3                          | Test runner decides; AI explains gaps                  | ai-gates-pr.yml          |
| 6 Security     | Every PR touching `force-app/`        | Code Analyzer decides; AI triages                      | ai-gates-pr.yml          |
| 7 Release      | You run it before a prod deploy       | AI drafts packet, release owner decides                | ai-gate-release.yml      |
| 8 Post-deploy  | You run it (or chain it) after deploy | AI compares signals, on-call decides                   | ai-gate-post-deploy.yml  |

Everything starts in **advisory mode**: the AI gates comment, they never
block. Gate 3 and the Code Analyzer severity check do block, because they
are deterministic.

## Notes for this repo (DevTony)

- `force-app/` has no source yet, so Gates 3-6 will skip until a PR adds
  Apex, LWC or other metadata there. Gates 1, 2, 7 and 8 work now.
- Gate 3 also runs this repo's own `npm run lint` and LWC Jest tests (B6).
- Prettier (B7) runs report-only, because four files from the original
  project template don't pass it yet. Run `npm run prettier` once, commit,
  then remove `continue-on-error` from step B7 in `ai-gates-pr.yml`.

## What's in the kit

```
.ai-gates/
  gates.json                 model + advisory/blocking mode per gate
  prompts/01..08-*.md        one prompt + rubric per gate (edit these to tune)
  schema/verdict.schema.json the JSON every gate must return
  standards/architecture-standards.md   YOUR standards (Gates 2 and 4 judge against it)
  scripts/run_gate.py        calls the model, validates JSON, applies verdict rules
  scripts/gh.py              fetches stories, posts/updates PR comments, collects verdicts
  scripts/check_test_tampering.py       Gate 3 B4/B5
  scripts/summarize_tests.py            Gate 3 B2/B3 + Gate 5 inputs
.github/workflows/           the four workflows above
.github/pull_request_template.md, ISSUE_TEMPLATE/user-story.md, docs/design/TEMPLATE.md
```

The scripts use only the Python standard library, so CI needs no `pip install`.

## Setup (about an hour)

1. **Copy the kit into your repo root** on a new branch. It assumes the
   standard SFDX layout: `force-app/` and `config/project-scratch-def.json`.
   If your source lives elsewhere, change `SOURCE_DIR` in `ai-gates-pr.yml`.

2. **Add repository secrets** (Settings > Secrets and variables > Actions):
   - `ANTHROPIC_API_KEY` from the Claude Console.
   - `SFDX_AUTH_URL_DEVHUB`: run `sf org display --target-org <devhub> --verbose`
     and copy the "Sfdx Auth Url" value. Use a dedicated CI integration user.
   - `SFDX_AUTH_URL_PROD` (Gate 8 only): same, for a production user with
     **read-only** access. Gate 8 only queries; it never deploys.
     Treat auth URLs like passwords. Verify the current CLI auth options in the
     Salesforce CLI docs; JWT auth is the usual choice for production CI.

3. **Create the labels:**

   ```
   gh label create ready-for-dev
   gh label create ai-gate:needs-human --color D93F0B
   gh label create ai-gate:allow-test-removal --color FBCA04
   ```

4. **Replace `standards/architecture-standards.md`** with your real rules.
   This matters more than anything else in the kit. Vague standards give
   vague reviews.

5. **Check the model** in `gates.json`. It is set to `claude-sonnet-5-5`.
   Model names change; check the current list in the Claude docs and pin one.

6. **Open a PR with the kit itself** and confirm the workflows start. On
   that first PR, Gates 3-6 skip because nothing in `force-app/` changed.

## Day-to-day flow

1. Write a story with the issue template (numbered AC1, AC2...). Add
   `ready-for-dev`. Gate 1 comments on the issue within a minute or two.
2. For non-trivial stories, open a PR with `docs/design/story-<n>.md`. Gate 2
   comments; the architect approves the PR.
3. Build the change. The prompt in `prompts/03-build.md` is what you give
   your coding agent. Name test methods after ACs (`test_AC2_...`).
4. Open the PR with `Story: #<n>` in the description. Gates 3-6 run and
   each posts one comment that updates in place on every push.
5. Before release, run **AI Gate 7** from the Actions tab with the last
   release tag. It opens a "Release readiness" issue with the packet.
6. After the production deploy, run **AI Gate 8** with the deploy time.

Anything labeled `ai-gate:needs-human` is waiting on a person.

## How a verdict is decided

`run_gate.py` does not just trust the model. After the reply comes back it:

- rejects malformed JSON or a wrong shape -> `needs_human`
- drops any `fail` finding that has no evidence
- raises `pass` to `fail` if a blocking criterion failed
- turns a low-confidence `pass` into `needs_human`
- never lets Gate 2 return `fail` (the architect decides)
- treats an API error as `needs_human` (and as a failure in blocking mode)

## Testing a gate without CI or API spend

```
python3 .ai-gates/scripts/run_gate.py --gate code_review \
  --input story=story.md --input diff=pr.diff \
  --mock-response saved_reply.json --out-dir gate-out
```

Drop `--mock-response` and set `ANTHROPIC_API_KEY` to run it for real
against an old PR.

## Turning a gate to blocking

1. Run the gate in advisory mode on 20-50 real PRs or stories.
2. Track how often its blocking findings were real problems vs. noise.
3. Tune the prompt in `prompts/`. After every change, rerun the same set.
4. When your team agrees with it, set `"mode": "blocking"` in `gates.json`
   and make its job a required status check in branch protection.

I can't give you a universal accuracy target; pick what your team will
tolerate.

## Known limits and things to verify

- **Fork PRs:** GitHub does not pass secrets to workflows triggered by PRs
  from forks, so AI gates and Gate 3 won't run on them. This kit uses
  `pull_request` (not `pull_request_target`) on purpose; the latter would
  expose secrets to untrusted code.
- **Cost:** every gate run is an API call; Gates 4-6 run on every push.
  Check current pricing and watch usage for the first weeks.
- **Large diffs** are truncated at `max_input_chars`, and the gate is told
  to say so and lower its confidence.
- **CLI output shapes** (`sf apex run test --json`, Code Analyzer severity
  numbers) can change between versions. If Gate 3 or 6 behaves oddly, check
  the uploaded artifacts and the current Salesforce CLI reference.
- **Coverage:** `MIN_COVERAGE` defaults to 75, which I believe is
  Salesforce's org-wide production minimum. Confirm for your org.
- **Gate 8 signals** are a minimal starting point. Add the queries that
  actually show health in your org.
- These prompts are starting templates, not a benchmarked standard.

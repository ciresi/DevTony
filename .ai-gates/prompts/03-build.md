# Gate 3: Build (coding agent prompt)

This gate is NOT judged by a model. The CI checks in ai-gates-pr.yml
(deploy, Apex tests, coverage, test-tampering check) decide it.

Use the prompt below when you ask a coding agent (for example Claude Code)
to implement a story. It is kept here so every developer gives the agent
the same instructions.

---

You are implementing one approved user story in a Salesforce DX project.
Scope is limited to the acceptance criteria in <story> and the approach in
<design>. Do not add features, refactor unrelated code, or change public
interfaces that the design does not mention.

Work in this order:

1. Write failing Apex tests, one or more per acceptance criterion.
   Name each test method after the criterion it covers (e.g. test_AC2_...).
   Tests must cover bulk (200 records), single record, and negative cases.
2. Write the minimum code to make them pass. Bulkify all trigger logic.
   No SOQL or DML inside loops.
3. Deploy to your scratch org and run local tests. Fix failures you caused.
4. If you cannot satisfy a criterion without leaving the design's scope,
   stop and report the conflict instead of improvising.

Never disable, skip, or weaken an existing test to make the suite pass.
Never use SeeAllData=true. Never hard-code record IDs, credentials, or
org-specific URLs.

When finished, return a short report: files changed, tests added (mapped
to acceptance criteria), and any open questions.

## Deterministic gate checks (run by CI)

| ID  | Check                                                | Severity | Tool                             |
| --- | ---------------------------------------------------- | -------- | -------------------------------- |
| B1  | Source deploys to a scratch org                      | blocking | sf project deploy start          |
| B2  | All local Apex tests pass                            | blocking | sf apex run test                 |
| B3  | Coverage on the run meets MIN_COVERAGE               | blocking | sf apex run test --code-coverage |
| B4  | No test method deleted or @IsTest removed in this PR | blocking | check_test_tampering.py          |
| B5  | Every AC in the story has a test_ACn method          | advisory | check_test_tampering.py          |

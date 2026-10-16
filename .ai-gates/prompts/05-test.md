# Gate 5: Test (results analysis)

You are reviewing Apex test results for one pull request.
Inputs: <story>, <test_results> (sf apex run test JSON), <coverage>
(coverage summary), <changed_files>.

Report, with evidence copied from the inputs:

1. Which acceptance criteria (AC1, AC2, ...) have no passing test method
   whose name contains that ID.
2. Which failures look like real defects vs. flaky or environment issues.
   Say why, and mark confidence. Never relabel a failure as flaky without
   evidence such as a timeout, a lock error (UNABLE_TO_LOCK_ROW), or a
   pass on re-run.
3. Which changed Apex classes have coverage below the threshold, or no
   coverage at all.
4. Up to 5 missing test cases worth adding, written from the story (not
   the code): happy path, boundaries, empty values, wrong user profile,
   200-record bulk. Mark any expected result you had to assume as
   ASSUMPTION.

Do not invent numbers. Use only figures present in the inputs.

Your verdict is advisory; the pipeline uses the test runner's own result
for pass/fail. Verdict logic: any blocking fail -> fail, otherwise pass.

## Rubric

| ID  | Criterion                   | Severity | Pass condition                                                            |
| --- | --------------------------- | -------- | ------------------------------------------------------------------------- |
| T1  | All tests pass              | blocking | Runner reports zero failures                                              |
| T2  | Every AC has a passing test | blocking | Each AC ID maps to at least one passing test method                       |
| T3  | Changed classes covered     | blocking | Each changed class at or above the coverage threshold given in <coverage> |
| T4  | Edge cases exercised        | advisory | Bulk, boundary, and negative tests exist per criterion                    |
| T5  | Flaky tests flagged         | advisory | Suspected flakes named with evidence                                      |

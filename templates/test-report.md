# Test report template

Fill this in by executing `test-plan.md` for this PR — every planned scenario
(N*/R*/E*) must appear below with a result. Post it **as a comment on the GitHub
PR**, save it in the ticket worktree at `artifacts/SHU-<id>-test-report.md`
(that file is the durable record), and **attach it to the ticket on Jira board
SHU**.

---

## Test report: SHU-<ticket-id> — PR #<number>

**Tester:** <agent/session identifier>
**Verdict:** Pass | Fail

### Build & suite
- Build: <command> — <pass/fail, warnings>
- Test suite: <command> — <N passed, M failed, K skipped>; failures listed below

### End-to-end walkthrough
<Execute every N* (new behaviour) and R* (regression) scenario from the test
plan. Reference the plan's IDs; add rows only for unplanned discoveries.>

| ID | Scenario | Steps | Expected | Actual | Pass? |
|---|---|---|---|---|---|
| N1 | | | | | |

### Edge cases probed
<Execute every E* scenario from the test plan.>

| ID | Case | Result | Notes |
|---|---|---|---|
| E1 | | | |

### Failures
<For each failure: command or input, expected, actual, and how to reproduce.
Empty if none.>

### Required before merge
- <If Fail: the concrete failing items blocking merge.>

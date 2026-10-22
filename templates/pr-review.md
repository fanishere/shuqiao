# PR review template

Complete this review and post it **as a comment on the GitHub PR**. Save the
filled-in review in the ticket worktree at `artifacts/SHU-<id>-pr-review.md`
(that file is the durable record), and **attach it to the ticket on Jira board
SHU** (same ticket the PR references).

---

## Review: SHU-<ticket-id> — PR #<number>

**Reviewer:** <agent/session identifier>
**Verdict:** Approve | Request changes | Reject

### Acceptance criteria
- [ ] <criterion> — met / not met: <evidence>

### Principle conformance
<Check the change against README.md's seven principles. Name any principle the
change violates and how; "conforms" is acceptable with a sentence of reasoning.>

### Test quality
- Do tests cover the behaviour changed? <yes/no + what's missing>
- Would they fail without this change? <verified how?>

### Diff hygiene
<Scoped to the ticket? No drive-by refactors, reformatting, unrelated renames?>

### Comments for the developer
1. <file:line — what to change and why>
2. ...

### Required before merge
- <Only if verdict is Request changes: the concrete list of fixes. Empty if approving.>

### Scripts to keep
<CLI/shell verification steps from this review worth making permanent in the
repo (e.g. `scripts/smoke-test.sh`): command, what it verifies, proposed
location. Empty if none — but if you re-derived the same command as a past
review, that's a script the repo is missing.>

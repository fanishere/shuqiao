# Test plan template

Authored by the **reviewer** as part of the PR review, from the ticket's
acceptance criteria and the PR diff. Post it as a comment on the GitHub PR.
Expected values come from the ticket's intent, never from what the diff
currently does. The tester's completed `test-report.md` must cover every
scenario listed here — a report missing a planned scenario is incomplete.
Save the filled plan in the ticket worktree at
`artifacts/SHU-<id>-test-plan.md`; that file is the durable record.

---

## Test plan: SHU-<ticket-id> — PR #<number>

**Planner:** <agent/session identifier>

### New behaviour to confirm
<One row per acceptance criterion / new behaviour introduced by the PR. These
come from the ticket and the PR description's "What changed".>

| # | Scenario | How to exercise it | Expected |
|---|---|---|---|
| N1 | <e.g. focus item graduates after 2 correct unprompted uses> | | |

### Regression checks
<Existing behaviour this PR could plausibly break: shared code paths it touches,
data formats it changes, adjacent features. Trace the diff — every modified
shared module earns at least one regression scenario.>

| # | Scenario | Existing behaviour that must not change | How to exercise it |
|---|---|---|---|
| R1 | | | |

### Edge cases
<Boundaries the scenarios above don't cover: empty state / first run,
Chinese/unicode input, boundary HSK levels, long input, concurrent review
sessions — whatever the change makes plausible.>

| # | Case | Why it's plausible for this change |
|---|---|---|
| E1 | | |

### Out of scope
<What this plan deliberately does not test, and why.>

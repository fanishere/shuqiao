# Working agreement for agents in this repo

> Proposed content for `AGENTS.md`. Roles: pick the section matching your assignment.

## Project orientation
Read `README.md` first: it defines the product's purpose and the seven learning
principles. Features that violate a principle are wrong even if they pass tests.

## Workflow (all roles)
1. `main` is the release branch. All reviewed, tested work lands here.
2. Release branches (`release/v1.0`, `release/v1.1`, …) are cut only when asked.
   Never initiate a release on your own.
3. Ticket branches merge to `main` only via a pull request on GitHub.
4. Tickets live on the Jira Kanban board **SHU**. `Idea` tickets are not ready;
   everything without the `Manual` label is ready or in progress.
5. Read tickets from the local board cache in `board/` (one card per ticket,
   plus `INDEX.md`) — not from Jira. Record status changes, comments, and
   artifact attachments as pending ops on the card instead of calling Jira.
   Only the flush procedure pushes ops back to Jira. See `board/README.md`.
   Never re-pull while any card has `dirty: true`.

## Worktrees
The ticket's worktree is **shared and stable**: one worktree per ticket at
`.worktrees/SHU-<id>/` inside the repo (`.worktrees/` is gitignored), created by
whoever starts first, used by all roles (developer, reviewer, tester) for the
life of the ticket. Never create a second worktree for the same ticket. Delete
it only after the PR is merged and the ticket is closed.
Caution: `.worktrees/` is ignored, so `git status` won't warn about its
contents — never run blanket `git clean` in the repo root; remove worktrees
with `git worktree remove`.

## Artifacts
Every template output (PR review, test plan, test report) is stored in the
ticket's shared worktree under `artifacts/` as markdown, named
`SHU-<id>-<kind>.md` (e.g. `.worktrees/SHU-123/artifacts/SHU-123-test-plan.md`).
The worktree copy is the durable record; the PR comment and Jira attachment are
copies of it. Do not commit `artifacts/` — add it to `.gitignore`.

## Working on a ticket as developer
1. Branch off latest `main` as `SHU-123-brief-note` in the ticket's shared
   worktree (see Worktrees).
2. Keep the change scoped to the ticket. Found an unrelated problem? Note it in a
   new ticket, don't fix it here.
3. Make the necessary changes; record assumptions and decisions you made.
4. Push and open a pull request to `main` using `templates/pr-description.md`.

## Reviewing a PR
Use `templates/pr-review.md`. Post the filled review as a comment on the PR,
save it as an artifact, and attach it to the ticket on Jira.
The review also includes authoring `templates/test-plan.md` (new behaviour +
regression checks + edge cases, derived from the ticket's acceptance criteria
and the diff); post the plan as a PR comment so the tester executes it.
Plan scenarios from the ticket's intent, not from the diff's behaviour —
expected values come from the acceptance criteria, never from what the code
currently does.
While reviewing, note any CLI/shell verification steps worth keeping (build,
seed, smoke-test scripts): list them under "Scripts to keep" in the review.
Repeatedly re-derived verification commands are a signal the repo is missing
a permanent script.
1. Check the PR against its ticket: every acceptance criterion met, nothing extra
   smuggled in.
2. Check the change against the principles in `README.md` — a correct feature
   that violates a principle is a reject.
3. Verify tests: do they exist for the behaviour changed, and do they actually
   fail without the change?
4. Review for scoped, minimal diffs: no drive-by refactors, reformatting, or
   unrelated renames.
5. Leave comments as concrete requests (what to change and why), not verdicts.
   Approve, request changes, or reject with reasons tied to the points above.

## Testing a PR
Execute `templates/test-plan.md` — authored by the reviewer and posted as a PR
comment — with `templates/test-report.md`, covering every planned scenario.
Post the filled report as a comment on the PR, save it as an artifact, and
attach it to the ticket on Jira.
1. Run the full build and test suite on the PR branch; report real output, not
   assumptions.
2. Exercise the ticket's behaviour end-to-end the way the learner would (write a
   composition, trigger review, etc.), not just the unit-tested paths.
3. Probe edge cases the developer likely skipped: empty state, first-run,
   unicode/Chinese input, and boundary HSK levels.
4. Report results on the PR: what you ran, what passed, what failed, with enough
   detail (command, input, expected vs actual) to reproduce a failure.
5. A PR is test-passed only when build, suite, and the end-to-end walkthrough
   all pass. Otherwise request changes with the failing details.

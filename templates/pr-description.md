# PR description template

Copy into the PR body when opening a pull request. Fill every section; write
`None` rather than deleting a section.

---

## SHU-<ticket-id>: <one-line summary>

**Ticket:** [SHU-<id>](<jira-url>)

### What changed
- <bullet per meaningful change; reference files/modules>

### Why
<The problem or need, in a sentence or two — what does this look like on the ticket?>

### Acceptance criteria
- [ ] <criterion from the ticket, verbatim>
- [ ] <criterion>

### Assumptions & decisions
- <Assumption made or decision taken, and why. Include anything a reviewer
  should double-check.>

### Verification
- <Command + result proving the change works, e.g. `dotnet test` output summary,
  screenshots of the behaviour, curl calls>

### Not in this PR
- <Explicitly out-of-scope items, follow-up tickets filed (with IDs)>

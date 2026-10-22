# Board cache (local Jira mirror)

`board/` is a local, file-based cache of the Jira board **SHU** so agents can read
and update tickets without hammering the Jira MCP server (which is currently
unstable). One markdown card per ticket + `INDEX.md`.

## Rules for agents

1. **Read from `board/`, not Jira.** Unless the user asks for fresh data or the
   card's `updated` stamp is older than the work you're about to base on it,
   `board/INDEX.md` is the board. `Idea`-status and `Manual`-labelled tickets are
   not ready; everything else is fair game.
2. **Writes go to the card, not Jira.** Append op lines under the card's
   "Pending changes" section and set `dirty: true` in its frontmatter.
   Valid ops, applied in order on flush:
   - `- transition: <status name>` — also update the frontmatter `status:` to match
   - `- comment: <markdown text>`
   - `- artifact: <absolute path>` — file to attach on flush
   - `- label-add: <label>` / `- label-remove: <label>`
3. **Only the flush touches Jira.** Don't call Jira write tools to "save time";
   that defeats the cache and the server is flaky. Never re-pull while any card
   is `dirty: true` — you'd wipe unflushed ops.
4. Update `INDEX.md`'s Status/Dirty columns when you change a card.

## Pull (refresh from Jira)

```bash
python3 board/scripts/pull.py <search_issues_result.json>
```

An agent with the Jira connector runs `SEARCH_ISSUES` (project SHU, ~100 max),
saves the JSON to a temp file, and runs the script. Cards and INDEX regenerate
in place. Refuses to make sense while cards are dirty — check first.

Only actionable tickets become cards: issues with status `Ideas` and Epics are
skipped (Epics live only in Jira; an Ideas ticket gets a card on the pull after
it moves to Ready For Work). Cards dropped from the pull result are deleted,
except dirty ones, which are kept so their pending ops survive to the flush.

## Flush (push local writes to Jira)

An agent with the Jira connector does, for each card with `dirty: true`, in op
order:

- `transition` → `TRANSITION_ISSUE`
- `comment` → `ADD_COMMENT`
- `artifact` → `ADD_ATTACHMENT`
- `label-add`/`label-remove` → `EDIT_ISSUE`

Then verify with `GET_ISSUE`, clear the pending section, set `dirty: false`,
update `updated:` stamp, and correct the INDEX row. If Jira is down (as it is
now), the flush simply waits — nothing is lost, ops live in the cards.

## Known limitation

Attachments can't be pulled into cards; artifacts flow one way (local → Jira).
Comments made directly in Jira won't appear here until the next pull.

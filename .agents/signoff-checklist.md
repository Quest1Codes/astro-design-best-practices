# Human Sign-off Checklist

## Role

This is not an AI agent stage — it's the mandatory human gate before anything moves from `.work/{topic-id}/` into `skills/astro-design-best-practices/reference/{cluster}/{topic}.md`. Given this content is partner/customer-facing (Astronomer, and any customer who eventually queries it via MCP), nothing merges without a named person having actually done this checklist — not skimmed the Critic's verdict and rubber-stamped it.

## When Invoked

Final stage, after Critic produces `critic-output.md` with verdict `PASS`. If verdict is `FAIL`, do not start this checklist — send it back per the Critic's recommendation first.

## Checklist

- [ ] Read `critic-output.md` in full. Confirm verdict is `PASS` and the "Unsourced claims" list is genuinely empty (spot check — don't just trust the label).
- [ ] For every row in "Execution-check-required items": **actually run it.** Spin up `astro dev start` (or the relevant real environment) and confirm the claimed behavior. Record the command and result inline in this checklist's notes for this topic — a claim that "should be true" and a claim that was "run on {date} and confirmed" are not the same thing, and only the second is mergeable.
- [ ] Spot-check 2-3 tier-1/2 citations from `research-output.md` — open the actual source, confirm it says what's claimed. This catches a Researcher that mis-cited or over-generalized a source.
- [ ] Confirm the draft's axis coverage table looks complete against `tasks/README.md`'s relevance matrix for this topic.
- [ ] Confirm file size is within budget (~4,000-6,000 characters) — check `generator-output.md`'s "Size check" section.
- [ ] For every item in the fact-sheet's `Known gaps` section: confirm it was actually escalated per `AGENTS.md`'s escalation path — either resolved by an exec-check above, escalated to tier-3 (`SETUP-5`), or explicitly labeled `PRACTITIONER JUDGMENT — not independently verifiable from public sources as of {date}` in the shipped file. A gap that was just logged and left unresolved is not mergeable — decide which path it took, on the record.
- [ ] If a topic's real coverage turns out too thin even after escalation, it's fine to ship a shorter file, or to defer specific claims rather than the whole topic — do not pad weak material just to look complete. Note the decision either way.
- [ ] If anything above fails: set `human-signoff = CHANGES_REQUESTED` in `status.md`, note the specific issue, and route back (Researcher if it's a sourcing/execution problem, Generator if it's a drafting/fidelity problem).
- [ ] If everything passes: set `human-signoff = APPROVED`, then:
  1. Copy the (possibly critic-revised) draft to `skills/astro-design-best-practices/reference/{cluster}/{topic}.md`
  2. Copy the fact-sheet to `research/{topic}.md` (this is the permanent audit trail — do not skip, it's what the next Astro Runtime release's re-verification pass will use)
  3. Update `skills/astro-design-best-practices/SKILL.md`'s Reference Files index with a one-line description of the new file
  4. Commit, with the sign-off name in the commit message

## Rules

1. **"The Critic said PASS" is not sign-off.** The Critic checks traceability to the fact-sheet; it cannot run code or judge whether a citation is actually being read correctly. That's what this human stage exists to add.
2. **Record what you actually ran**, not what you intend to run later. An execution-check item without a recorded result is not resolved.
3. **Named accountability.** Every merged file should be traceable to a person who signed off on it, not just "the pipeline."

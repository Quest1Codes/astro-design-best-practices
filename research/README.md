# Research

Permanent, version-controlled sourced fact-sheets — one per shipped topic in
`skills/astro-design-best-practices/reference/`. Populated at Human Sign-off
(see `.agents/signoff-checklist.md`) by copying the approved
`.work/{topic-id}/researcher-output.md`.

This is **not** the same as `.work/` (gitignored, transient pipeline
coordination). These files are the durable audit trail: when Astro Runtime
ships a new release and a maintenance pass needs to know what to re-verify,
this is what it reads — not the finished prose in `skills/`, which doesn't
carry citations in a re-checkable form on its own.

Naming convention: `{topic}.md`, matching the reference file it backs, e.g.
`scheduler-and-dag-design.md` backs
`skills/astro-design-best-practices/reference/scheduler-and-dag-design.md`.

Empty until the first Phase 2 task (`tasks/007` onward) completes Human Sign-off.

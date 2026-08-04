# Astro Design Best Practices

Quest1's Astronomer-partner skill library for AutoSys → Astronomer/Airflow migrations. This is a **content repo**: Claude-Code-style skills (`SKILL.md` + `reference/*.md` + `scripts/`) meant to stand on their own as a production-grade knowledge base — usable directly via Claude Code or any CLI agent — before anyone wires them into a specific consumer.

## What's here

- **`skills/migrating-autosys-to-astronomer/`** and its 3 topology companions (`...-k8s-to-astronomer`, `...-mainframe-boundary-to-astro`, `...-onprem-distributed-to-astro-cloud`) — imported as-is from the mentor's existing work in `shinro`. These cover *migration workflow*: inventory, classification, translation, cutover.
- **`skills/astro-design-best-practices/`** (in progress — this is the actual project) — a new skill covering *target-side architecture design*: 130 topic files across 19 clusters — how to design the Astro/Airflow solution well, not just how to translate a JIL construct. The first 13 clusters (100 topics) came from general reasoning about Astro/Airflow design concerns; 6 more clusters (30 topics, 101-130) were added after actually researching Broadcom's AutoSys documentation, each grounded in a specific real AutoSys mechanism (instance topology, `max_load`/virtual resources, EEM/PAM security, Forecast/`autorep`, native SAP/PeopleSoft/Oracle-EBS agents, container-agent parity) that the first pass had missed or covered too generically. See `tasks/README.md` for the full list.

## Why a separate repo from Shinro

This content needs its own release lifecycle and needs to be reviewable by non-engineers (SMEs, partner content) — bundling it inside one Shinro agent's Python package made both harder. This repo's job stops at producing a verified, sourced knowledge base. **Consuming it — wiring it into Shinro's report generation, an MCP server, or anything else — is explicitly out of scope here** (see `tasks/README.md`'s "Explicitly out of scope" section); that's separate downstream work for whichever project ends up consuming this one, once it exists.

## How content gets built here

Every reference file goes through a 4-stage pipeline — see `AGENTS.md` for the full definition:

```
Researcher → Human Source Check (gate) → Generator → Critic → Human Sign-off (gate)
```

The short version of why: research-then-write with no verification step is how you get confidently-wrong content. Every claim traces to a ranked, cited source; a fresh-context Critic checks the draft against that source before a human does a final execution-verified sign-off.

## Where to start

- `AGENTS.md` — the pipeline, the design principles (why axes split into "companion skill" vs. "decision table inside a file"), and how to actually run each stage
- `tasks/README.md` — the phased roadmap, the axis relevance matrix, and the task tracker
- `research/` — permanent sourced fact-sheets per shipped topic (the maintenance audit trail)

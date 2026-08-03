# Astro Migration Skills

Quest1's Astronomer-partner skill library for AutoSys → Astronomer/Airflow migrations. This is a **content repo**: Claude-Code-style skills (`SKILL.md` + `reference/*.md` + `scripts/`) meant to be usable directly (via Claude Code or any CLI agent), consumed by Shinro's assessment-report generation, and eventually served by an MCP server to any MCP-compatible client.

## What's here

- **`skills/migrating-autosys-to-astronomer/`** and its 3 topology companions (`...-k8s-to-astronomer`, `...-mainframe-boundary-to-astro`, `...-onprem-distributed-to-astro-cloud`) — imported as-is from the mentor's existing work in `shinro`. These cover *migration workflow*: inventory, classification, translation, cutover.
- **`skills/astro-design-best-practices/`** (in progress) — a new skill covering *target-side architecture design*: how to design the Astro/Airflow solution well (scheduler/DAG design, executor/worker architecture, metadata DB, security/multi-tenancy, observability, CI/CD topology, secrets, HA/DR, regulatory/compliance) rather than just how to translate a JIL construct.

## Why a separate repo from Shinro

This content needs its own release lifecycle, needs to be reviewable by non-engineers (SMEs, partner content), and is meant to be consumed by more than one thing (Shinro today, an MCP server eventually) — bundling it inside one Shinro agent's Python package made all three harder. Shinro is a **consumer** of this repo, not its origin.

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

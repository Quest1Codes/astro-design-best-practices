# Astro Migration Skills — Task List

### Roadmap for building the `astro-design-best-practices` skill (and maintaining the 4 imported companion skills) via the Researcher → Generator → Critic → Human Sign-off pipeline defined in `AGENTS.md`

---

## Overview

This folder tracks the roadmap in the same convention as other Quest1 projects: numbered task files with Description/Deliverables/Acceptance Criteria/Dependencies, a phase table, and a task tracker. Unlike a software project, most tasks here are **content-pipeline runs** (execute `AGENTS.md`'s 4-stage pipeline for one topic) rather than code changes — but they follow the same discipline: no task starts before its dependencies are `MERGED`, and every task has a binary-checkable Acceptance Criteria list.

Tasks are grouped into phases. Phases 0-1 are foundational and mostly sequential. Phase 2 tasks (one per topic's baseline content) can run in parallel once Phase 1 is complete, since each targets an independent file. Phase 3 (axis branches) depends on its parent Phase 2 task only.

---

## Phase 0 — Repo Foundation

**Goal**: Scaffolding, imported companion skills, agent role definitions, and the axis relevance matrix that Phase 2+ tasks depend on.

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 001 | [Repo Scaffolding + Agent Pipeline Definitions](001-repo-scaffolding-and-agent-pipeline.md) | P0 | None | DONE |
| 002 | [Import Mentor-Authored Companion Skills](002-import-companion-skills.md) | P0 | 001 | DONE |
| 003 | [Axis Relevance Matrix](003-axis-relevance-matrix.md) | P0 | 001 | DONE (this file, below) |
| 004 | Seed Source List (tier 1/2 URLs per topic) | P0 | 003 | NOT STARTED |
| 005 | Tier-3 Partner Material Ingestion Path | P1 | 003 | NOT STARTED |

**Exit criteria**: New topic work in Phase 2 can start without re-deriving the axis classification, source policy, or pipeline mechanics — all of it is documented and referenceable.

---

## Phase 1 — `astro-design-best-practices` Skill Scaffold

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 006 | Create `skills/astro-design-best-practices/SKILL.md` manifest (empty Reference Files index, filled in as Phase 2 tasks complete) | P0 | 003 | NOT STARTED |

---

## Phase 2 — Baseline Topic Content (one task per reference file, axis-free)

Each task = one full run of the 4-stage pipeline for that topic's **default** guidance only (no axis branches yet — those are Phase 3). Parallel-safe once Phase 0-1 are `MERGED` — each targets an independent file.

| # | Topic → reference file | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 007 | `scheduler-and-dag-design.md` | P0 | 004, 006 | NOT STARTED |
| 008 | `executor-and-worker-architecture.md` | P0 | 004, 006 | NOT STARTED |
| 009 | `metadata-db-and-state-design.md` | P1 | 004, 006 | NOT STARTED |
| 010 | `security-and-multitenancy-design.md` | P0 | 004, 006 | NOT STARTED |
| 011 | `observability-and-alerting-design.md` | P1 | 004, 006 | NOT STARTED |
| 012 | `cicd-and-environment-topology.md` | P0 | 004, 006 | NOT STARTED |
| 013 | `config-and-secrets-design.md` | P1 | 004, 006 | NOT STARTED |
| 014 | `ha-and-dr-design.md` | P1 | 004, 006 | NOT STARTED |
| 015 | `regulatory-and-compliance-design.md` | P0 | 004, 006 | NOT STARTED |

**Priority rationale**: scheduler, executor, security, CI/CD topology, and regulatory-compliance are P0 — these are the ones every migrating customer conversation touches early, and (per the earlier financial-services signal in the existing test fixtures) security/multitenancy and regulatory-compliance are load-bearing for the likely first vertical.

**Exit criteria**: All 9 baseline files exist in `skills/astro-design-best-practices/reference/`, each Critic-verified and Human-signed-off, `SKILL.md`'s index updated.

---

## Phase 3 — Axis-Branch Layering

One follow-on task per **populated cell** in the relevance matrix below (Section "Axis Relevance Matrix") — e.g. `007a` = "add estate-scale branching to `scheduler-and-dag-design.md`". Not enumerated individually here yet (would be ~25-30 small tasks per the matrix) — each gets its own task file, numbered `{parent}a`, `{parent}b`, ... as it's started, mirroring the PACT `003a`/`004b` convention. Do not batch multiple axes into one task — each is independently sourced and verified.

**Dependency rule**: `NNNx` depends only on `NNN` being `MERGED` (the baseline file must exist before a branch can be added to it).

---

## Phase 4 — Pilot Integration into Shinro

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 040 | Wire `astro-design-best-practices` into Shinro's `skill_loader.py` bundle (alongside the existing `autosys-astronomer-expert` report-narrative skill) | P0 | All Phase 2 tasks | NOT STARTED |
| 041 | Generate a real report with the new skill loaded; confirm narrative quality improvement and no PDF/formatting regression | P0 | 040 | NOT STARTED |

**Exit criteria**: A real assessment report references concrete Astro architecture guidance (not just AutoSys→Airflow construct translation) and reads as sharper/more specific than before this skill existed.

---

## Phase 5 — MCP Packaging

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 050 | Design MCP resource/tool interface for this skill corpus | P1 | 041 | NOT STARTED |
| 051 | Implement MCP server exposing `skills/` as resources (+ optional `get_design_guidance` tool) | P1 | 050 | NOT STARTED |
| 052 | Verify Shinro and the MCP server both read the same corpus with no fork | P1 | 051 | NOT STARTED |

**Exit criteria**: Any MCP-compatible client (not just Shinro) can query this skill content directly.

---

## Phase 6 — Maintenance Cadence

| # | Task | Priority | Dependencies | Status |
|---|------|----------|---------------|--------|
| 060 | Define quarterly re-verification trigger tied to Astro Runtime release notes | P2 | 041 | NOT STARTED |

---

## Axis Relevance Matrix

Rows = the 9 `astro-design-best-practices` topics. Columns = the 7 decision-table axes (see `AGENTS.md` Design Principles #2 for why these are branches-within-a-file, not separate skills). **H** = high relevance (a real decision table needed), **M** = medium (worth a short branch/callout), **L** = low (note "checked, no branch needed" and move on) — not blank, per the Critic's axis-coverage check.

| Topic | Deployment model (A) | Estate scale (B) | Migration temporal (C) | Org model (D) | Vertical/compliance (E) | Executor substrate (F) | Integration surface (G) |
|---|---|---|---|---|---|---|---|
| `scheduler-and-dag-design` | L | **H** | M | L | L | L | L |
| `executor-and-worker-architecture` | **H** | **H** | L | M | L | **H** | L |
| `metadata-db-and-state-design` | **H** | **H** | L | L | M | L | L |
| `security-and-multitenancy-design` | **H** | **H** | L | **H** | **H** | L | M |
| `observability-and-alerting-design` | M | M | L | L | M | L | **H** |
| `cicd-and-environment-topology` | **H** | **H** | **H** | **H** | M | L | L |
| `config-and-secrets-design` | **H** | M | L | M | **H** | L | L |
| `ha-and-dr-design` | **H** | M | L | L | M | L | L |
| `regulatory-and-compliance-design` | M | L | L | L | **H** | L | M |

**How to read this for Phase 3 planning**: only **H** cells are near-term follow-on tasks; **M** cells are a short callout, often addressable inside the Phase 2 baseline task itself rather than a separate Phase 3 task; **L** cells just need the Critic's axis-coverage table to record "checked, no branch needed" — no task required.

---

## Task Tracker

Status legend: `NOT STARTED` | `IN PROGRESS` | `IN REVIEW (Critic)` | `IN SIGN-OFF` | `MERGED` | `BLOCKED`

| # | Task | Phase | Status | Owner | Notes |
|---|------|-------|--------|-------|-------|
| 001 | Repo Scaffolding + Agent Pipeline Definitions | 0 | MERGED | — | AGENTS.md, .agents/*.md, directory structure |
| 002 | Import Mentor-Authored Companion Skills | 0 | MERGED | — | 4 skills copied from shinro, flattened out of the nested `skills/skills/` path |
| 003 | Axis Relevance Matrix | 0 | MERGED | — | See matrix above |
| 004 | Seed Source List | 0 | NOT STARTED | — | Blocks all Phase 2 tasks |
| 005 | Tier-3 Partner Material Ingestion Path | 0 | NOT STARTED | — | |
| 006 | `astro-design-best-practices` SKILL.md scaffold | 1 | NOT STARTED | — | |
| 007-015 | Phase 2 baseline topics (9) | 2 | NOT STARTED | — | Parallel-safe once 004, 006 merged |
| 040-041 | Shinro pilot integration | 4 | NOT STARTED | — | |
| 050-052 | MCP packaging | 5 | NOT STARTED | — | |
| 060 | Maintenance cadence | 6 | NOT STARTED | — | |

---

## Summary

- **9 baseline topic tasks** (Phase 2) + an estimated **~15-20 axis-branch follow-ons** (Phase 3, only for H/M cells) + foundation/integration/MCP/maintenance tasks
- **4 companion skills imported** as-is from the mentor's existing work (`migrating-autosys-to-astronomer` + 3 topology companions) — unchanged, not regenerated by this pipeline
- **1 new skill** (`astro-design-best-practices`) is what Phases 1-3 build
- Every topic task runs the same 4-stage pipeline: `AGENTS.md` is the single source of truth for *how*; this file is the source of truth for *what, in what order*

## Source Documents

- `AGENTS.md` — pipeline definition, design principles, agent role files in `.agents/`
- `research/` — permanent per-topic fact-sheets, populated as Phase 2/3 tasks complete

# Astro Migration Skills — Agent Team Workflow

### Multi-agent pipeline for producing production-grade, MCP-attachable Astro/Airflow design-best-practice skill content, sourced from AutoSys migration work · CLI-agnostic

---

## Overview

This repo is the canonical home for Quest1's Astronomer-partner skill library: Claude-Code-style skills (`SKILL.md` + `reference/*.md` + `scripts/`) that give production-grade design and architecture guidance for migrating AutoSys estates to Astronomer/Airflow. It is a **content asset**, not an application — the "build" is markdown, not code, but it gets the same rigor as PACT's software pipeline because it will eventually be consumed by real customers, by Astronomer as a partner, and by an MCP server that other agents can query directly. Wrong guidance here is a partner-facing/reputational risk, not just a bug.

**Pipeline**: `Researcher → Human Source Check (gate) → Generator → Critic → Human Sign-off (gate)`

Each agent:
1. Reads **only** what it needs for its stage (token-optimized context)
2. Produces a structured Markdown output in `.work/{topic-id}/`
3. That output becomes the **primary input** for the next agent

Two mandatory human gates: one right after research (catch bad sourcing before anything is drafted — cheap to fix here, expensive after drafting), one at the very end (nothing merges into `skills/` without a named human sign-off, and this is where any claim flagged as execution-checkable actually gets executed and confirmed).

**Why this shape, not just "Researcher → Generator"**: a two-stage pipeline has no way to catch (a) the researcher citing a low-authority or stale source, (b) the generator drifting from the research during drafting, or (c) a claim that's asserted in prose but never actually verified against real Airflow/Astro behavior. Each of those needs a distinct check, not a bigger prompt. See "Design Principles" below — this is not incidental structure, it is the actual point of the pipeline.

---

## Design Principles (read before writing anything)

These were established through discussion before this repo existed and should not be re-litigated per topic — they are the constraints every agent role below is built around.

1. **Source-authority ranking, not open crawling.** Every claim traces to a source, ranked: (1) Astronomer official docs / Astro Runtime release notes, (2) Airflow OSS docs / provider source code, (3) Astronomer partner/SA material or conference talks / real case studies, (4) general web. Tier 4 is draft-scaffold only, never a final citation. Some tier-3 material (Astronomer partner/SA content) is not web-crawlable — it needs a manual-ingestion path, not autonomous search.

2. **Two kinds of axis — know which one a new topic is.**
   - **Companion-skill axis** (source topology: mainframe-boundary, on-prem-distributed, containerized/k8s — the 3 skills already in `skills/`): the axis value changes the *migration workflow itself* (new phases, new scripts). These get their own top-level skill.
   - **Decision-table axis** (target deployment model, estate scale, migration temporal strategy, org model, vertical/compliance, executor/compute substrate, integration surface): the axis value changes *which recommendation is right inside an existing phase*, not the phases themselves. These become branch tables **inside** a topic's reference file — never a new skill. Forking a skill per axis value here is the single most likely way this project turns into an unmaintainable pile; don't do it.
   - The test when a new axis candidate comes up: *does this change which phases exist, or just which answer is correct within a phase that stays the same?* First → companion skill. Second → decision table.

3. **Draft the baseline first, per topic; layer axis branches in as separate small follow-on tasks.** A topic file is shippable once its default (axis-free) guidance is sourced and verified. Axis branches get added incrementally afterward, one relevant axis at a time, per the relevance matrix in `tasks/README.md` — not attempted all at once, and not added where the axis doesn't actually change the recommendation (don't manufacture branches to look thorough).

4. **The pipeline runs per *topic* (one reference file), not per axis.** A topic's brief includes which axes are relevant to it (from the relevance matrix) so the Researcher gathers axis-aware facts and the Generator produces one coherent file with branches built in — never spin up independent pipelines per axis and try to reconcile fragments afterward.

5. **Nothing merges without a source trail.** Every reference file ends with a `## Sources` section — not decorative, this is what a future maintenance pass (Astro Runtime ships a new release, a claim needs re-checking) actually uses.

---

## Repository Structure

```
astro-migration-skills/
├── AGENTS.md                 ← This file (orchestration)
├── README.md                 ← Project overview
├── .agents/                  ← Agent role definitions
│   ├── researcher.md         ← Stage 1: sourced fact-sheet
│   ├── generator.md          ← Stage 2: drafts the skill reference file
│   ├── critic.md             ← Stage 3: adversarial fact-check against the fact-sheet
│   └── signoff-checklist.md  ← Stage 4 (human): final gate, executes flagged claims
├── .work/                    ← Runtime pipeline outputs (gitignored)
│   └── {topic-id}/
│       ├── status.md
│       ├── researcher-output.md   (sourced fact-sheet)
│       ├── generator-output.md    (draft reference .md)
│       └── critic-output.md       (verdict + flagged items)
├── research/                 ← Persisted, NOT gitignored — the durable fact-sheet per
│                                shipped topic, kept for future re-verification passes
├── tasks/                    ← Phased roadmap, relevance matrix, task tracker
│   └── README.md
└── skills/                   ← The actual deliverable
    ├── migrating-autosys-to-astronomer/                        (mentor-authored, imported)
    ├── migrating-autosys-k8s-to-astronomer/                    (mentor-authored, imported)
    ├── migrating-autosys-mainframe-boundary-to-astro/          (mentor-authored, imported)
    ├── migrating-autosys-onprem-distributed-to-astro-cloud/    (mentor-authored, imported)
    └── astro-design-best-practices/                            (new — built by this pipeline)
        ├── SKILL.md
        └── reference/               (130 topic files across 19 cluster subdirectories;
                                        see tasks/README.md for the full list — e.g.:)
            ├── scheduler-and-dag/          (13 files, e.g. dag-factory-pattern-for-large-estates.md)
            ├── executor-and-worker/        (11 files)
            ├── metadata-db-and-state/      (8 files)
            ├── security-and-multitenancy/  (10 files)
            ├── observability-and-alerting/ (10 files)
            ├── cicd-and-environment-topology/ (10 files)
            ├── config-and-secrets/         (6 files)
            ├── ha-and-dr/                  (5 files)
            ├── regulatory-and-compliance/  (7 files)
            ├── integration-and-enterprise-mesh/ (6 files)
            ├── migration-execution-and-coexistence/ (4 files)
            ├── cost-and-capacity-governance/ (4 files)
            ├── governance-and-operating-model/ (6 files)
            ├── multi-instance-and-cross-instance/       (5 files — added after researching
            │                                              AutoSys's real instance/CCI model)
            ├── machine-load-and-virtual-resources/      (4 files — from max_load/job_load/
            │                                              virtual-resource mechanics)
            ├── native-security-and-credentials/         (4 files — from EEM/autosys_secure/PAM)
            ├── reporting-and-forecasting/                (3 files — from Forecast/autorep)
            ├── native-erp-and-webservice-agents/          (5 files — from the SAP/PeopleSoft/
            │                                                Oracle EBS/WS-job native agents)
            └── container-native-and-legacy-precision/     (8 files — from AutoSys's own k8s
                                                             container-agent feature + HA mechanics)
```

**On the 101-130 cluster additions**: these came from actually researching Broadcom's AutoSys documentation (see `tasks/README.md`'s per-cluster grounding notes) rather than from the same general-reasoning pass that produced 001-100. This is a live example of Design Principle #1 applied one level up — the topic *taxonomy itself* needed the same source discipline as any individual topic's content, and the first pass hadn't gotten that treatment yet.

**Key rule**: this repo is the source of truth for skill content, and this content's job is to stand on its own as a production-grade knowledge base — not to be built *for* any particular consumer. Shinro (`shinro/apps/api/agents/autosys_astronomer/skill_loader.py`) is one *possible future consumer*, the same way an eventual MCP server would be — wiring either of those up is explicitly **not** part of this project's roadmap (see `tasks/README.md`'s "Explicitly out of scope" section). The 4 skills under `skills/` above were copied in from Shinro's tree as a starting point; Shinro's copies should eventually be treated as the stale ones once this repo is established as canonical, not the other way around.

---

## How to Run the Pipeline

### Prerequisites

- A topic exists in `tasks/README.md`'s relevance matrix (which reference file, which axes apply to it, which phase it's in)
- `.work/` is writable
- Web search/fetch tool access for the Researcher stage

### Step 1: Initialize the Topic Workspace

```bash
mkdir -p .work/{topic-id}
```

Create `.work/{topic-id}/status.md`:

```markdown
# Pipeline Status — {topic-id}

## Topic
- **Reference file**: skills/astro-design-best-practices/reference/{cluster}/{topic}.md
- **Relevant axes**: {list from tasks/README.md relevance matrix}

## Stages
| Stage | Role | Status | Output File |
|-------|------|--------|-------------|
| 1 | Researcher | PENDING | researcher-output.md |
| 1.5 | Human Source Check | PENDING | (review of researcher-output.md) |
| 2 | Generator | PENDING | generator-output.md |
| 3 | Critic | PENDING | critic-output.md |
| 4 | Human Sign-off | PENDING | (merge decision) |

## Pipeline Status: IN_PROGRESS
## Notes
```

Status values: `PENDING → IN_PROGRESS → DONE / BLOCKED / FAILED`. Human gates: `PENDING → APPROVED / CHANGES_REQUESTED`.

### Stage 1: Researcher

```
Read the agent instructions in .agents/researcher.md and execute them for {topic-id}.
Topic: {reference file name + one-line scope, from tasks/README.md}
Relevant axes: {axes list from the relevance matrix}
Write the sourced fact-sheet to .work/{topic-id}/researcher-output.md
```

Update status: `researcher = DONE`.

### Stage 1.5: Human Source Check (MANDATORY gate)

The Generator **must not start** until this gate is `APPROVED`. What the human checks:
- Every fact-sheet entry has a real, dated source and sits at the tier it claims (spot-check a few tier-1/2 citations actually say what's claimed)
- No tier-4 (general web) item is being relied on for anything load-bearing
- Coverage looks complete for the topic's relevant axes — nothing obviously missing

Set `human-source-check = APPROVED` (or `CHANGES_REQUESTED`, with notes, re-running the Researcher) in `status.md`.

### Stage 2: Generator

```
Read the agent instructions in .agents/generator.md and execute them for {topic-id}.
Primary input: .work/{topic-id}/researcher-output.md (the ONLY source of facts — do not add anything not in it)
Style template: skills/*/SKILL.md and an existing reference/*.md file, for format/tone/budget matching
Write the draft to .work/{topic-id}/generator-output.md
```

Update status: `generator = DONE`.

### Stage 3: Critic

```
Read the agent instructions in .agents/critic.md and execute them for {topic-id}.
Draft: .work/{topic-id}/generator-output.md
Fact-sheet: .work/{topic-id}/researcher-output.md (check the draft against this ONLY — do not introduce new research)
Sibling files: skills/astro-design-best-practices/reference/*.md (already-shipped files, for consistency checks)
Write the verdict to .work/{topic-id}/critic-output.md
```

Update status: `critic = DONE`.

### Stage 4: Human Sign-off (MANDATORY gate)

Read `.agents/signoff-checklist.md`. This is where anything the Critic flagged as execution-checkable actually gets run (e.g. `astro dev start` + confirm a claimed CLI/API behavior), not just re-read. Nothing moves from `.work/{topic-id}/generator-output.md` into `skills/astro-design-best-practices/reference/{cluster}/{topic}.md` without this gate set to `APPROVED`.

On approval:
1. Copy the (possibly critic-revised) draft into `skills/astro-design-best-practices/reference/{cluster}/{topic}.md`
2. Copy the fact-sheet into `research/{topic}.md` (permanent, for future re-verification)
3. Update `skills/astro-design-best-practices/SKILL.md`'s Reference Files index
4. Commit

---

## Context Scoping Per Agent

| Agent | Reads | Does NOT read |
|-------|-------|----------------|
| Researcher | Topic brief + relevant axes from `tasks/README.md` | Other topics' fact-sheets, existing skill files (avoid anchoring before gathering) |
| Generator | `researcher-output.md` only + one sibling file for style/format | The open web, other topics' fact-sheets |
| Critic | `generator-output.md` + `researcher-output.md` + sibling shipped files (consistency only) | Nothing beyond those — the Critic's job is to check the draft against *this topic's* research, not to do new research itself |
| Human Sign-off | `critic-output.md` + the draft + ability to run real commands | — |

---

## Failure Handling

- **Researcher produces thin/low-tier sourcing**: Human Source Check sets `CHANGES_REQUESTED`, re-run Researcher with the gap named explicitly.
- **Generator adds unsourced content**: Critic must catch this (its primary job) — flag as `UNSOURCED_CLAIM`, kick back to Generator with the fact-sheet re-emphasized, do not hand-patch the prose yourself.
- **Critic flags an execution-checkable claim**: goes to Human Sign-off, not back to Generator — the claim might be correct, it just needs to be *run*, not rewritten.
- **Sign-off finds the claim doesn't hold up when actually run**: back to Researcher — the source was wrong or version-specific, this is a sourcing failure, not a drafting one.

---

## Model Assignment

| Agent | Suggested model | Why |
|-------|------|-----|
| Researcher | Strong reasoning + live web tool access (e.g. Claude with WebSearch/WebFetch) | Judging source authority/tier is a reasoning task, not a retrieval task |
| Generator | Mid-tier, strict-instruction-following | Pure distillation from a fixed input — fidelity matters more than creativity |
| Critic | Strongest available reasoning, **fresh context** (separate invocation, not the Generator continuing) | Adversarial fact-checking needs to not share the Generator's blind spots — same reason code review works better from a fresh reviewer than self-review |

---

## Definition of Done (per topic file)

A reference file is mergeable when:
- [ ] Every claim traces to a `## Sources` entry, tiered per the Design Principles source-authority ranking
- [ ] File size is within the existing skill budget (~4-6 KB, matching `skill_loader.py`'s per-file guardrail already in use in Shinro)
- [ ] All axes marked relevant to this topic in the `tasks/README.md` matrix are addressed with a decision table (or explicitly noted as "checked, no branch needed")
- [ ] Critic verdict is `PASS` with zero open `UNSOURCED_CLAIM` flags
- [ ] Any `NEEDS_EXEC_CHECK` flag has a recorded confirmation (command run + result) in the Human Sign-off notes
- [ ] A named human has set `human-signoff = APPROVED` in `status.md`

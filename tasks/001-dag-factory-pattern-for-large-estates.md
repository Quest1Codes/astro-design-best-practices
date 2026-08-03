# Task 001 — DAG-Factory Pattern for Large Estates

**Cluster**: 1 — Scheduler & DAG Design
**Priority**: P0
**Status**: NOT STARTED
**Output file**: `skills/astro-design-best-practices/reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md`

---

## Description

An AutoSys estate migrating to Astro can easily carry thousands of JIL job/box
definitions. Hand-writing one Python DAG file per box does not scale past a
few dozen — it becomes unreviewable, drifts from the source JIL, and turns
every schema change into a mass hand-edit. The design-best-practice answer is
a **DAG factory**: workflow definitions kept as data (YAML/JSON, one file per
box, structurally close to the original JIL), plus a small number of Python
modules that read that data at parse time and generate the actual DAG objects.
This topic is the concrete guidance on how to design that factory well —
config schema, code-generation boundaries, testing the generator itself (not
just the generated DAGs), and where this pattern breaks down.

This is rated **P0** because every large-estate AutoSys migration conversation
hits this question early — it is one of the first things a customer's
platform team asks once they see the job count.

## How this task gets built

This is **one topic = one full run of the 4-stage pipeline defined in
`AGENTS.md`** — this task does not get hand-written; it gets produced by
`Researcher → Human Source Check → Generator → Critic → Human Sign-off`,
same as all 100 tasks in this project:

1. **Researcher** gathers a sourced fact-sheet for this topic specifically —
   tier 1 (Astronomer docs on dynamic DAG generation / DAG factories), tier 2
   (Airflow OSS docs on DAG parsing, `airflow/example_dags`, dynamic task
   mapping source), tier 3 (any Astronomer partner material or conference
   talks on DAG-factory patterns at scale), per the source-authority policy.
   Per this cluster's row in the Axis Relevance Matrix (`tasks/README.md`),
   **estate scale (axis B) is rated H** for this cluster — the Researcher
   brief must explicitly gather how the recommendation changes between, say,
   a 500-job estate and a 50,000-job estate (single factory module vs.
   sharded/paginated generation, parse-time budget concerns, etc.). Migration
   temporal strategy (axis C) is rated M — worth a short callout (does the
   factory need to emit both "shadow" and "live" DAG variants during
   coexistence?) but not a full decision table.
2. **Human Source Check** — spot-checks the fact-sheet before drafting starts.
3. **Generator** drafts the actual reference file from the fact-sheet only,
   in the house style (terse rule/decision tables, config-schema examples,
   not prose).
4. **Critic** — fresh-context adversarial check against the fact-sheet.
5. **Human Sign-off** — executes any claim flagged `NEEDS_EXEC_CHECK` (e.g.
   confirming actual DAG-parse-time impact of a factory pattern by running
   `astro dev start` against a generated set of DAGs), then merges.

## Deliverables

- `.work/001/researcher-output.md`, `generator-output.md`, `critic-output.md`,
  `status.md` (transient pipeline artifacts)
- `research/dag-factory-pattern-for-large-estates.md` (permanent fact-sheet,
  copied at sign-off)
- `skills/astro-design-best-practices/reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md`
  (the actual deliverable)
- `skills/astro-design-best-practices/SKILL.md`'s Reference Files index updated
  with a one-line entry for this file

## Acceptance Criteria

(Mirrors `AGENTS.md`'s Definition of Done, applied to this specific topic)

- [ ] Every claim in the shipped file traces to a `## Sources` entry, tiered
      per the source-authority policy
- [ ] File size is within the ~4,000-6,000 character budget
- [ ] The estate-scale (axis B) decision table is present and gives a
      concretely different recommendation at small vs. large scale — not the
      same advice restated
- [ ] The migration-temporal (axis C) callout is present, at minimum as a
      short note (does not need a full table, per its M rating)
- [ ] Critic verdict is `PASS` with zero open `UNSOURCED_CLAIM` flags
- [ ] Any `NEEDS_EXEC_CHECK` flag has a recorded confirmation in the Human
      Sign-off notes
- [ ] A named human has set `human-signoff = APPROVED`

## Dependencies

- SETUP-4 (seed source list — this cluster's seed URLs)
- SETUP-6 (skill scaffold — `reference/scheduler-and-dag/` must exist)

## References

- `AGENTS.md` — the pipeline definition and Design Principles this task follows
- `tasks/README.md` — Cluster 1 topic list and the Axis Relevance Matrix row this task's axis coverage is checked against

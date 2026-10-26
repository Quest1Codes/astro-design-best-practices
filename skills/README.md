# Skills

**Start with `autosys-to-astronomer/SKILL.md`** for any AutoSys-to-Astronomer request — it
triages assessment-vs-migration and routes to the right skill(s) below. Everything in this
directory is either loaded through that router or referenced from within another skill; there
should be no reason to load one of these directly without going through it first, unless you
already know exactly which one you need.

## Router

- `autosys-to-astronomer/` — decides assessment-vs-migration, routes to a topology companion,
  points at the knowledge skills. No scripts of its own.

## Assessment family (produces a document — a report, an estimate, a target-architecture
recommendation; nothing gets written to a target Astro project)

Run in order:

1. `assess-estate-discovery/` — what artifacts to request from the customer/platform team;
   builds the discovery checklist.
2. `assess-estate-inventory/` — parses the JIL export (and any `autorep` text output) into
   `estate_manifest.json`, the single typed artifact every later script reads and enriches.
3. `assess-migration-complexity-scoring/` — MECH/JUDG/REDESIGN/NONE/DECOMMISSION disposition per
   unit, wave proposal.
4. `assess-astro-target-architecture/` — target executor/sizing/cost recommendation, routes into
   `astro-design-best-practices` via `kb-routing.md`.
5. `assess-assessment-report/` — renders the final report from the manifest
   (`--draft`/`--final` split protects human-authored prose from being silently overwritten).

## Migration family (produces a running platform — actual DAGs, an actual Astro buildout, an
actual cutover)

Requires a scored, waved `estate_manifest.json` from the assessment family first (see the
router's Phase 0 for the one small-spike exception).

- `migrate-jil-to-airflow-translation/` — scaffolds DAGs from the manifest
  (`scaffold_dags.py`), translates conditions/calendars, runs the DAG-integrity quality gate.
- `migrate-astro-platform-buildout/` — Workspace/Deployment Terraform skeleton, RBAC mapping from
  exported EEM/native-security policy.
- `migrate-parallel-run-and-cutover/` — parity-cycle reconciliation between AutoSys and Airflow
  run history, the cutover go/no-go gate, decommission checklist.

## Topology companions

Loaded alongside whichever family skill above applies, when the estate matches — an estate can
match more than one:

- `migrate-topology-mainframe-boundary/` — jobs touching mainframe-produced data
  (`ZOS`/`ZOSM`/`ZOSDST`, MFT/Connect:Direct/NDM patterns).
- `migrate-topology-onprem-distributed/` — large on-prem Unix/Windows agent fleets, not yet
  containerized.
- `migrate-topology-k8s/` — the AutoSys Application Server/agents already run on Kubernetes.

These are source-**topology** skills — the axis where the value genuinely changes the migration
workflow itself (`AGENTS.md` Design Principles #2), so each gets its own skill by design.

## Knowledge (loaded on demand, never wholesale)

- `autosys-reference/` — source-side facts: job types, attributes, condition grammar, states,
  commands, machine/security. Every claim cites a page in the ingested AutoSys 12.0 PDF corpus
  (`research/autosys-12.0/*.txt`). Load whenever a "what does AutoSys actually do" question comes
  up; never guess JIL syntax.
- `astro-design-best-practices/` — target-side design guidance, 137 topics across 19 clusters,
  organized as `reference/{cluster}/{topic}.md`. Load **selectively** via
  `assess-astro-target-architecture/reference/kb-routing.md` (inventory signal → topic list), not
  all 137 at once. **Draft status**: only 24 topics are Critic-checked and none are human-signed-off;
  see the provenance table in that skill's `SKILL.md` before treating any claim as verified.

## Shared library (not a skill — imported by scripts across every family above)

- `_lib/autosys_jil/` — the JIL parser, condition/box/calendar models, the Estate manifest
  schema, the generic workflow-state engine, command/credential analysis, `autorep`-output
  parsing, and the registry of job types/attributes/states/events/config params built from the
  ingested AutoSys 12.0 corpus. `pip install -e skills/_lib` once per environment; `cd
  skills/_lib && pytest -q` runs its test suite (140 tests).

## Internal docs

- `docs/` — the refactor's own planning/handoff record (`HANDOFF.md`, `REFACTOR-PLAN.md`,
  `REFACTOR-FILE-SPEC.md`). Not part of the AutoSys-to-Astronomer workflow itself; useful if
  continuing or auditing the refactor that produced everything above.

See `tasks/README.md` for the original build-order tracker and `AGENTS.md` for how KB reference
files get produced.

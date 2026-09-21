---
topic: airflow-2-to-3-in-place-upgrade-constraints
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-18
confidence: cited
signals: []
---

# Airflow 2-to-3 In-Place Upgrade Constraints

This topic is for the brownfield case — an estate that already has an Astro Deployment running
Airflow 2.x (from an earlier phase of this migration, or pre-existing Astro usage) and needs to
move that Deployment to Airflow 3, as distinct from a net-new Airflow 3 Deployment created for
newly-translated AutoSys units. See `brownfield_astro`-tagged topics in this KB for the broader
coexistence context.

> RESOLVED: this file's version numbers have now been independently verified against
> astronomer-docs (`astro/airflow3/upgrade-af3`). The Astro Runtime floor for the in-place Airflow
> 2→3 upgrade is **Runtime 13.7.0 (Airflow 2.11)**; the rollback ceiling is **Airflow 2.11 only**,
> and only from **Runtime 3.0-11+**. Astro has since optimized the in-place upgrade path, reducing
> upgrade times from hours to minutes.

## The general shape of the constraint (higher confidence)

Airflow major-version upgrades (2.x → 3.x) are not simple rolling deploys — they involve:

- **A minimum Astro Runtime floor**: **Runtime 13.7.0 (Airflow 2.11)** must be met before the
  in-place upgrade path is available at all.
- **A "latest patch of 2.x first" rule** — Astronomer's upgrade tooling has historically required
  landing on the newest available Airflow 2.x patch release before attempting the jump to 3.x,
  rather than upgrading directly from an arbitrary older 2.x patch.
- **A metadata-DB schema migration** as part of the upgrade, with associated downtime expectations
  — treat this the same way `db-migration-strategy-across-airflow-upgrades.md` already treats
  major-version upgrades generally: pre-migration checklist, tested against a staging Deployment
  first, not attempted directly against production.
- **A limited rollback window**: once the schema migration has run, rollback is only supported to
  **Airflow 2.11**, and only from **Runtime 3.0-11+** — not to an arbitrary earlier 2.x version.

## Design guidance for the migration plan

- Treat an in-place Airflow 2→3 upgrade of an existing brownfield Astro Deployment as its own
  gated step in the migration plan, with the same rigor as `db-migration-strategy-across-airflow-upgrades.md`'s
  general upgrade checklist — pre-upgrade backup, staging rehearsal, a defined rollback window, and
  an explicit go/no-go decision, not a routine deploy.
- If the estate's DAGs (translated from JIL by this project's own `scaffold_dags.py`, or hand-written)
  were authored directly against Airflow 3 idioms from the start, prefer standing up a **new**
  Airflow 3 Deployment and cutting over via this project's own `migrate-parallel-run-and-cutover`
  workflow, rather than in-place-upgrading an existing 2.x Deployment mid-migration — this avoids
  taking on the in-place upgrade's own risk profile on top of the AutoSys migration's risk profile
  at the same time.
- Reserve the in-place upgrade path specifically for a Deployment that must keep its existing
  DAG history/metadata-DB state (audit/compliance continuity requirements, per
  `regulatory-and-compliance/audit-trail-immutability-design.md`) rather than starting fresh.

## Sources

- [P1] Project-internal — `skills/docs/REFACTOR-FILE-SPEC.md` §4 (original version-number citation, now independently confirmed below)
- [P2] Project-internal — `skills/astro-design-best-practices/reference/metadata-db-and-state/db-migration-strategy-across-airflow-upgrades.md`
- [B1] Astronomer Docs — Upgrade to Airflow 3 on Astro (Runtime 13.7.0/Airflow 2.11 floor; rollback to Airflow 2.11 only, from Runtime 3.0-11+; in-place upgrade times reduced from hours to minutes): https://www.astronomer.io/docs/astro/airflow3/upgrade-af3 (tier 1, confirmed via astronomer-docs verification)

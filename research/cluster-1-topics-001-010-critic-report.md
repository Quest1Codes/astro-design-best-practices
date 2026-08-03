# Critic Report — Topics 001-010 (Cluster 1: Scheduler & DAG Design)

Full output of the fresh-context Critic subagent pass run against all 10 shipped files. All findings below were addressed directly in the shipped files (see `cluster-1-topics-001-010-fact-sheet.md`'s "Critic findings and fixes applied" section for the summary). Preserved here verbatim as the permanent audit-trail record of what was checked and how.

---

## Overall verdict per file (as originally submitted, before fixes)

| File | Verdict | Why |
|---|---|---|
| `dag-factory-pattern-for-large-estates.md` | FAIL | Contains an unmarked, factually wrong technical claim (`paused_as_of_creation` — wrong parameter name); also carries the shared `parsing_processes`/2x-vCPU mis-citation |
| `dag-versioning-and-change-management.md` | PASS WITH NOTES | Core facts all verified accurate; one citation-number mismatch (F2 cited, F1 actually contains the quoted text) |
| `scheduler-ha-and-leader-election.md` | PASS WITH NOTES | Core active-active claims verified accurate; NEEDS_EXEC_CHECK properly flagged and transparent |
| `dag-parsing-performance-budget.md` | PASS WITH NOTES | Core mechanics verified; shares the parsing_processes/2x-vCPU wrong-URL citation |
| `taskgroups-vs-separate-dags.md` | FAIL | Load-bearing F1 claim (TaskGroup tasks "inherit `max_active_runs`, pool configuration") is not present on the cited page at all — verified by raw-page fetch |
| `cross-dag-dependencies-...md` | PASS | Dataset→Asset rename and all three-mechanism claims verified accurate |
| `dynamic-task-mapping-design.md` | PASS | `partial()`/`expand()` mechanics verified accurate, including the exact upstream-`.output()` pattern |
| `custom-timetable-design-for-autosys-calendars.md` | PASS | Timetable contract claims are standard, correctly described; not independently disputed |
| `dag-level-sla-and-catchup-backfill-policy.md` | PASS WITH NOTES | The flagged conflict is real and confirmed; one sub-claim (sync callback status) was stale |
| `idempotency-and-retry-design.md` | PASS WITH NOTES | Correctly, transparently hedges its one open question — which turned out to already be resolvable |

## Unsourced or misattributed claims found (all fixed post-review)

1. `dag-factory-pattern-for-large-estates.md` — invented parameter name `paused_as_of_creation` (real name: `is_paused_upon_creation`), no citation at all on the sentence.
2. `taskgroups-vs-separate-dags.md` — the cited Astronomer TaskGroups page (`astronomer.io/docs/learn/task-groups`), fetched and grepped directly, does not contain "pool," "max_active_runs," "concurrency," or "inherit" — the claim was real but the citation didn't support it.
3. `dag-factory-pattern-for-large-estates.md` [F6] and `dag-parsing-performance-budget.md` [F1] both cited `dag-best-practices` for the `parsing_processes`/2x-vCPU guidance; that page (fetched and grepped) contains zero matches for "parsing_processes" or "vCPU." Correct source: `astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro`.
4. `dag-versioning-and-change-management.md` — the verbatim "structural changes include..." quote is on F1 (`learn/airflow-dag-versioning`), was cited as F2 (`astro/dag-versioning`, which only has vaguer phrasing).

## Smuggled facts inside `{syn: ...}` tags

None found. Every `{syn: ...}` block was checked against its listed row IDs; in every case the sentence was logically constructible from just those facts. Noted as a genuine strength of the batch.

**Systemic non-blocking pattern**: several "callout"-style sections (Estate-scale, Migration-temporal, "What NOT to do," etc.) contain synthesis-style prose without a formal `{syn: ...}` tag. None smuggled new facts, but recommended as a house-style cleanup for future batches rather than a per-instance failure.

## Cross-file consistency

No contradictions found. Specifically checked: Assets/Datasets rename consistency, retry/idempotency (only one file covers it, no conflicts), DAG-factory ↔ parsing-performance cross-reference alignment, and the scheduler-HA "2+, up to 4" claim (appears once, properly flagged, not contradicted elsewhere).

## The `alerting-and-sla.md` conflict claim — independently confirmed real

Verified directly (not just trusting the fact-sheet's account) via two live-fetched official Airflow pages:
- `upgrading_to_airflow3.html` breaking-changes section: "SLAs: Deprecated and removed; replaced with Deadline Alerts."
- `deadline-alerts.html`: "Deadline Alerts are new in Airflow 3.1 and should be considered experimental."

`alerting-and-sla.md`'s "Airflow 3: SLA callbacks" is confirmed stale/wrong — the feature was removed, not renamed. The flagging and corrected guidance in `dag-level-sla-and-catchup-backfill-policy.md` is accurate. Minor citation-attachment note applied as a fix (see above).

## An outdated claim caught by live re-fetching

`dag-level-sla-and-catchup-backfill-policy.md` originally stated, unhedged, that Deadline Alerts "currently support only asynchronous callbacks, with synchronous callback support planned but not yet available." A live fetch of the current `deadline-alerts.html` page shows `SyncCallback` support was added in Airflow 3.2, with worked examples. Fixed in place.

## A `NEEDS_EXEC_CHECK` that was already resolvable

`idempotency-and-retry-design.md` flagged the `retry_exponential_backoff` float-multiplier claim as unconfirmed. A live fetch of `astronomer.io/docs/learn/rerunning-dags` — already cited elsewhere in the same file — contains the claim verbatim ("In Airflow 3.2+ you can set `retry_exponential_backoff` to a float..."). Closed; no execution check needed.

## Other spot-checks that came back clean

- Airflow 2.0 scheduler active-active model, shared-metadata-DB coordination.
- `LocalDagBundle` non-versioning vs. Git-backed bundle versioning.
- `partial()`/`expand()` mechanics and the `upstream_task.output` mapping pattern, including code examples.
- Astronomer "2+ schedulers, up to 4" v0.37 guidance — could not re-fetch live (page returned 500 at check time); file already carries its own honest `NEEDS_EXEC_CHECK` flag for this exact staleness risk, so no further action needed from the Critic.

## Final recommendation (as given, before fixes were applied)

7 of 10 files ready for human sign-off as-is with only minor citation-precision notes; 3 of 10 needed a specific named fix before sign-off (all three fixed — see fact-sheet summary). Separately recommended: open a follow-up task to correct `alerting-and-sla.md` itself (confirmed genuinely stale), and noted that the idempotency file's one `NEEDS_EXEC_CHECK` item could be closed immediately using evidence already in-file.

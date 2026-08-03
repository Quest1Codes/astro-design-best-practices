# Worker Queue Segregation Mirroring AutoSys Machine Groups

AutoSys physically segregated jobs by pinning them to specific `machine:` names or machine groups — a job requiring a particular tool, credential set, or resource profile ran on the machine(s) that had it. Airflow's equivalent segregation mechanism under CeleryExecutor is worker queues, and it needs to be designed deliberately, not left as one undifferentiated worker pool.

## Core mechanics

- `queue` is an attribute on `BaseOperator` — any task can be assigned to any queue [F1].
- Celery workers are started listening to one or more named queues (e.g. `airflow celery worker -q spark,quark`) — a worker only picks up tasks from the queues it's listening to [F1].
- The default queue (for both task assignment and worker listening, when unspecified) is set in `airflow.cfg`'s `operators -> default_queue` [F1].
- On Astro specifically, worker queues are a first-class Deployment concept — you can configure multiple worker queues, each with its own resource profile and its own autoscaling min/max worker count [F2].
- Worker queues let you build genuinely different execution environments for different task categories within the same Deployment — e.g. separating resource-intensive tasks from lightweight ones [F2].

## {syn: F1,F2} Design guidance — translating AutoSys machine groups

Enumerate the distinct `machine:` values/groups the source estate actually used, and classify *why* each grouping existed:

| AutoSys machine-grouping reason | Astro worker-queue translation |
|---|---|
| Resource profile (heavy jobs needed a bigger box) | A dedicated worker queue sized with a larger resource profile per worker [F2] — the queue-level resource config directly replaces the machine-level one. |
| Tool/software availability (only some machines had a given client/library installed) | A dedicated worker queue backed by a custom worker image with that tooling installed — this is closer to what the machine pinning was actually expressing than a generic resource-based split. |
| Credential/network-zone isolation (a machine had access to a specific system others didn't) | A dedicated worker queue whose workers run with the specific credentials/network access — do not spread this across a general-purpose queue, since that would broaden access beyond what the source estate deliberately restricted. |
| No real reason beyond historical machine assignment (arbitrary distribution across an undifferentiated fleet) | Default queue — don't manufacture an Astro-side queue split that doesn't correspond to an actual functional distinction in the source estate. |

## What NOT to do

Do not create one worker queue per distinct `machine:` name in the source JIL by default — AutoSys estates commonly have far more named machines than genuine functional categories (many machines existed for capacity/load-balancing reasons, not functional segregation; see the `machine-load-and-virtual-resources` cluster's "virtual machine" load-balancing construct). Queue proliferation without a real functional reason adds operational overhead (more autoscaling groups to tune, more resource profiles to maintain) without a corresponding benefit.

## Sources

- [F1] Apache Airflow docs — Celery Executor (`queue` attribute, worker `-q` flag, `default_queue` config): https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html (tier 2)
- [F2] Astronomer Docs — Configure worker queues (per-queue resource profile + autoscaling, use case for separating task categories): https://www.astronomer.io/docs/astro/configure-worker-queues (tier 1)

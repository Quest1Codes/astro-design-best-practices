# Execution topology: Hosted, Hybrid, or bridge

This is the central decision this skill exists to make, machine group by machine group. Three targets, in order of preference:

## 1. Astro Cloud (Hosted) — the default goal

The job's work can run in a container Astro manages: no dependency on being physically inside the customer's network, no dependency on a specific persistent host's local state. Signs a machine group is Hosted-ready:

- The job's command is a script whose dependencies (interpreters, drivers, libraries) can be packaged into a worker/KubernetesPodOperator image.
- Everything it needs to reach (databases, APIs, file storage) is reachable over the public internet or through a network path that can be opened to Astro's known egress ranges (or via Astro's private connectivity options).
- No dependency on host-specific state (a mapped drive with irreplaceable local files, a machine-bound license, hardware like a card reader).

**Target**: KubernetesPodOperator or standard Astro worker execution, image built to replicate the machine's software dependencies.

## 2. Astro Hybrid — when the network boundary itself is the requirement

The job's work must execute *inside* the customer's own network — not because containerizing the software is hard, but because compliance, data locality, or an internal-only system (no path to expose it, even via firewall rules) requires it. Signs:

- Downstream systems are only reachable from inside the corporate network/VPC (internal-only DNS, no route from outside even with firewall changes).
- A compliance requirement mandates execution stay within a specific network boundary or data residency zone.
- The volume of firewall/network changes required to make a system Hosted-reachable is itself the risk (e.g., opening a mainframe gateway to the internet is a bigger ask than running the worker on-network).

**Target**: Astro Hybrid worker node(s) inside the customer's network; same DAG code as Hosted, different execution location.

## 3. Bridge — the narrow, temporary exception

The job genuinely cannot be containerized or run under Hybrid yet: proprietary Windows-only software with no Linux/container path, a hardware dependency, or a migration timeline that requires keeping a legacy execution point alive past the main cutover. Signs:

- The job's command depends on software with no container-compatible license or build, and no near-term plan to replace it.
- Hardware-bound execution (a physical device attached to the host).

**Target**: a small, explicitly-tracked residual on-prem execution host, invoked from Airflow via `SSHOperator` (Unix) or a WinRM-based equivalent (Windows), rather than a full agent fleet. This is a bridge, not a destination — every bridged job needs a written reason and a revisit trigger (a date, or a condition like "when the vendor ships a Linux build").

## Decision checklist per machine group

1. Can the job's dependencies be containerized? If yes and reachability is solvable → **Hosted**.
2. If containerizable but the network boundary itself is the blocker → **Hybrid**.
3. If not containerizable at all, or blocked by something with no near-term fix → **Bridge**, with a written reason and revisit trigger.

Do not let "it's always worked on that machine" stand in as a reason on its own — ask what specifically about that machine is load-bearing (the software, the network position, or just history) before defaulting to Bridge. Bridge is the expensive long-term answer; it should be earned, not defaulted to.

## Mixed machine groups

A single business process's jobs sometimes span multiple targets (e.g., an extract job that's easily Hosted, feeding a load job that must stay Hybrid because of a compliance-scoped database). This is fine — the DAG can span execution targets per task (`queue=` or per-task executor config); don't force an entire box onto one target just because it was one box in AutoSys.

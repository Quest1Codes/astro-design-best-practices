# Legacy Machine-Type Inventory (Deprecated n/l/L/r Types) → Pre-Migration Cleanup Task

AutoSys machine definitions carry a `type` attribute that specifies the agent technology. The current and only supported agent type is **`a`** (Workload Automation Agent), compatible with UNIX, Linux, Windows, i5/OS, and z/OS [B1]. Legacy machine types `n`, `l`, `L`, and `r` were platform-specific agent designations from AutoSys 4.5.x and r11 eras and are deprecated [B1].

Jobs pointing to machines with deprecated types must be re-pointed or cleaned up **before migration** — otherwise the inventory migration tool will encounter orphaned or invalid machine references.

## Legacy Machine Type Reference

{syn: deprecated machine types `n`/`l`/`L`/`r` → pre-migration cleanup targets}

| Type | Legacy Meaning | Status |
|---|---|---|
| `a` | Workload Automation Agent (all platforms) | **Current — keep** |
| `n` | UNIX agent (NetWare/legacy UNIX direct) | **Deprecated** |
| `l` | Legacy Linux agent | **Deprecated** |
| `L` | Legacy Linux 64-bit agent | **Deprecated** |
| `r` | r11 agent type | **Deprecated** |

## Pre-Migration Cleanup Procedure

### Step 1: Inventory All Machine Definitions

```bash
autorep -M ALL -s > machine_inventory_$(date +%Y%m%d).txt
```

Filter for deprecated types:
```bash
grep -E "\s+(n|l|L|r)\s+" machine_inventory_$(date +%Y%m%d).txt
```

### Step 2: Identify Jobs Still Pointing to Legacy Machines

For each deprecated machine, identify dependent jobs:
```bash
autorep -J ALL -s | grep -i "<deprecated_machine_name>"
```

### Step 3: Re-point Jobs to `a`-type Machines

Update JIL to point jobs to the correct `a`-type Workload Automation Agent machine. Then update the machine definition.

**Important**: You **cannot change a machine type in-place** in AutoSys [B1]. The procedure is:
1. Delete the existing machine definition: `delete_machine: <name>` (use `force: y` if jobs still reference it).
2. Re-create the machine with the correct `type: a` attribute.
3. Re-run the jobs to validate connectivity.

### Step 4: Verify Clean State Before Migration

```bash
autorep -M ALL -s | grep -vE "\s+a\s+"
```

This should return **zero rows** — all machines should be `a`-type before the migration proceeds.

## Why This Matters for Astro Migration

Airflow/Astro has no concept of machine types — execution targets are Airflow Connections (database endpoints, API URLs, SSH hosts). If the AutoSys job inventory contains references to deprecated machine types, the migration tool cannot reliably map them to Airflow Connections. Clean the machine inventory first; then the job-to-DAG migration can proceed with unambiguous execution targets.

## Sources

[B1] Broadcom AutoSys Documentation — Machine `type` attribute values (`a`, `n`, `l`, `L`, `r`); `a`-type as the current Workload Automation Agent standard; machine type cannot be changed in-place; `force: y` for deletion with active job references (accessed 2026-08-18)

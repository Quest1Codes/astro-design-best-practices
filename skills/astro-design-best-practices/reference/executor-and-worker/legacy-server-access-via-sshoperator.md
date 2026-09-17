# Legacy-Server Access via SSHOperator

AutoSys handled "this job must run on that specific host" via `machine:` — a named agent process on a specific box. Some AutoSys jobs genuinely need that forever: a command that only exists on a legacy/vendor appliance, a mainframe-adjacent gateway box, or a server a specific team owns and won't containerize. For those, Astro doesn't run the work itself — it reaches out and runs a command on the remote host, the same way a person would over `ssh`.

## Core mechanics

- `SSHOperator` (`airflow.providers.ssh.operators.ssh`) runs a shell command on a remote host over SSH and streams the output back into the task log; the underlying `SSHHook` (`airflow.providers.ssh.hooks.ssh`) manages the actual connection and can also be used directly inside a `@task`-decorated function for more control (e.g. issuing multiple commands over one connection) [F1].
- The operator/hook resolve their target host and credentials from a standard Airflow **Connection** (`ssh_conn_id`), not a hardcoded host string in the DAG file — this is the direct architectural replacement for `machine:` [F1][F2].
- `execution_timeout` (a `BaseOperator` argument, not SSH-specific) bounds how long Airflow waits for the task overall; `cmd_timeout` on `SSHOperator` specifically bounds the remote command itself [F1][F3]. Set both explicitly — a hung remote process with no timeout blocks a worker slot indefinitely, which is exactly the AutoSys-side risk `max_run_alarm` existed to catch.

## {syn: F1,F2,F4} Connection and credential design

SSH access to a fixed legacy host is architecturally identical to any other credentialed external system Airflow talks to — it should go through the same Secrets Backend path this skill already establishes for AutoSys/PAM credential migration (`reference/native-security-and-credentials/pam-credential-vaulting-to-astro-secrets-backend.md`), not a one-off exception:

| Design choice | Recommendation |
|---|---|
| Where the SSH private key lives | Secrets Backend (Vault / cloud secrets manager), resolved via the same 4-tier lookup (Secrets Backend → Astro Environment Manager → Environment Variables → Metadata DB) already documented for all Astro connections [F2] — not hardcoded in DAG code or checked into the `include/` directory. |
| Connection identity | One `ssh_conn_id` per target host, named for the host/purpose (not shared across unrelated legacy servers), mirroring how AutoSys `machine:` assignment was explicit and auditable per job. |
| Key rotation | Same rotation discipline as any other Secrets-Backend-held credential — see `reference/config-and-secrets/secret-rotation-strategy.md`. |

`NEEDS_EXEC_CHECK`: the exact field layout Airflow's SSH connection type expects in the Astro UI/Connection form (host, port, username, and whether the private key is supplied as key content vs. a key-file path) should be confirmed against the current `apache-airflow-providers-ssh` connection docs on the target Astro Runtime version before scripting connection creation via Terraform/CLI — this file states the *architectural* pattern (Secrets-Backend-resolved Connection), not the exact form-field names.

## When SSHOperator is the right migration answer — and when it's a smell

| Signal | Read |
|---|---|
| A handful of jobs run one or two commands on a fixed legacy host that genuinely can't be containerized or re-platformed in this migration's scope | `SSHOperator` is the correct, durable replacement for that `machine:` pinning — no further action needed. |
| A growing share of an estate's actual business logic lives *on the remote server*, with Airflow reduced to a thin SSH-triggering wrapper around it | {syn: F1} This is a design smell, not a target state — Airflow can't apply its own retry/backfill/observability semantics to work happening entirely outside its control on the remote box; it can only report whether the SSH command exited zero. Treat this as a signal the job (or the remote logic itself) needs re-platforming, not a case for adding more SSH-wrapped tasks. |
| The remote command is long-running and must survive a task retry without re-launching from scratch | Consider Airflow's task state store pattern (store the remote process's PID after launch, reconnect to it on retry instead of re-starting it) [F5] rather than a plain `SSHOperator` call per attempt. |

## Sources

- [F1] Astronomer Docs — Airflow task state store, SSH examples (`SSHHook`, `SSHOperator`, `ssh_conn_id`, `cmd_timeout`, retry/reconnect pattern for long-running remote commands): https://www.astronomer.io/docs/learn/airflow-task-state-store#task-state-store-examples (tier 1)
- [F2] Astronomer Docs — Secrets backend, "How Airflow finds Connections or Variables" (4-tier resolution order): https://www.astronomer.io/docs/astro/secrets-backend#how-airflow-finds-connections-or-variables (tier 1) — same source already cited in `pam-credential-vaulting-to-astro-secrets-backend.md`, kept consistent here.
- [F3] Astronomer Docs — What is an operator, `BaseOperator` common arguments (`execution_timeout`): https://www.astronomer.io/docs/learn/what-is-an-operator#operator-examples (tier 1)
- [F4] Astronomer Docs — Airflow connection basics (Connection precedence: Secrets Backend → Astro Environment Manager → Environment Variables → Metadata DB): https://www.astronomer.io/docs/learn/connections#airflow-connection-basics (tier 1)
- [F5] Astronomer Docs — Airflow task state store overview (PID-reconnect-on-retry pattern for long-running remote jobs): https://www.astronomer.io/docs/learn/airflow-task-state-store (tier 1)

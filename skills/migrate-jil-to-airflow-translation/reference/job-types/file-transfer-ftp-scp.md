---
topic: file-transfer-ftp-scp
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: [credential_hits]
---

# File transfer: FTP, SCP

| Code | Default target | Disposition | Delta |
|---|---|---|---|
| `FTP` | `apache-airflow-providers-ftp`'s transfer operator (or `SFTPToS3Operator`/similar if the destination is object storage, not another filesystem) | MECH once the protocol is confirmed | None expected once attributes map 1:1 to the provider operator's parameters |
| `SCP` | `apache-airflow-providers-sftp`'s operator (SCP itself has no dedicated provider; SFTP is the practical target unless the customer specifically needs SCP's exact protocol behavior) | MECH once the protocol is confirmed | Confirm SFTP is an acceptable substitute for SCP with the platform/security team before assuming it — the protocols are related but not identical |

The mechanics of the transfer are usually mechanical once the protocol is confirmed; **the
protocol confirmation itself is the judgment step** — this job-type family's attributes vary the
most across AutoSys/WA AE versions and shops of any core type (per the pre-refactor skill's own
note, still accurate). **Verify the JIL attribute names against the customer's actual export**
via `Job.extras`/`Instance.unknowns.attributes`, do not assume a fixed attribute set from this
file alone.

## Credentials

FTP/SCP jobs are one of the highest-density sources of embedded credentials
(`command_analysis.py`'s `credential_hits`) — a connection string, `-p password`, or hardcoded
host/user in the command. Route every one through the target secrets backend
(`migrate-astro-platform-buildout/reference/secrets-and-identity.md`), never copy the observed
value forward.

## Cross-machine transfer partners

An FTP/SCP job's counterpart host (source or destination) is a topology signal —
`migrate-topology-onprem-distributed`'s `agent_fleet_inventory.py` flags these explicitly
(`job '<name>' (FTP) references host '<host>' in its command`). Plan the network path for both
ends together, not just the machine the job is nominally scheduled on.

## What the scaffolder emits vs. leaves as TODO

Emits the provider operator call with source/destination/credentials parameterized (credentials
via `# TODO(JUDG:secrets-backend)` referencing a Connection ID, never a literal); leaves
`# TODO(JUDG:protocol-confirm)` if the export's attribute set didn't clearly resolve to a single
known protocol/provider.

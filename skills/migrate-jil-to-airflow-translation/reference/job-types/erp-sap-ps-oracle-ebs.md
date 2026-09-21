---
topic: erp-sap-ps-oracle-ebs
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: [erp_sap]
---

# ERP: SAP family, PeopleSoft, Oracle E-Business Suite

All 12 ERP job types [AS p.2551] score `4pt JUDG flag:erp` (`scoring_rules.yaml`) — deliberately
high, since these are the family most likely to need a specialist review regardless of how
mechanical the underlying call turns out to be.

| Code | System | Default target | Disposition |
|---|---|---|---|
| `SAP` | SAP R/3 | `apache-airflow-providers-sap`'s `SAPRfcHook`-based operator | JUDG |
| `SAPBDC` | SAP Batch Input Session | Same provider, batch-input-specific call | JUDG |
| `SAPBWIP` | SAP BW InfoPackage | Same provider | JUDG |
| `SAPBWPC` | SAP BW Process Chain | Same provider — RFC process-chain start | JUDG |
| `SAPDA` | SAP Data Archiving | Same provider | JUDG |
| `SAPEVT` | SAP Event Monitor | A sensor polling the SAP event, via the same provider | JUDG |
| `SAPJC` | SAP Job Copy | Same provider | JUDG |
| `SAPPM` | SAP Process Monitor | Same provider (sensor-style) | JUDG |
| `PS` (PeopleSoft) | A custom `PeopleSoftProcessOperator` — no first-party Airflow provider exists | JUDG |
| `OASG` / `OASET` / `OACOPY` (Oracle E-Business Suite) | `OracleHook` + `fnd_request.submit_request` | JUDG |

## Why these are all JUDG, never MECH by default

ERP job attribute sets are the least standardized surface in this whole reference set — even more
so than file-transfer. Every one of these needs the actual JIL attributes verified against the
customer's export (`Job.extras`/`Instance.unknowns.attributes`) before assuming a 1:1 attribute
mapping exists; the "default target" column is a starting position for the Researcher/Critic
pipeline to verify, not a guarantee.

## What the scaffolder emits vs. leaves as TODO

Emits a `@task` stub with the relevant provider hook imported and a
`# TODO(JUDG:erp-attribute-mapping)` marker naming the specific unverified attributes found in
this job's export — never a fully-filled-in call for an ERP job without a human confirming the
attribute mapping first.

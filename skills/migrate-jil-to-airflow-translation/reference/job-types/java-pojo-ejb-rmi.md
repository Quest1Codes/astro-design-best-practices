---
topic: java-pojo-ejb-rmi
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Java: POJO, ENTYBEAN, SESSBEAN, JAVARMI

| Code | What it is | Default target | Disposition |
|---|---|---|---|
| `POJO` (Plain Old Java Object) | Runs a Java class's method directly | `KubernetesPodOperator` running the JAR, or `BashOperator java -cp ...` for a simpler case | JUDG |
| `ENTYBEAN` (Entity Bean) | Legacy EJB entity bean invocation | `KubernetesPodOperator` running a wrapper JAR — the EJB container dependency itself may need addressing separately, this is a re-platforming signal worth naming | JUDG |
| `SESSBEAN` (Session Bean) | Legacy EJB session bean invocation | Same as `ENTYBEAN` | JUDG |
| `JAVARMI` (Java RMI) | Remote method invocation over RMI | `KubernetesPodOperator` running a client stub, or `@task` with a Java subprocess call if RMI itself is being retired rather than ported | JUDG |

## `ENTYBEAN`/`SESSBEAN`/`JAVARMI` as modernization signals

These three job types point at a Java EE / RMI architecture that may itself be a candidate for
modernization independent of the AutoSys migration — flag this explicitly in the report as a
scope question for the customer (in scope for this migration, or a separate initiative), rather
than silently containerizing legacy EJB/RMI machinery as-is.

## What the scaffolder emits vs. leaves as TODO

Emits a `KubernetesPodOperator` skeleton with the JAR/classpath parameterized from the JIL
`command`; leaves `# TODO(JUDG:runtime-image)` for the container image build (this refactor does
not attempt to derive a Dockerfile from a JIL `command:` line).

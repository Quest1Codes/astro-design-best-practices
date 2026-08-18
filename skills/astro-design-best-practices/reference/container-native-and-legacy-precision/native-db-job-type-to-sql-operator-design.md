# Native DB Job Type Execution Patterns → Airflow SQL-Operator Design

AutoSys's native DB job type executes SQL statements directly against a database (Oracle, SQL Server, Sybase, PostgreSQL, DB2) without a wrapper shell script — the JIL definition specifies the database connection, SQL command or script file, and success/failure conditions [B1].

In Airflow, the equivalent is the database-specific SQL operators from the provider packages, or the unified `SQLExecuteQueryOperator` [B2].

## Job Type → Operator Mapping

{syn: AutoSys native DB job type → Airflow `SQLExecuteQueryOperator` / `PostgresOperator` / `OracleOperator` / `MsSqlOperator`}

| AutoSys DB Target | Airflow Operator | Provider Package |
|---|---|---|
| **Any (unified)** | `SQLExecuteQueryOperator` | `apache-airflow-providers-common-sql` [B2] |
| **PostgreSQL** | `PostgresOperator` | `apache-airflow-providers-postgres` [B2] |
| **Oracle** | `OracleOperator` | `apache-airflow-providers-oracle` [B2] |
| **SQL Server** | `MsSqlOperator` | `apache-airflow-providers-microsoft-mssql` [B2] |

## SQL Operator Pattern (Recommended)

```python
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

run_finance_sql = SQLExecuteQueryOperator(
    task_id="run_month_end_close",
    conn_id="oracle_finance_prod",
    sql="include/sql/month_end_close.sql",  # External SQL file in project
    parameters={"batch_date": "{{ ds }}"},  # Jinja-templated params
    autocommit=True,
)
```

Store SQL in `include/sql/` directory within the Astro project — never inline long SQL in DAG files [B2].

## JIL → Operator Attribute Mapping

| AutoSys DB Job JIL Attribute | Airflow Equivalent |
|---|---|
| `db_connection_string` | Airflow Connection `conn_id` |
| `sql_command` / `sql_script_file` | `sql` parameter (inline or file path) |
| `max_run_alarm` (timeout) | `execution_timeout` on the task |
| Success based on exit code | `SQLExecuteQueryOperator` raises on non-zero exit; use `handler` for custom success logic |

## Data Quality Extension

AutoSys DB jobs ran SQL and checked exit code for success. Airflow allows extending this pattern with SQL quality checks immediately after the SQL executes [B2]:

```python
from airflow.providers.common.sql.operators.sql import SQLColumnCheckOperator

validate_output = SQLColumnCheckOperator(
    task_id="validate_row_count",
    conn_id="oracle_finance_prod",
    table="month_end_results",
    column_mapping={
        "record_count": {"min": {"geq_to": 1000}},
    },
)
```

This pattern has no AutoSys equivalent — it is Airflow-native value-add.

## Sources

[B1] Broadcom AutoSys Documentation — Native DB job type, `db_connection_string`, `sql_command`, `sql_script_file` JIL attributes (accessed 2026-08-18)
[B2] Apache Airflow Docs — `SQLExecuteQueryOperator`, `PostgresOperator`, `OracleOperator`, `MsSqlOperator`, `SQLColumnCheckOperator`, `sql` parameter file path support (accessed 2026-08-18)

"""AutoSys platform configuration surface: `config.$AUTOSERV` and `agentparm.txt` [plan §11.3].

Deterministic; reads files only (callers pass text).

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §1.10 (config.py spec)
  - PDF p.851-1132 "Administrating" section (`research/autosys-12.0/administration.txt`);
    `key=value` format confirmed at [AS p.853] ("$AUTOUSER/config.$AUTOSERV").
  - `registry/config_params.yaml` (hand-curated overlay: which parameters change migration
    semantics, and how -- see that file's header for why this is curated, not generated).

`agent_capabilities()` is PRACTITIONER JUDGMENT -- not independently verifiable as of
2026-09-17: the agentparm.txt key vocabulary is documented in the separate "Workload Automation
Agents" guide, which is not part of the ingested 12.0 PDF corpus. It matches on substrings of
known plugin/vendor names in keys and values; treat its output as a hint, not a fact.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve().parent
_CONFIG_PARAMS_PATH = _HERE / "registry" / "config_params.yaml"

# PRACTITIONER JUDGMENT: substrings observed in real-world agentparm.txt/plugin deployments,
# not sourced from the ingested PDF (see module docstring). Maps a substring found in an
# agentparm key or value to the job-type family it signals the agent can run.
_PLUGIN_HINTS: dict[str, str] = {
    "oracle": "erp-oracle", "sqlplus": "db", "mssql": "db", "sybase": "db", "db2": "db",
    "sap": "erp-sap", "peoplesoft": "erp-ps", "psft": "erp-ps",
    "ftp": "file-transfer", "sftp": "file-transfer", "scp": "file-transfer",
    "webservice": "web", "soap": "web", "http": "web",
    "hadoop": "hadoop", "hdfs": "hadoop", "hive": "hadoop", "sqoop": "hadoop", "oozie": "hadoop", "pig": "hadoop",
    "informatica": "informatica", "pmcmd": "informatica",
    "snmp": "os-monitor", "jms": "web", "jmx": "web",
    "java": "java", "rmi": "java",
    "zos": "zos", "mainframe": "zos",
}


@lru_cache(maxsize=None)
def config_params() -> dict:
    return yaml.safe_load(_CONFIG_PARAMS_PATH.read_text())


def parse_config_autoserv(text: str) -> dict[str, str]:
    """Parse `$AUTOUSER/config.$AUTOSERV`: `Key=Value` lines, `#` starts a comment [AS p.853].

    Unlike JIL (where `#` is NOT a comment -- see lexer.py), the config file uses `#` comments,
    same as a standard shell-style properties file.
    """
    out: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = re.sub(r"\s+#.*$", "", s)  # trailing comment after a value
        if "=" not in s:
            continue
        key, _, value = s.partition("=")
        out[key.strip()] = value.strip()
    return out


def parse_agentparm(text: str) -> dict[str, str]:
    """Parse `agentparm.txt`: `key=value`, java-properties style (`#` and `!` both comment)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("!"):
            continue
        if "=" not in s:
            continue
        key, _, value = s.partition("=")
        out[key.strip()] = value.strip()
    return out


def semantic_params(cfg: dict[str, str]) -> dict[str, dict]:
    """Subset of `cfg` that appears in the curated `config_params.yaml` overlay, each entry
    enriched with its documented default/translation_effect. Unknown keys are dropped here
    (they still round-trip through `Instance.config`, which holds the raw dict unfiltered)."""
    overlay = config_params()
    out: dict[str, dict] = {}
    for key, raw_value in cfg.items():
        spec = overlay.get(key)
        if spec is None:
            continue
        out[key] = {
            "value": raw_value, "pdf_page": spec.get("pdf_page"),
            "default": spec.get("default"), "description": spec.get("description"),
            "translation_effect": spec.get("translation_effect"),
        }
    return out


def agent_capabilities(agentparm: dict[str, str]) -> set[str]:
    """Job-type families an agent's plugins suggest it can run (PRACTITIONER JUDGMENT; see
    module docstring). Scans both keys and values for known plugin/vendor substrings."""
    haystack = " ".join(f"{k} {v}" for k, v in agentparm.items()).lower()
    return {family for needle, family in _PLUGIN_HINTS.items() if needle in haystack}

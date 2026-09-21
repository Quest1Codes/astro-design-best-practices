"""`command:` string payload analysis -- interpreter detection, hidden control flow, environment
coupling, credential exposure, and template clustering [plan §11.2].

Deterministic: given identical command text and pattern version, output is byte-identical.
No I/O beyond reading the versioned pattern file at import time; never executes the command.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §1.9 (commands.py spec)
  - skills/docs/REFACTOR-PLAN.md §11.2 (command payload analysis: the command string is the
    real workload; the plan only counted it before)
  - `commands_patterns.yaml` in this package (the versioned, Critic-reviewable pattern library)
"""
from __future__ import annotations

import hashlib
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve().parent
_PATTERNS_PATH = _HERE / "commands_patterns.yaml"


def load_patterns() -> dict:
    return yaml.safe_load(_PATTERNS_PATH.read_text())


_P = load_patterns()
# Whether a pattern is anchored (`^...`, an explicit leading interpreter token like `bash x.sh`)
# vs. unanchored (an extension match embedded in the script-path token itself, e.g. `x.sh` with
# no separate interpreter word) matters for _script_path_and_args: only the anchored case means
# the interpreter occupies its own token that should be skipped.
_INTERPRETERS = [(p["name"], re.compile(p["pattern"]), p["pattern"].startswith("(?i)^"))
                 for p in _P["interpreters"]]
_GLOBAL_VAR_RE = re.compile(_P["global_var_ref"]["pattern"])
_HOSTS_RE = re.compile(_P["hosts"]["pattern"])
_IPS_RE = re.compile(_P["ips"]["pattern"])
_ABS_PATH_RE = re.compile(_P["abs_paths_unix"]["pattern"])
_UNC_RE = re.compile(_P["unc_paths"]["pattern"])
_MAPPED_DRIVE_RE = re.compile(_P["mapped_drives"]["pattern"])
_OS_WIN_RE = re.compile(_P["os_hint_windows"]["pattern"])
_OS_UNIX_RE = re.compile(_P["os_hint_unix"]["pattern"])
_HIDDEN = _P["hidden_control_flow"]
_CREDENTIAL_PATTERNS = {
    name: (re.compile(spec["pattern"]), spec["group"]) for name, spec in _P["credential_patterns"].items()
}
_NORMALIZE = [(re.compile(p["pattern"]), p["placeholder"]) for p in _P["normalize_placeholders"]]


def credential_patterns() -> dict[str, tuple[re.Pattern, int]]:
    """The canonical (regex, secret-group-index) map, reused verbatim by manifest.redact()."""
    return dict(_CREDENTIAL_PATTERNS)


@dataclass(slots=True)
class HiddenEdge:
    kind: str  # sendevent / autorep / jil / autosyslog
    event: str | None
    job: str | None
    raw: str


@dataclass(slots=True)
class CredentialHit:
    pattern: str
    span: tuple[int, int]  # offsets in the ORIGINAL command string; value never captured here


@dataclass(slots=True)
class CommandAnalysis:
    raw: str
    interpreter: str  # one of the interpreters.yaml names, or "unknown"
    script_path: str | None
    args: list[str] = field(default_factory=list)
    global_var_refs: list[str] = field(default_factory=list)
    hidden_control_flow: list[HiddenEdge] = field(default_factory=list)
    hosts: list[str] = field(default_factory=list)
    ips: list[str] = field(default_factory=list)
    abs_paths: list[str] = field(default_factory=list)
    unc_paths: list[str] = field(default_factory=list)
    mapped_drives: list[str] = field(default_factory=list)
    credential_hits: list[CredentialHit] = field(default_factory=list)
    os_hint: str = "unknown"  # windows | unix | unknown
    normalized: str = ""
    template_hash: str = ""

    def as_dict(self) -> dict:
        return {
            "interpreter": self.interpreter, "script_path": self.script_path, "args": self.args,
            "global_var_refs": self.global_var_refs,
            "hidden_control_flow": [
                {"kind": h.kind, "event": h.event, "job": h.job, "raw": h.raw}
                for h in self.hidden_control_flow
            ],
            "hosts": self.hosts, "ips": self.ips, "abs_paths": self.abs_paths,
            "unc_paths": self.unc_paths, "mapped_drives": self.mapped_drives,
            "credential_hits": [{"pattern": c.pattern, "span": list(c.span)} for c in self.credential_hits],
            "os_hint": self.os_hint, "normalized": self.normalized, "template_hash": self.template_hash,
        }


def _detect_interpreter(command: str) -> tuple[str, bool]:
    """Returns (name, is_explicit_token) -- see _INTERPRETERS' anchoring comment above."""
    for name, pat, anchored in _INTERPRETERS:
        if pat.search(command):
            return name, anchored
    return "unknown", False


def _tokenize_command(command: str) -> list[str]:
    """Quote-aware split so a quoted multi-word argument (a paging message, a SQL string) is
    one token, not several -- a naive .split() here previously mistook the first word of a
    quoted argument for the script path whenever it followed an explicit interpreter token."""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # unbalanced quotes or similar -- fall back to a naive split rather than raising,
        # since assessment input is real-world messy JIL, not a controlled grammar.
        return command.strip().split()


def _script_path_and_args(command: str, interpreter: str, explicit_token: bool) -> tuple[str | None, list[str]]:
    tokens = _tokenize_command(command)
    if not tokens:
        return None, []
    idx = 0
    # Only skip a token when the interpreter occupies its OWN token (`bash x.sh`, `cmd /c x.bat`)
    # -- an extension-based match (`x.sh` with no separate interpreter word) means tokens[0] IS
    # the script path already.
    if interpreter == "cmd" and len(tokens) >= 2 and tokens[1] == "/c":
        idx = 2
    elif explicit_token:
        idx = 1
    if idx >= len(tokens):
        return None, []
    return tokens[idx], tokens[idx + 1:]


def _detect_os_hint(command: str) -> str:
    if _OS_WIN_RE.search(command):
        return "windows"
    if _OS_UNIX_RE.search(command):
        return "unix"
    return "unknown"


def _hidden_control_flow(command: str) -> list[HiddenEdge]:
    out: list[HiddenEdge] = []
    for kind, spec in _HIDDEN.items():
        for m in re.finditer(spec["pattern"], command):
            snippet = m.group(0)
            event = job = None
            if "event_flag_pattern" in spec:
                em = re.search(spec["event_flag_pattern"], snippet)
                event = em.group(1) if em else None
            if "job_flag_pattern" in spec:
                jm = re.search(spec["job_flag_pattern"], snippet)
                job = jm.group(1) if jm else None
            out.append(HiddenEdge(kind=kind, event=event, job=job, raw=snippet.strip()))
    return out


def _credential_hits(command: str) -> list[CredentialHit]:
    out: list[CredentialHit] = []
    for name, (pat, group_idx) in _CREDENTIAL_PATTERNS.items():
        for m in pat.finditer(command):
            out.append(CredentialHit(pattern=name, span=(m.start(group_idx), m.end(group_idx))))
    return out


def normalize(command: str) -> str:
    """Replace literal, position-varying spans (dates, numbers, %%vars%%) with placeholders
    so near-duplicate commands (same script, different args) hash to the same template
    [plan §11.2 template_clusters]."""
    out = command
    for pat, placeholder in _NORMALIZE:
        out = pat.sub(placeholder, out)
    return out


def analyze(command: str, os_hint: str | None = None) -> CommandAnalysis:
    """Analyze one `command:`/`watch_file:`/`std_*_file:`/`profile:` string. Never executes it."""
    interpreter, explicit_token = _detect_interpreter(command)
    script_path, args = _script_path_and_args(command, interpreter, explicit_token)
    normalized = normalize(command)
    return CommandAnalysis(
        raw=command,
        interpreter=interpreter,
        script_path=script_path,
        args=args,
        global_var_refs=sorted(set(_GLOBAL_VAR_RE.findall(command))),
        hidden_control_flow=_hidden_control_flow(command),
        hosts=sorted({m.group(1) for m in _HOSTS_RE.finditer(command)} - set(_IPS_RE.findall(command))),
        ips=sorted(set(_IPS_RE.findall(command))),
        abs_paths=sorted(set(_ABS_PATH_RE.findall(command))),
        unc_paths=sorted(set(_UNC_RE.findall(command))),
        mapped_drives=sorted(set(_MAPPED_DRIVE_RE.findall(command))),
        credential_hits=_credential_hits(command),
        os_hint=os_hint or _detect_os_hint(command),
        normalized=normalized,
        template_hash=hashlib.sha256(normalized.encode()).hexdigest()[:16],
    )


@dataclass(slots=True)
class Cluster:
    template_hash: str
    members: list[str] = field(default_factory=list)  # job names
    normalized: str = ""
    varying_positions: list[int] = field(default_factory=list)  # word-index positions that differ

    def as_dict(self) -> dict:
        return {"template_hash": self.template_hash, "members": self.members,
                "normalized": self.normalized, "varying_positions": self.varying_positions}


def _varying_word_positions(raws: list[str]) -> list[int]:
    tokenized = [r.split() for r in raws]
    width = max((len(t) for t in tokenized), default=0)
    varying: list[int] = []
    for i in range(width):
        values = {t[i] for t in tokenized if i < len(t)}
        if len(values) > 1:
            varying.append(i)
    return varying


def cluster_templates(jobs: dict[str, str]) -> list[Cluster]:
    """Group job commands by normalized template hash.

    `jobs` maps job name -> raw command string. Only hashes with >= 2 members are clusters
    worth reporting as dag-factory / dynamic-task-mapping candidates [plan §5, KB 001/007];
    singletons are omitted.
    """
    by_hash: dict[str, list[str]] = {}
    raws_by_hash: dict[str, list[str]] = {}
    normalized_by_hash: dict[str, str] = {}
    for name, cmd in jobs.items():
        if not cmd:
            continue
        a = analyze(cmd)
        by_hash.setdefault(a.template_hash, []).append(name)
        raws_by_hash.setdefault(a.template_hash, []).append(cmd)
        normalized_by_hash[a.template_hash] = a.normalized
    clusters = [
        Cluster(template_hash=h, members=sorted(members), normalized=normalized_by_hash[h],
               varying_positions=_varying_word_positions(raws_by_hash[h]))
        for h, members in by_hash.items() if len(members) >= 2
    ]
    return sorted(clusters, key=lambda c: (-len(c.members), c.template_hash))

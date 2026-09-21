from pathlib import Path

import pytest

from autosys_jil import status

_LIB_ROOT = Path(__file__).resolve().parents[2]  # skills/_lib (autosys_jil is importable from here)


def test_all_seven_workflows_defined():
    workflows = status.load_workflows()
    assert set(workflows) == {"assessment", "translation", "topology", "k8s-parity", "boundary",
                              "cutover", "platform"}


def test_advance_creates_unit_and_records_history():
    m = {}
    rec = status.advance(m, "translation", "job_a", "translate", unit_type="job")
    assert rec["state"] == "translate"
    assert rec["history"][0]["from"] == "pending"
    assert rec["history"][0]["to"] == "translate"


def test_deferred_without_note_is_rejected():
    m = {}
    with pytest.raises(status.WorkflowError):
        status.advance(m, "translation", "job_a", "deferred")


def test_deferred_with_note_records_reason():
    m = {}
    status.advance(m, "translation", "job_a", "deferred", note="blocked on legal review")
    rec = m["status"]["translation"]["units"]["job_a"]
    assert rec["deferred_reason"] == "blocked on legal review"


def test_invalid_state_rejected():
    m = {}
    with pytest.raises(status.WorkflowError):
        status.advance(m, "translation", "job_a", "not_a_real_state")


def test_completeness_clean_when_all_terminal():
    m = {}
    status.advance(m, "translation", "job_a", "complete")
    status.advance(m, "translation", "job_b", "deferred", note="waived")
    result = status.completeness(m, "translation")
    assert result["clean"] is True
    assert result["incomplete"] == []


def test_completeness_dirty_when_a_unit_is_not_terminal():
    m = {}
    status.advance(m, "translation", "job_a", "fix-lint")
    result = status.completeness(m, "translation")
    assert result["clean"] is False
    assert result["incomplete"] == [("job_a", "fix-lint")]


def test_cutover_parity_state_is_repeatable_and_counts_cycles():
    m = {}
    status.advance(m, "cutover", "box1", "shadow")
    status.advance(m, "cutover", "box1", "parity")
    status.advance(m, "cutover", "box1", "parity")
    status.advance(m, "cutover", "box1", "parity")
    assert m["status"]["cutover"]["units"]["box1"]["cycle"] == 2


def test_reopen_resets_to_initial_state():
    m = {}
    status.advance(m, "translation", "job_a", "complete")
    status.reopen(m, "translation", "job_a", "found a regression")
    assert m["status"]["translation"]["units"]["job_a"]["state"] == "pending"
    assert "deferred_reason" not in m["status"]["translation"]["units"]["job_a"]


def test_reopen_unknown_unit_raises():
    m = {}
    with pytest.raises(status.WorkflowError):
        status.reopen(m, "translation", "does_not_exist", "reason")


def test_k8s_parity_disposition_is_independent_of_state():
    m = {}
    status.advance(m, "k8s-parity", "rbac", "classified", disposition="direct-port")
    rec = m["status"]["k8s-parity"]["units"]["rbac"]
    assert rec["state"] == "classified" and rec["disposition"] == "direct-port"
    status.advance(m, "k8s-parity", "rbac", "planned")  # state moves on, disposition persists
    assert m["status"]["k8s-parity"]["units"]["rbac"]["disposition"] == "direct-port"


def test_k8s_parity_invalid_disposition_rejected():
    m = {}
    with pytest.raises(status.WorkflowError):
        status.advance(m, "k8s-parity", "rbac", "classified", disposition="not-a-real-disposition")


def test_k8s_parity_completeness_flags_advanced_without_disposition():
    m = {}
    status.advance(m, "k8s-parity", "rbac", "planned")  # advanced past 'pending', no disposition set
    result = status.completeness(m, "k8s-parity")
    assert "rbac" in result["advanced_without_disposition"]
    assert result["clean"] is False


def test_boundary_workflow_states_match_legacy_shape():
    workflows = status.load_workflows()
    assert set(workflows["boundary"]["states"]) == {
        "flagged", "confirmed", "translate", "trial", "validating",
        "complete", "not-a-boundary-job", "deferred",
    }
    assert "not-a-boundary-job" in workflows["boundary"]["terminal"]


def test_cli_manifest_flag_must_precede_subcommand(tmp_path):
    import json
    import subprocess
    import sys

    manifest_path = tmp_path / "m.json"
    manifest_path.write_text("{}")
    result = subprocess.run(
        [sys.executable, "-m", "autosys_jil.status", "--manifest", str(manifest_path),
         "advance", "job_x", "--workflow", "translation", "--status", "complete"],
        capture_output=True, text=True, cwd=str(_LIB_ROOT),
    )
    assert result.returncode == 0, result.stderr
    saved = json.loads(manifest_path.read_text())
    assert saved["status"]["translation"]["units"]["job_x"]["state"] == "complete"


def test_cli_gate_exits_nonzero_when_dirty(tmp_path):
    import subprocess
    import sys

    manifest_path = tmp_path / "m.json"
    manifest_path.write_text("{}")
    subprocess.run(
        [sys.executable, "-m", "autosys_jil.status", "--manifest", str(manifest_path),
         "advance", "job_x", "--workflow", "translation", "--status", "fix-lint"],
        capture_output=True, text=True, check=True, cwd=str(_LIB_ROOT),
    )
    result = subprocess.run(
        [sys.executable, "-m", "autosys_jil.status", "--manifest", str(manifest_path),
         "gate", "--workflow", "translation"],
        capture_output=True, text=True, cwd=str(_LIB_ROOT),
    )
    assert result.returncode == 1

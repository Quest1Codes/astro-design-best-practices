from autosys_jil import commands


def test_bare_script_path_interpreter_detection_by_extension():
    assert commands.analyze("/scripts/mktdata/fetch_bloomberg.sh --date %%DATE%%").interpreter == "sh"
    assert commands.analyze("/scripts/refdata/validate_integrity.py --strict").interpreter == "python"


def test_explicit_interpreter_prefix_detection():
    assert commands.analyze("bash /scripts/x.sh").interpreter == "bash"
    assert commands.analyze("/usr/bin/ksh /scripts/x.ksh").interpreter == "ksh"
    assert commands.analyze("sqlplus scott/tiger@PRODDB @report.sql").interpreter == "sqlplus"


def test_global_var_refs_found():
    a = commands.analyze("/scripts/x.sh --date %%DATE%% --fallback %%YESTERDAY%%")
    assert a.global_var_refs == ["DATE", "YESTERDAY"]


def test_hidden_sendevent_control_flow_detected():
    a = commands.analyze("sendevent -E FORCE_STARTJOB -J downstream_job")
    assert len(a.hidden_control_flow) == 1
    edge = a.hidden_control_flow[0]
    assert edge.kind == "sendevent" and edge.event == "FORCE_STARTJOB" and edge.job == "downstream_job"


def test_credential_hit_connect_string_never_captures_value():
    a = commands.analyze("sqlplus scott/tiger@PRODDB @script.sql")
    assert len(a.credential_hits) == 1
    hit = a.credential_hits[0]
    assert hit.pattern == "connect_string"
    # only a span is recorded, never the literal value
    assert not hasattr(hit, "value")


def test_credential_hit_password_flag():
    a = commands.analyze("mytool -p Secr3t!")
    assert any(h.pattern == "password_flag" for h in a.credential_hits)


def test_credential_hit_userpass_flag():
    a = commands.analyze("curl -u admin:S3cret https://api.example.com/trigger")
    assert any(h.pattern == "userpass_flag" for h in a.credential_hits)


def test_no_false_positive_credential_hit_on_clean_command():
    a = commands.analyze("/scripts/x.sh --date %%DATE%% --threshold 0.98")
    assert a.credential_hits == []


def test_os_hint_windows_from_cmd_c_and_unc_and_drive_letter():
    assert commands.analyze(r"cmd /c C:\jobs\extract\run.bat").os_hint == "windows"
    assert commands.analyze(r"powershell.exe -File \\fileserver01\share\report.ps1").os_hint == "windows"


def test_os_hint_unix_from_absolute_path():
    assert commands.analyze("/scripts/mktdata/fetch.sh --date %%DATE%%").os_hint == "unix"


def test_os_hint_unknown_when_no_signal():
    assert commands.analyze("echo hello").os_hint == "unknown"


def test_normalize_replaces_dates_numbers_and_vars_with_placeholders():
    norm = commands.normalize("/scripts/x.sh --date 2026-09-17 --retries 3 --var %%DATE%%")
    assert "2026-09-17" not in norm
    assert "<DATE>" in norm
    assert "<N>" in norm
    assert "<VAR>" in norm


def test_cluster_templates_groups_by_normalized_shape():
    jobs = {
        "job_a": "/scripts/x/run.sh --date 2026-01-01",
        "job_b": "/scripts/x/run.sh --date 2026-01-02",
        "job_c": "/scripts/y/other.sh --date 2026-01-01",
    }
    clusters = commands.cluster_templates(jobs)
    assert len(clusters) == 1
    assert set(clusters[0].members) == {"job_a", "job_b"}


def test_cluster_templates_omits_singletons():
    jobs = {"job_a": "/scripts/x/run.sh --unique-arg-a", "job_b": "/scripts/y/run.sh --unique-arg-b"}
    assert commands.cluster_templates(jobs) == []


def test_script_path_for_bare_extension_matched_script_is_tokens_0_not_1():
    # Extension-based interpreter detection (no separate interpreter token) must not skip
    # tokens[0] -- tokens[0] IS the script.
    a = commands.analyze("/scripts/mktdata/fetch_bloomberg.sh --type EQUITY --date %%DATE%%")
    assert a.script_path == "/scripts/mktdata/fetch_bloomberg.sh"
    assert a.args == ["--type", "EQUITY", "--date", "%%DATE%%"]


def test_script_path_for_explicit_interpreter_token_skips_it():
    a = commands.analyze("bash /scripts/x.sh arg1 arg2")
    assert a.script_path == "/scripts/x.sh"
    assert a.args == ["arg1", "arg2"]


def test_script_path_and_args_respect_quoting_not_naive_split():
    # A quoted multi-word argument must not be torn apart and mistaken for the script path.
    a = commands.analyze('/scripts/alerts/send_page.sh "CRITICAL: Market data validation failed for %%DATE%%"')
    assert a.script_path == "/scripts/alerts/send_page.sh"
    assert a.args == ["CRITICAL: Market data validation failed for %%DATE%%"]


def test_unbalanced_quotes_fall_back_gracefully_not_raise():
    a = commands.analyze('/scripts/x.sh "unterminated')
    assert a.script_path == "/scripts/x.sh"


def test_credential_patterns_reused_verbatim_by_manifest():
    from autosys_jil import manifest
    assert manifest.DEFAULT_REDACT_PATTERNS is not commands.credential_patterns()
    assert set(manifest.DEFAULT_REDACT_PATTERNS) == set(commands.credential_patterns())

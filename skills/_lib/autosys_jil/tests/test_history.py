from datetime import date
from pathlib import Path

from autosys_jil import history
from autosys_jil.history import Event

FIXTURES = Path(__file__).parent / "fixtures" / "synthetic"


def _fixed_width_report(header_cols, widths, rows, indent=0):
    def fmt(cols):
        return " " * indent + " ".join(c.ljust(w) for c, w in zip(cols, widths))
    sep = fmt(["_" * w for w in widths])
    return "\n".join([fmt(header_cols), sep] + [fmt(r) for r in rows]) + "\n"


def test_parse_autorep_r_flat_box_report():
    # Real column shape/values from [AS p.2364] "nebox" worked example (verified in this
    # session's HANDOFF -- PDF text itself is line-wrapped for print, so this is rebuilt with
    # exact fixed-width padding rather than copied verbatim).
    widths = [21, 20, 20, 5, 8, 7]
    text = _fixed_width_report(
        ["Job Name", "Last Start", "Last End", "ST/Ex", "Run/Ntry", "Pri/Xit"], widths,
        [
            ["nebox", "09/07/2016 10:17:33", "-----", "RU", "1620/1", ""],
            ["nebox_b1", "09/07/2016 10:17:34", "-----", "RU/NE", "1620/1", ""],
            ["nebox_b1_j1", "09/07/2016 10:17:35", "09/07/2016 10:17:35", "SU/NE", "1620/1", "0"],
            ["nebox_j1", "09/07/2016 10:17:34", "09/07/2016 10:17:34", "SU", "1620/1", "0"],
        ],
    )
    runs = history.parse_autorep_r(text)
    assert len(runs) == 4
    assert runs[0].job == "nebox" and runs[0].status == "RUNNING" and runs[0].end is None
    assert runs[1].status == "RUNNING" and runs[1].exec_mode_noexec is True
    assert runs[2].status == "SUCCESS" and runs[2].exec_mode_noexec is True and runs[2].exit_code == 0
    assert runs[3].status == "SUCCESS" and runs[3].exec_mode_noexec is False


def test_parse_autorep_r_columns_can_exactly_fill_width_with_no_space_gap():
    # ST/Ex value "RU/NE" is exactly as wide as the 5-char ST/Ex column -- there is NO
    # whitespace gap before Run/Ntry in real output. A space-run splitter would misparse this;
    # fixed-width slicing (derived from the underscore separator line) must not.
    widths = [10, 20, 20, 5, 8, 7]
    text = _fixed_width_report(
        ["Job Name", "Last Start", "Last End", "ST/Ex", "Run/Ntry", "Pri/Xit"], widths,
        [["j1", "-----", "-----", "RU/NE", "1620/1", ""]],
    )
    runs = history.parse_autorep_r(text)
    assert len(runs) == 1 and runs[0].exec_mode_noexec is True


def test_parse_autorep_d_detail_report_with_two_jobs_no_repeated_header():
    sw = [29, 21, 21, 5, 8, 7]
    ew = [22, 21, 4, 3, 21, 16]

    def srow(cols):
        return " ".join(c.ljust(w) for c, w in zip(cols, sw))

    def erow(cols):
        return "   " + " ".join(c.ljust(w) for c, w in zip(cols, ew))

    sh = srow(["Job Name", "Last Start", "Last End", "ST/Ex", "Run/Ntry", "Pri/Xit"])
    ssep = srow(["_" * w for w in sw])
    eh = erow(["Status/[Event]", "Time", "Ntry", "ES", "ProcessTime", "Machine"])
    esep = erow(["-" * w for w in ew])

    text = "\n".join([
        sh, ssep,
        srow(["Nightly_Download", "05/21/2010 11:27:31", "05/21/2010 11:27:33", "SU", "197/1", "0"]),
        eh, esep,
        erow(["RUNNING", "05/21/2010 11:27:31", "1", "PD", "05/21/2010 11:27:31", ""]),
        erow(["SUCCESS", "05/21/2010 11:27:33", "1", "PD", "05/21/2010 11:27:34", ""]),
        srow(["RunData", "05/21/2010 11:41:10", "05/21/2010 11:41:10", "FA", "198/1", "20007"]),
        eh, esep,
        erow(["STARTING", "05/21/2010 11:41:09", "1", "PD", "05/21/2010 11:41:09", "localhost"]),
        erow(["RUNNING", "05/21/2010 11:41:10", "1", "PD", "05/21/2010 11:41:10", "localhost"]),
        erow(["FAILURE", "05/21/2010 11:41:10", "1", "PD", "05/21/2010 11:41:10", ""]),
        "   <Command file not found>",
        erow(["[JOBFAILURE]", "05/21/2010 11:41:10", "1", "PD", "05/21/2010 11:41:11", "localhost"]),
    ]) + "\n"

    runs, events = history.parse_autorep_d(text)
    assert len(runs) == 2
    assert runs[0].job == "Nightly_Download" and runs[0].status == "SUCCESS"
    assert runs[1].job == "RunData" and runs[1].status == "FAILURE" and runs[1].exit_code == 20007
    assert len(events) == 6
    assert events[0].job == "Nightly_Download" and events[2].job == "RunData"
    assert events[-1].event == "JOBFAILURE"
    assert events[4].event == "FAILURE" and events[4].note == "Command file not found"


def test_parse_run_history_csv_fixture():
    runs = history.parse_run_history_csv(FIXTURES / "history_90d.csv")
    assert len(runs) == 11
    by_job: dict[str, list] = {}
    for r in runs:
        by_job.setdefault(r.job, []).append(r)
    assert len(by_job["nightly_extract"]) == 5
    assert any(r.status == "FAILURE" for r in by_job["nightly_extract"])


def test_parse_event_archive_csv_fixture():
    events = history.parse_event_archive_csv(FIXTURES / "events_90d.csv")
    assert any(e.event == "FORCE_STARTJOB" and e.source_user == "ops_bob" for e in events)


def test_job_stats_from_fixture_csv():
    runs = history.parse_run_history_csv(FIXTURES / "history_90d.csv")
    stats = history.job_stats(runs)
    assert stats["nightly_extract"]["count"] == 5
    assert stats["nightly_extract"]["failure_rate"] == 1 / 5
    assert stats["build_report"]["failure_rate"] == 0.0


def test_manual_intervention_counts_by_job_and_user():
    events = history.parse_event_archive_csv(FIXTURES / "events_90d.csv")
    result = history.manual_intervention(events)
    assert result["per_job"]["nightly_extract"] == 1
    assert result["per_source_user"]["ops_bob"] == 1
    assert result["per_job"].get("monthly_close", 0) == 2  # JOB_ON_HOLD + JOB_OFF_HOLD


def test_dead_jobs_flags_jobs_with_no_recent_run():
    runs = history.parse_run_history_csv(FIXTURES / "history_90d.csv")
    dead = history.dead_jobs(
        ["nightly_extract", "build_report", "never_ran_job"], runs, window_days=30,
        as_of=date(2026, 10, 15),
    )
    dead_names = {d["job"] for d in dead}
    assert "never_ran_job" in dead_names
    assert "nightly_extract" in dead_names  # last run 09/04, 30d window from 10/15


def test_sla_breaches_detects_late_completion():
    runs = history.parse_run_history_csv(FIXTURES / "history_90d.csv")
    breaches = history.sla_breaches({"nightly_extract": ["01:10"]}, runs)
    assert breaches and breaches[0]["job"] == "nightly_extract"


def test_concurrency_curve_counts_overlap():
    from datetime import datetime
    runs = [
        history.Run(job="a", run_num=1, ntry=1,
                   start=datetime(2026, 1, 1, 10, 0), end=datetime(2026, 1, 1, 10, 5),
                   status="SUCCESS", exit_code=0),
        history.Run(job="b", run_num=1, ntry=1,
                   start=datetime(2026, 1, 1, 10, 2), end=datetime(2026, 1, 1, 10, 8),
                   status="SUCCESS", exit_code=0),
    ]
    curve = history.concurrency_curve(runs)
    assert curve["2026-01-01T10:03:00"] == 2
    assert curve["2026-01-01T10:00:00"] == 1

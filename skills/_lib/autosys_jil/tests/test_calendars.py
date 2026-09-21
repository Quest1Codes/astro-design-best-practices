from datetime import date

from autosys_jil.calendars import (
    classify_calendar, cron_equivalent, eligible_dates, expand, parse_autocal_asc, parse_date_tokens,
)
from autosys_jil.models import Calendar, Job, Provenance, Schedule


def _job(**schedule_kwargs) -> Job:
    prov = Provenance("<test>", 1, 0, "ACE", "insert_job")
    return Job(name="j", job_type="CMD", job_type_known=True, attrs={}, provenance=prov,
              schedule=Schedule(date_conditions=True, **schedule_kwargs))


def test_parse_autocal_asc_multi_calendar(tmp_path):
    from pathlib import Path
    fixture = Path(__file__).parent / "fixtures" / "synthetic" / "autocal_asc_sample.txt"
    cals = parse_autocal_asc(fixture.read_text())
    assert set(cals) == {"US_HOLIDAYS_2026", "MONTH_END_2026"}
    assert date(2026, 1, 1) in cals["US_HOLIDAYS_2026"].dates
    assert len(cals["MONTH_END_2026"].dates) == 12


def test_parse_date_tokens_both_formats():
    dates = parse_date_tokens(["01/15/2026", "2026-02-20"])
    assert dates == [date(2026, 1, 15), date(2026, 2, 20)]


def test_classify_weekday_only():
    start, end = date(2026, 1, 5), date(2026, 1, 9)  # Mon-Fri
    dates = [start.replace(day=d) for d in range(5, 10)]
    cal = Calendar(name="weekdays", dates=dates)
    assert classify_calendar(cal) == "weekday_only"


def test_classify_month_end():
    cal = Calendar(name="me", dates=[date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)])
    assert classify_calendar(cal) == "month_end"


def test_eligible_dates_all_days():
    job = _job(days_of_week=["all"])
    dates = eligible_dates(job, {}, date(2026, 1, 1), date(2026, 1, 7))
    assert len(dates) == 7


def test_eligible_dates_specific_days():
    job = _job(days_of_week=["mo", "we", "fr"])
    dates = eligible_dates(job, {}, date(2026, 1, 5), date(2026, 1, 11))  # Mon 1/5 .. Sun 1/11
    assert dates == [date(2026, 1, 5), date(2026, 1, 7), date(2026, 1, 9)]


def test_run_calendar_intersection():
    cal = Calendar(name="c", dates=[date(2026, 1, 5), date(2026, 1, 6)])
    job = _job(days_of_week=["all"], run_calendar="c")
    dates = eligible_dates(job, {"c": cal}, date(2026, 1, 1), date(2026, 1, 10))
    assert dates == [date(2026, 1, 5), date(2026, 1, 6)]


def test_exclude_calendar_removes_dates():
    excl = Calendar(name="holidays", dates=[date(2026, 1, 6)])
    job = _job(days_of_week=["mo", "tu"], exclude_calendar="holidays")
    dates = eligible_dates(job, {"holidays": excl}, date(2026, 1, 5), date(2026, 1, 7))
    assert date(2026, 1, 6) not in dates


def test_expand_produces_instants_with_start_times():
    job = _job(days_of_week=["all"], start_times=["09:00", "17:00"])
    result = expand(job, {}, date(2026, 1, 5), date(2026, 1, 5))
    assert result["count"] == 2


def test_cron_equivalent_for_simple_daily_schedule():
    job = _job(days_of_week=["all"], start_times=["09:00"])
    cron = cron_equivalent(job, {}, date(2026, 1, 1), date(2026, 3, 1))
    assert cron == "0 9 * * *"


def test_cron_equivalent_none_for_calendar_driven_schedule():
    cal = Calendar(name="c", dates=[date(2026, 1, 5), date(2026, 2, 20)])
    job = _job(days_of_week=["all"], start_times=["09:00"], run_calendar="c")
    cron = cron_equivalent(job, {"c": cal}, date(2026, 1, 1), date(2026, 3, 1))
    assert cron is None


def test_dst_spring_forward_gap_flagged():
    # America/New_York 2026-03-08: clocks spring forward 02:00 -> 03:00; 02:30 does not exist.
    job = _job(days_of_week=["all"], start_times=["02:30"], timezone="America/New_York")
    result = expand(job, {}, date(2026, 3, 8), date(2026, 3, 8))
    assert result["dst_gap_instants"]


def test_dst_fall_back_overlap_flagged():
    # America/New_York 2026-11-01: clocks fall back 02:00 -> 01:00; 01:30 occurs twice.
    job = _job(days_of_week=["all"], start_times=["01:30"], timezone="America/New_York")
    result = expand(job, {}, date(2026, 11, 1), date(2026, 11, 1))
    assert result["dst_overlap_instants"]

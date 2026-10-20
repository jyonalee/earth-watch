"""Complete-calendar-year rules for chart annual series."""

from __future__ import annotations

from datetime import datetime, timezone

from earth_watch.annual_complete import (
    berkeley_chart_years,
    filter_annual_values,
    gistemp_complete_years,
    hadcrut_monthly_complete_years,
)


def test_hadcrut_monthly_flags_2026_incomplete():
    months = [{"year": 2025, "month": m} for m in range(1, 13)]
    months += [{"year": 2026, "month": m} for m in range(1, 8)]
    complete = hadcrut_monthly_complete_years(months)
    assert 2025 in complete
    assert 2026 not in complete


def test_gistemp_complete_years_need_twelve_months():
    frame = [
        {
            "Year": 2025,
            "Jan": 1.0,
            "Feb": 1.0,
            "Mar": 1.0,
            "Apr": 1.0,
            "May": 1.0,
            "Jun": 1.0,
            "Jul": 1.0,
            "Aug": 1.0,
            "Sep": 1.0,
            "Oct": 1.0,
            "Nov": 1.0,
            "Dec": 1.0,
            "J-D": 1.0,
        },
        {
            "Year": 2026,
            "Jan": 1.0,
            "Feb": 1.0,
            "Mar": None,
            "Apr": None,
            "May": None,
            "Jun": None,
            "Jul": None,
            "Aug": None,
            "Sep": None,
            "Oct": None,
            "Nov": None,
            "Dec": None,
            "J-D": 1.1,
        },
    ]
    complete = gistemp_complete_years(frame)
    assert 2025 in complete
    assert 2026 not in complete


def test_filter_annual_values():
    values = {2024: 1.0, 2025: 1.1, 2026: 1.2}
    out = filter_annual_values(values, {2024, 2025})
    assert out == {2024: 1.0, 2025: 1.1}


def test_berkeley_drops_current_calendar_year():
    run_at = datetime(2026, 10, 19, tzinfo=timezone.utc)
    years = berkeley_chart_years([2023, 2024, 2025, 2026], run_at=run_at)
    assert years == {2023, 2024, 2025}

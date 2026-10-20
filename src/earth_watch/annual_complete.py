"""Rules for including only complete calendar years in chart annual series."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

_GISTEMP_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _years_with_twelve_months(month_rows: Iterable[dict[str, Any]]) -> set[int]:
    counts: dict[int, int] = {}
    for row in month_rows:
        year = int(row["year"])
        month = int(row["month"])
        if month < 1 or month > 12:
            continue
        counts[year] = counts.get(year, 0) + 1
    return {year for year, count in counts.items() if count >= 12}


def hadcrut_monthly_complete_years(monthly_frame: list[dict[str, Any]]) -> set[int]:
    return _years_with_twelve_months(monthly_frame)


def gistemp_complete_years(frame: list[dict[str, Any]]) -> set[int]:
    complete: set[int] = set()
    for row in frame:
        year = int(row["Year"])
        months_present = sum(1 for col in _GISTEMP_MONTHS if row.get(col) is not None)
        if months_present >= 12:
            complete.add(year)
    return complete


def berkeley_chart_years(
    years_in_file: Iterable[int],
    *,
    run_at: datetime | None = None,
) -> set[int]:
    run_at = run_at or datetime.now(timezone.utc)
    current_year = run_at.astimezone(timezone.utc).year
    return {int(y) for y in years_in_file if int(y) < current_year}


def filter_annual_values(values: dict[int, float], complete_years: set[int]) -> dict[int, float]:
    return {year: val for year, val in values.items() if year in complete_years}

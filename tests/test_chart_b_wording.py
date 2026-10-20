"""Chart (b) read and facts wording for airborne-fraction trends."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from earth_watch.chart_b import _read_from_trend, build_chart_b_payload
from earth_watch.fetchers import GcbBudgetFetcher, GmlGlobalGrowthFetcher
from earth_watch.fetchers.base import FetchResult
from earth_watch.trends.ols import TrendFit

FIXTURES = Path(__file__).parent / "fixtures"


def _trend_fit(
    *,
    slope_pp_decade: float,
    low_pp_decade: float,
    high_pp_decade: float,
) -> TrendFit:
    slope = slope_pp_decade / 100.0
    low = low_pp_decade / 100.0
    high = high_pp_decade / 100.0
    return TrendFit(
        year_start=1960,
        year_end=2024,
        n=65,
        slope_per_year_c=slope / 10.0,
        intercept_c=0.45,
        slope_per_decade_c=slope,
        ci95_low_per_decade_c=low,
        ci95_high_per_decade_c=high,
        ar1_rho=0.05,
        effective_n=59.0,
        residual_std_c=0.02,
        x_mean=1992.0,
        sxx=1.0e5,
        t_critical=2.0,
    )


def test_read_hint_when_ci_includes_zero_but_lower_bound_near_zero():
    fit = _trend_fit(slope_pp_decade=1.65, low_pp_decade=-0.03, high_pp_decade=3.33)
    text = _read_from_trend(fit)
    assert "hint" in text.lower() or "not yet statistically clear" in text.lower()
    assert "weakening" in text.lower() or "rising share" in text.lower()
    assert "roughly constant" not in text.lower()


def test_read_constant_share_when_ci_centered_near_zero():
    fit = _trend_fit(slope_pp_decade=0.1, low_pp_decade=-1.5, high_pp_decade=1.2)
    text = _read_from_trend(fit)
    assert "roughly constant share" in text.lower()


def test_read_increasing_when_ci_excludes_zero():
    fit = _trend_fit(slope_pp_decade=2.0, low_pp_decade=0.5, high_pp_decade=3.5)
    text = _read_from_trend(fit)
    assert "increased since 1960" in text


def _fixture_payload():
    run_at = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)

    def _record(fetcher, filename: str):
        content = (FIXTURES / filename).read_bytes()
        fetch = FetchResult.from_bytes(
            fetcher.spec,
            content,
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        return fetcher.process(fetch)

    return build_chart_b_payload(
        [
            _record(GcbBudgetFetcher(), "global_carbon_budget_2025.xlsx"),
            _record(GmlGlobalGrowthFetcher(), "co2_gr_gl.txt"),
        ],
        run_at=run_at,
    )


def test_facts_include_long_term_mean_and_10y_smooth():
    payload = _fixture_payload()
    facts_text = " ".join(payload["facts"]).lower()
    assert "1960" in facts_text
    assert "mean" in facts_text
    assert "10-year" in facts_text or "10 year" in facts_text
    assert "smoothed" in facts_text


def test_facts_note_enso_and_fire_year_volatility():
    payload = _fixture_payload()
    facts_text = " ".join(payload["facts"]).lower()
    assert "enso" in facts_text or "el niño" in facts_text or "el nino" in facts_text
    assert "fire" in facts_text or "fires" in facts_text
    assert "single year" in facts_text or "single years" in facts_text


def test_fixture_read_uses_hint_not_constant_share():
    """Production-like trend (+1.65 pp/dec, CI -0.03 to 3.33) from fixtures."""
    payload = _fixture_payload()
    assert "roughly constant" not in payload["read"].lower()

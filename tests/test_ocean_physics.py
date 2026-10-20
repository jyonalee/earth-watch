"""OHC heating-rate conversion."""

from earth_watch.ocean_physics import ohc_slope_1e22j_per_year_to_w_m2


def test_heating_rate_positive_for_warming_ocean():
    w = ohc_slope_1e22j_per_year_to_w_m2(1.0)
    assert 0.5 < w < 2.0

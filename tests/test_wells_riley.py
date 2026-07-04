"""
test_wells_riley.py
---------------------
Unit tests for the core risk-scoring formula. Run with: pytest tests/
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from wells_riley import rebreathed_air_fraction, infection_risk_score, risk_category


def test_rebreathed_fraction_at_outdoor_baseline_is_zero():
    assert rebreathed_air_fraction(420) == 0.0


def test_rebreathed_fraction_increases_with_co2():
    low = rebreathed_air_fraction(800)
    high = rebreathed_air_fraction(2800)
    assert high > low


def test_rebreathed_fraction_clipped_between_0_and_1():
    assert 0.0 <= rebreathed_air_fraction(100000) <= 1.0
    assert 0.0 <= rebreathed_air_fraction(0) <= 1.0


def test_risk_score_zero_when_room_empty():
    assert infection_risk_score(co2_ppm=3000, occupancy=0) == 0.0
    assert infection_risk_score(co2_ppm=3000, occupancy=1) == 0.0


def test_risk_score_increases_with_co2_and_occupancy():
    low_risk = infection_risk_score(co2_ppm=500, occupancy=20)
    high_risk = infection_risk_score(co2_ppm=3000, occupancy=55)
    assert high_risk > low_risk


def test_risk_score_bounded_between_0_and_1():
    score = infection_risk_score(co2_ppm=3200, occupancy=60)
    assert 0.0 <= score <= 1.0


def test_risk_category_boundaries():
    assert risk_category(0.0) == "Low"
    assert risk_category(0.19) == "Low"
    assert risk_category(0.20) == "Medium"
    assert risk_category(0.44) == "Medium"
    assert risk_category(0.45) == "High"
    assert risk_category(1.0) == "High"

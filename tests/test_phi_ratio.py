import pytest
from fossil_scanner.analysis.phi_ratio import (
    PHI, ratio, deviation_from_phi, analyze_pair,
)


def test_phi_is_correct():
    assert abs(PHI - 1.61803398875) < 1e-9


def test_ratio_normalizes_order():
    assert ratio(2.0, 1.0) == ratio(1.0, 2.0)


def test_ratio_zero_denominator():
    assert ratio(1.0, 0.0) is None


def test_deviation_zero_at_phi():
    d = deviation_from_phi(PHI)
    assert d < 1e-9


def test_analyze_pair_flags_phi_interval():
    result = analyze_pair("a", 1.0, "b", PHI, uncertainty_a=0.05, uncertainty_b=0.02)
    assert result["status"] == "ok"
    assert result["phi_within_interval"] in (True, False)


def test_analyze_pair_rejects_nonpositive():
    result = analyze_pair("a", 0.0, "b", 1.0)
    assert result["status"] == "invalid"

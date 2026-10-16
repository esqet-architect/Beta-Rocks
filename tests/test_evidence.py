import pytest
from fossil_scanner.evidence import make_claim, transition_claim


def test_verified_requires_independent_verification():
    with pytest.raises(ValueError):
        make_claim("x", "VERIFIED", basis=["a"], independent_verification=False)


def test_verified_requires_records():
    with pytest.raises(ValueError):
        make_claim("x", "VERIFIED", basis=["a"], independent_verification=True)


def test_observed_requires_basis():
    with pytest.raises(ValueError):
        make_claim("x", "OBSERVED", basis=[])


def test_legal_transition_hypothesis_to_verified():
    c = make_claim("x", "HYPOTHESIS", basis=["observation"])
    c = transition_claim(c, "UNVERIFIED", reason="sent for review")
    c["verification_records"] = [{"reviewer": "A"}]
    c = transition_claim(c, "VERIFIED", reason="confirmed")
    assert c["state"] == "VERIFIED"


def test_illegal_transition_observed_to_verified():
    c = make_claim("x", "OBSERVED", basis=["sensor"])
    with pytest.raises(ValueError):
        transition_claim(c, "VERIFIED")

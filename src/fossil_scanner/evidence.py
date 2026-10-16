"""
Epistemological state machine for claims about a specimen.

Every interpretive statement made by the platform must carry an evidence
state so downstream readers can distinguish measurement from hypothesis.

State transitions are enforced. A VERIFIED claim must have at least one
verification record. A HYPOTHESIS may be promoted only by explicit review,
not by repetition.
"""
EVIDENCE_STATES = (
    "OBSERVED",    # directly recorded by a sensor
    "MEASURED",    # derived from a sensor with a documented method
    "DERIVED",     # computed from measurements
    "MODELED",     # produced by a model with documented assumptions
    "HYPOTHESIS",  # candidate interpretation, not verified
    "UNVERIFIED",  # claim awaiting independent check
    "VERIFIED",    # independently confirmed
    "REJECTED",    # falsified or retracted
)

# Legal transitions. A state may also stay in itself.
_ALLOWED_TRANSITIONS = {
    "OBSERVED":   {"OBSERVED", "DERIVED", "MEASURED", "UNVERIFIED", "HYPOTHESIS", "REJECTED"},
    "MEASURED":   {"MEASURED", "DERIVED", "UNVERIFIED", "HYPOTHESIS", "REJECTED"},
    "DERIVED":    {"DERIVED", "MODELED", "UNVERIFIED", "HYPOTHESIS", "REJECTED"},
    "MODELED":    {"MODELED", "UNVERIFIED", "HYPOTHESIS", "REJECTED"},
    "HYPOTHESIS": {"HYPOTHESIS", "UNVERIFIED", "VERIFIED", "REJECTED"},
    "UNVERIFIED": {"UNVERIFIED", "VERIFIED", "REJECTED"},
    "VERIFIED":   {"VERIFIED", "REJECTED"},
    "REJECTED":   {"REJECTED"},
}


def _check_transition(from_state: str, to_state: str) -> None:
    if to_state not in _ALLOWED_TRANSITIONS.get(from_state, set()):
        raise ValueError(
            f"Illegal evidence transition: {from_state} -> {to_state}"
        )


def make_claim(
    text: str,
    state: str,
    basis: list,
    independent_verification: bool = False,
    verification_records: list = None,
    confidence: float = None,
) -> dict:
    if state not in EVIDENCE_STATES:
        raise ValueError(f"state must be one of {EVIDENCE_STATES}")
    if confidence is not None and not (0.0 <= confidence <= 1.0):
        raise ValueError("confidence must be in [0, 1]")
    verification_records = verification_records or []
    if state == "VERIFIED":
        if not independent_verification:
            raise ValueError("VERIFIED requires independent_verification=True")
        if not verification_records:
            raise ValueError("VERIFIED requires at least one verification record")
    if state in ("OBSERVED", "MEASURED", "DERIVED", "MODELED") and not basis:
        raise ValueError(f"{state} requires a non-empty basis")
    return {
        "claim": text,
        "state": state,
        "basis": basis,
        "independent_verification": independent_verification,
        "verification_records": verification_records,
        "confidence": confidence,
    }


def transition_claim(claim: dict, to_state: str, reason: str = "") -> dict:
    """Return a new claim dict with an updated state, enforcing legal transitions."""
    _check_transition(claim["state"], to_state)
    if to_state == "VERIFIED" and not claim.get("verification_records"):
        raise ValueError("Cannot transition to VERIFIED without verification records")
    updated = dict(claim)
    updated["state"] = to_state
    updated.setdefault("transitions", []).append(
        {"from": claim["state"], "to": to_state, "reason": reason}
    )
    return updated


def make_classification(
    surface_morphology: dict = None,
    mineralization: dict = None,
    biological_origin: dict = None,
    taxonomic_affinity: dict = None,
) -> dict:
    """
    Multi-axis classification record. Each axis is independent so the
    platform never collapses 'interesting geometry' into 'fossil'.
    """
    undetermined = {"label": "undetermined", "state": "HYPOTHESIS", "confidence": None}
    return {
        "surface_morphology": surface_morphology or dict(undetermined),
        "mineralization": mineralization or dict(undetermined),
        "biological_origin": biological_origin or dict(undetermined),
        "taxonomic_affinity": taxonomic_affinity or dict(undetermined),
    }

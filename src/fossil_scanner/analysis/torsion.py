"""
Torsion measurement.

Records whole turns only when they are independently traced. A single
endpoint alignment cannot distinguish 0, 360, 720, and 1080 degrees, so the
app requires the observer to declare whether the full turn path was traced
and stores that declaration explicitly.

The app does not automatically convert hand-rotation into a claim of
historical deformation.
"""
from typing import Dict, Any, List, Optional


def make_measurement(
    form_class: str,
    trials_deg: List[float],
    direction: str,
    endpoint_a: str,
    endpoint_b: str,
    reference_frame: str,
    full_turn_traced: bool,
    traced_feature: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    if direction not in ("clockwise", "counterclockwise"):
        raise ValueError("direction must be clockwise or counterclockwise")
    if not trials_deg:
        raise ValueError("at least one trial required")
    if full_turn_traced and not traced_feature:
        raise ValueError(
            "full_turn_traced requires traced_feature: the continuously "
            "traceable feature used to count turns"
        )
    mean = sum(trials_deg) / len(trials_deg)
    return {
        "form_class": form_class,
        "trials_deg": list(trials_deg),
        "mean_deg": round(mean, 3),
        "range_deg": [round(min(trials_deg), 3), round(max(trials_deg), 3)],
        "direction": direction,
        "endpoint_a": endpoint_a,
        "endpoint_b": endpoint_b,
        "reference_frame": reference_frame,
        "full_turn_traced": full_turn_traced,
        "traced_feature": traced_feature,
        "notes": notes,
        "caveat": (
            "Endpoint alignment alone cannot distinguish whole turns. "
            "Values above 360 degrees require the traced_feature "
            "declaration to be independently checked."
        ),
    }

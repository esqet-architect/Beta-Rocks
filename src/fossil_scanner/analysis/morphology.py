"""
Morphology records.

Separates:
- observed_geometry: what is present in the point set
- observer_interpretation: what the observer proposes it means

This module never auto-assigns anatomical labels.
"""
from typing import Dict, Any, List, Optional

FORM_CLASSES = (
    "angular_faceted",
    "rounded_nodular",
    "layered_platy",
    "branched_fibrous",
    "c_shaped",
    "u_shaped",
    "folded_back",
    "twisted_spiral",
    "animal_like",
    "plant_like",
    "irregular",
)


def make_observation(
    overall_form: str,
    surface_features: Optional[List[str]] = None,
    apparent_translucency: Optional[str] = None,
    color_description: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    if overall_form not in FORM_CLASSES:
        raise ValueError(f"overall_form must be one of {FORM_CLASSES}")
    return {
        "overall_form": overall_form,
        "surface_features": surface_features or [],
        "apparent_translucency": apparent_translucency,
        "color_description": color_description,
        "notes": notes,
    }


def make_interpretation(
    label: str,
    state: str = "HYPOTHESIS",
    basis: Optional[List[str]] = None,
    alternatives: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    An interpretation is always an evidence-state record. It is never
    silently merged with the observation.
    """
    if state not in ("HYPOTHESIS", "UNVERIFIED", "VERIFIED", "REJECTED"):
        raise ValueError(
            "interpretation state must be one of "
            "HYPOTHESIS, UNVERIFIED, VERIFIED, REJECTED"
        )
    return {
        "label": label,
        "state": state,
        "basis": basis or [],
        "alternatives": alternatives or [],
    }

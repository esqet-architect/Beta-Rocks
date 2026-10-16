"""
Mineral identification support.

Photo appearance alone is insufficient for confident mineral identification.
This module therefore:
- Records the properties the observer can supply.
- Produces candidate lists with explicit uncertainty.
- Never claims a definitive species from a photograph.

The property weighting below is a transparent engineering heuristic, not a
validated identification model.
"""
from typing import Dict, Any, List, Optional

_REFERENCE_MINERALS = {
    "quartz": {
        "luster": ["vitreous", "greasy"],
        "hardness_mohs": 7.0,
        "streak": "white",
        "cleavage": "poor",
        "magnetism": "none",
        "common_colors": ["colorless", "white", "pink", "purple", "gray"],
    },
    "calcite": {
        "luster": ["vitreous", "pearly"],
        "hardness_mohs": 3.0,
        "streak": "white",
        "cleavage": "perfect_rhombohedral",
        "magnetism": "none",
        "common_colors": ["colorless", "white", "cream", "yellow"],
    },
    "pyrite": {
        "luster": ["metallic"],
        "hardness_mohs": 6.0,
        "streak": "greenish_black",
        "cleavage": "poor",
        "magnetism": "none",
        "common_colors": ["brass_yellow", "gold"],
    },
    "magnetite": {
        "luster": ["metallic", "submetallic"],
        "hardness_mohs": 6.0,
        "streak": "black",
        "cleavage": "none",
        "magnetism": "strong",
        "common_colors": ["black"],
    },
    "hematite": {
        "luster": ["metallic", "earthy"],
        "hardness_mohs": 5.5,
        "streak": "reddish_brown",
        "cleavage": "none",
        "magnetism": "weak",
        "common_colors": ["red", "brown", "gray"],
    },
    "halite": {
        "luster": ["vitreous"],
        "hardness_mohs": 2.5,
        "streak": "white",
        "cleavage": "perfect_cubic",
        "magnetism": "none",
        "common_colors": ["colorless", "white", "pink"],
    },
    "fluorite": {
        "luster": ["vitreous"],
        "hardness_mohs": 4.0,
        "streak": "white",
        "cleavage": "perfect_octahedral",
        "magnetism": "none",
        "common_colors": ["purple", "green", "blue", "yellow"],
    },
    "gypsum": {
        "luster": ["vitreous", "silky", "pearly"],
        "hardness_mohs": 2.0,
        "streak": "white",
        "cleavage": "perfect",
        "magnetism": "none",
        "common_colors": ["colorless", "white"],
    },
}


def _score_candidate(props: Dict[str, Any], ref: Dict[str, Any]) -> Dict[str, Any]:
    matched = 0
    possible = 0
    reasons = []

    if props.get("luster") and ref.get("luster"):
        possible += 1
        if props["luster"] in ref["luster"]:
            matched += 1
            reasons.append(f"luster '{props['luster']}' matches")
        else:
            reasons.append(f"luster '{props['luster']}' not in reference set")

    if props.get("hardness_mohs") is not None and ref.get("hardness_mohs") is not None:
        possible += 1
        if abs(props["hardness_mohs"] - ref["hardness_mohs"]) <= 0.5:
            matched += 1
            reasons.append("hardness within 0.5 Mohs")
        else:
            reasons.append("hardness outside tolerance")

    if props.get("streak") and ref.get("streak"):
        possible += 1
        if props["streak"] == ref["streak"]:
            matched += 1
            reasons.append("streak matches")
        else:
            reasons.append("streak differs")

    if props.get("magnetism") and ref.get("magnetism"):
        possible += 1
        if props["magnetism"] == ref["magnetism"]:
            matched += 1
            reasons.append("magnetic response matches")
        else:
            reasons.append("magnetic response differs")

    score = matched / possible if possible else 0.0
    return {
        "score": round(score, 4),
        "matched": matched,
        "possible": possible,
        "reasons": reasons,
        "coverage": round(possible / 4.0, 4),
    }


def identify_mineral(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a ranked list of candidates with the supporting reasoning.
    Does not claim a species; ranks candidates.
    """
    candidates = []
    for name, ref in _REFERENCE_MINERALS.items():
        result = _score_candidate(properties, ref)
        candidates.append({
            "mineral": name,
            "score": result["score"],
            "matched": result["matched"],
            "possible": result["possible"],
            "coverage": result["coverage"],
            "reasons": result["reasons"],
        })
    candidates.sort(key=lambda c: (c["score"], c["coverage"]), reverse=True)
    return {
        "status": "ranked_candidates" if candidates else "no_reference_data",
        "method": "property_match",
        "candidates": candidates,
        "note": (
            "Photo appearance and single-property observations are not "
            "sufficient for definitive mineral identification. Ranked "
            "candidates are proposals, not conclusions."
        ),
    }

"""
Diagnostic-character matching.

For a candidate taxon and a set of observable character states, compute:
- agreement score S(t)
- coverage C(t)
- list of supporting, contradictory, and missing characters

All weights come from the reference pack. They are not invented here.
"""
from typing import Dict, Any, List, Optional


def match_candidate(
    candidate_taxon_id: str,
    observed: List[Dict[str, Any]],
    reference_rules: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    observed: list of {character_id, state, observability, weight?}
    reference_rules: list of {character_id, expected_states, weight, diagnostic, citation}
    """
    rules_by_char = {r["character_id"]: r for r in reference_rules}
    supporting = []
    contradictory = []
    missing = []

    weighted_sum = 0.0
    weight_observed = 0.0
    weight_applicable = 0.0

    for rule in reference_rules:
        weight = float(rule.get("weight", 1.0))
        weight_applicable += weight
        cid = rule["character_id"]

        obs = next((o for o in observed if o["character_id"] == cid), None)
        if obs is None or obs.get("observability") in ("unknown", "obscured", "not_applicable"):
            missing.append({"character_id": cid, "reason": "unobserved or obscured"})
            continue

        state = obs.get("state")
        expected = rule.get("expected_states", [])
        weight_observed += weight
        if state in expected:
            weighted_sum += weight
            supporting.append({"character_id": cid, "state": state})
        else:
            weighted_sum -= weight
            contradictory.append({
                "character_id": cid,
                "observed": state,
                "expected": expected,
            })

    score = (weighted_sum / weight_observed) if weight_observed > 0 else 0.0
    coverage = (weight_observed / weight_applicable) if weight_applicable > 0 else 0.0

    return {
        "taxon_id": candidate_taxon_id,
        "score": round(score, 4),
        "coverage": round(coverage, 4),
        "supporting": supporting,
        "contradictory": contradictory,
        "missing": missing,
        "observable_character_count": len(supporting) + len(contradictory),
    }

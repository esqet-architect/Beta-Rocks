"""
Geological context ranking.

Context can adjust the plausibility of a candidate but cannot override
contradictions. Occurrence records provide context, not proof.
"""
from typing import Dict, Any, List, Optional


def context_bonus(
    candidate_taxon_id: str,
    context: Dict[str, Any],
    occurrence_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    context: { formation: str | None, age_ma_range: [lo, hi] | None, environment: str | None }
    occurrence_records: list of {taxon_id, formation, age_ma_range, environment}
    """
    matching = []
    for rec in occurrence_records:
        if rec.get("taxon_id") != candidate_taxon_id:
            continue
        if context.get("formation") and rec.get("formation") == context["formation"]:
            matching.append("formation")
        if context.get("age_ma_range") and rec.get("age_ma_range"):
            lo_c, hi_c = context["age_ma_range"]
            lo_r, hi_r = rec["age_ma_range"]
            if not (hi_c < lo_r or lo_c > hi_r):
                matching.append("age_overlap")

    bonus = min(0.2, 0.05 * len(set(matching)))
    return {
        "taxon_id": candidate_taxon_id,
        "context_matches": sorted(set(matching)),
        "bonus": round(bonus, 4),
        "note": (
            "Context supports plausibility. It does not resolve a "
            "candidate whose diagnostic characters are contradictory."
        ),
    }

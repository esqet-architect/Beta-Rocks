"""
Decision policy.

Determines the final decision rank from a candidate's matched evidence.

The policy is intentionally conservative: it prefers broader ranks and
'unresolved' over a specious species.
"""
from typing import Dict, Any, List


def decide_rank(
    best_candidate: Dict[str, Any],
    second_candidate: Dict[str, Any] = None,
    species_diagnostic_satisfied: bool = False,
    required_references_completed: bool = False,
    independent_review: bool = False,
) -> Dict[str, Any]:
    if best_candidate.get("observable_character_count", 0) == 0:
        return {"rank": "unresolved", "reason": "no observable characters"}

    if best_candidate.get("contradictory"):
        return {
            "rank": "review_required",
            "reason": "diagnostic contradictions present",
            "contradictions": best_candidate["contradictory"],
        }

    if best_candidate.get("coverage", 0.0) < 0.3:
        return {
            "rank": "unresolved",
            "reason": "coverage below threshold",
            "coverage": best_candidate["coverage"],
        }

    if not species_diagnostic_satisfied:
        return {
            "rank": "genus",
            "reason": "species-diagnostic characters not established; "
                      "broader rank supported",
        }

    if not required_references_completed:
        return {
            "rank": "candidate_species",
            "reason": "species diagnostics met; reference comparison incomplete",
        }

    if not independent_review:
        return {
            "rank": "candidate_species",
            "reason": "reference comparison complete; awaiting independent review",
        }

    return {
        "rank": "provisional_species",
        "reason": "species diagnostics, reference comparisons, and "
                  "independent review all present",
    }

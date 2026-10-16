"""Structured result for an identification run."""
from typing import Dict, Any, List, Optional
import time
import uuid

VALID_RANKS = (
    "unresolved",
    "candidate_species",
    "provisional_species",
    "review_required",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "kingdom",
)


def make_run(
    specimen_id: str,
    input_image_hashes: List[str],
    observation_revision: str,
    reference_pack_version: str,
    matcher_version: str,
    candidates: List[Dict[str, Any]],
    decision_rank: str,
    review_status: str = "unreviewed",
    context_assumptions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if decision_rank not in VALID_RANKS:
        raise ValueError(f"decision_rank must be one of {VALID_RANKS}")
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "specimen_id": specimen_id,
        "input_image_hashes": input_image_hashes,
        "observation_revision": observation_revision,
        "reference_pack_version": reference_pack_version,
        "matcher_version": matcher_version,
        "candidates": candidates,
        "decision_rank": decision_rank,
        "review_status": review_status,
        "context_assumptions": context_assumptions or {},
    }

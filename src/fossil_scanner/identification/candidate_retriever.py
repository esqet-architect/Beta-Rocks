"""
Broad candidate retrieval.

Combines multiple retrieval channels and merges their results. No single
channel decides; each contributes candidates to a pool that the character
matcher then evaluates.
"""
from typing import Dict, Any, List, Optional


def retrieve_by_shape(
    query_descriptor: Dict[str, Any],
    reference_descriptors: List[Dict[str, Any]],
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    """
    Rank reference descriptors by a simple weighted similarity. Shape
    comparison is one channel, never the sole basis for a name.
    """
    def similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
        score = 0.0
        n = 0
        fa = a.get("fold_angle_deg")
        fb = b.get("fold_angle_deg")
        if fa is not None and fb is not None:
            n += 1
            diff = abs(fa - fb)
            score += max(0.0, 1.0 - diff / 180.0)
        ea = a.get("endpoint_proximity", {}).get("end_gap_fraction")
        eb = b.get("endpoint_proximity", {}).get("end_gap_fraction")
        if ea is not None and eb is not None:
            n += 1
            score += max(0.0, 1.0 - abs(ea - eb))
        sa = a.get("bilateral_similarity", {}).get("symmetry_score")
        sb = b.get("bilateral_similarity", {}).get("symmetry_score")
        if sa is not None and sb is not None:
            n += 1
            score += max(0.0, 1.0 - abs(sa - sb))
        return score / n if n else 0.0

    ranked = []
    for ref in reference_descriptors:
        s = similarity(query_descriptor, ref)
        ranked.append({"taxon_id": ref.get("taxon_id"), "shape_score": round(s, 4)})
    ranked.sort(key=lambda r: r["shape_score"], reverse=True)
    return ranked[:top_k]


def merge_candidates(*channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Union candidate taxon_ids from each channel, retaining each channel's
    score under a namespaced key.
    """
    pool: Dict[str, Dict[str, Any]] = {}
    for channel in channels:
        for item in channel:
            tid = item.get("taxon_id")
            if not tid:
                continue
            entry = pool.setdefault(tid, {"taxon_id": tid, "channels": {}})
            for k, v in item.items():
                if k == "taxon_id":
                    continue
                entry["channels"][k] = v
    return list(pool.values())

"""
Golden-ratio analysis.

Measures the ratio between two selected lengths, reports deviation from phi,
and exposes sensitivity to landmark uncertainty.

The output is explicitly NOT a claim that the specimen 'is golden'. It is a
measurement with a tolerance.
"""
import math
from typing import Dict, Any, Optional, Tuple, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0  # 1.6180339887...


def ratio(a: float, b: float) -> Optional[float]:
    if b == 0:
        return None
    return a / b if a >= b else b / a


def deviation_from_phi(r: Optional[float]) -> Optional[float]:
    if r is None:
        return None
    return 100.0 * abs(r - PHI) / PHI


def analyze_pair(
    name_a: str,
    length_a: float,
    name_b: str,
    length_b: float,
    uncertainty_a: float = 0.0,
    uncertainty_b: float = 0.0,
) -> Dict[str, Any]:
    """
    Report the ratio between two lengths, its deviation from phi, and a
    bounding interval from the supplied uncertainties.
    """
    if length_a <= 0 or length_b <= 0:
        return {"status": "invalid", "reason": "lengths must be positive"}

    r = ratio(length_a, length_b)
    dev = deviation_from_phi(r)

    # Propagate uncertainty to the ratio interval (first-order).
    a_lo, a_hi = max(0.0, length_a - uncertainty_a), length_a + uncertainty_a
    b_lo, b_hi = max(0.0, length_b - uncertainty_b), length_b + uncertainty_b
    candidates = []
    for aa in (a_lo, a_hi):
        for bb in (b_lo, b_hi):
            if aa > 0 and bb > 0:
                candidates.append(ratio(aa, bb))
    r_min = min(candidates) if candidates else r
    r_max = max(candidates) if candidates else r

    return {
        "status": "ok",
        "phi": PHI,
        "lengths": {name_a: length_a, name_b: length_b},
        "uncertainties": {name_a: uncertainty_a, name_b: uncertainty_b},
        "ratio": round(r, 6),
        "deviation_percent": round(dev, 4),
        "ratio_interval": [round(r_min, 6), round(r_max, 6)],
        "phi_within_interval": r_min <= PHI <= r_max,
        "note": (
            "Deviation is a measurement. It does not imply biological "
            "origin or a specific physical mechanism."
        ),
    }


def scan_all_pairs(
    landmarks: Dict[str, Tuple[float, float, float]],
) -> List[Dict[str, Any]]:
    """
    Given a dict of named landmark positions in 3D, compute the pairwise
    distances and evaluate every pair against phi.
    """
    names = list(landmarks.keys())
    results = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = landmarks[names[i]]
            b = landmarks[names[j]]
            d = math.dist(a, b)
            for k in range(len(names)):
                if k in (i, j):
                    continue
                c = landmarks[names[k]]
                d2 = math.dist(a, c)
                if d2 == 0 or d == 0:
                    continue
                r = ratio(d, d2)
                if r is None:
                    continue
                dev = deviation_from_phi(r)
                results.append({
                    "pair": [names[i], names[k]],
                    "reference": names[j],
                    "ratio": round(r, 6),
                    "deviation_percent": round(dev, 4),
                    "nearest_phi": dev < 2.0,
                })
    results.sort(key=lambda x: x["deviation_percent"])
    return results


def spiral_classify(points: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Fit a general logarithmic spiral r = a * exp(b * theta) and compare to
    a golden-constrained version. Returns a descriptive result; it does not
    assert 'golden spiral'.
    """
    if len(points) < 4:
        return {"status": "insufficient_points", "count": len(points)}

    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    thetas = []
    log_rs = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        if r <= 0:
            continue
        theta = math.atan2(dy, dx)
        thetas.append(theta)
        log_rs.append(math.log(r))

    n = len(thetas)
    if n < 4:
        return {"status": "degenerate"}

    mean_t = sum(thetas) / n
    mean_lr = sum(log_rs) / n
    num = sum((t - mean_t) * (lr - mean_lr) for t, lr in zip(thetas, log_rs))
    den = sum((t - mean_t) ** 2 for t in thetas)
    if den == 0:
        return {"status": "degenerate"}
    b = num / den
    b_golden = math.log(PHI) / (math.pi / 2)
    return {
        "status": "ok",
        "b_fitted": round(b, 6),
        "b_golden_constrained": round(b_golden, 6),
        "difference": round(b - b_golden, 6),
        "note": (
            "A fitted logarithmic spiral is not automatically a golden "
            "spiral. The comparison is provided so the reader can judge."
        ),
    }

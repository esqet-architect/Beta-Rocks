"""
Magnetic field statistics.

Retains the full XYZ vector for every observation in addition to the scalar
magnitude. Vector information supports later direction-aware analysis
(delta_Bx, delta_By, delta_Bz, orientation of local anomaly).

Absent measurements are represented as None, not zero.
"""
import math
import statistics
from typing import List, Dict, Any, Optional


def _mad(values: List[float]) -> float:
    if not values:
        return 0.0
    med = statistics.median(values)
    return statistics.median([abs(v - med) for v in values])


def _robust_sigma(mad_value: float) -> float:
    return 1.4826 * mad_value


def process_magnetic_samples(samples: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Compute descriptive statistics for a burst of magnetometer samples.
    Returns None-valued fields when no samples were acquired.
    """
    if not samples:
        return {
            "count": 0,
            "magnitude": {
                "mean_uT": None,
                "median_uT": None,
                "stddev_uT": None,
                "mad_uT": None,
                "robust_sigma_uT": None,
            },
            "vector_mean": {"x_uT": None, "y_uT": None, "z_uT": None},
        }

    mags: List[float] = []
    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []
    for s in samples:
        x = float(s.get("x", 0.0))
        y = float(s.get("y", 0.0))
        z = float(s.get("z", 0.0))
        xs.append(x)
        ys.append(y)
        zs.append(z)
        mags.append(math.sqrt(x * x + y * y + z * z))

    mad_mag = _mad(mags)
    return {
        "count": len(mags),
        "magnitude": {
            "mean_uT": round(statistics.mean(mags), 4),
            "median_uT": round(statistics.median(mags), 4),
            "stddev_uT": round(statistics.stdev(mags), 4) if len(mags) > 1 else 0.0,
            "mad_uT": round(mad_mag, 4),
            "robust_sigma_uT": round(_robust_sigma(mad_mag), 4),
        },
        "vector_mean": {
            "x_uT": round(statistics.mean(xs), 4),
            "y_uT": round(statistics.mean(ys), 4),
            "z_uT": round(statistics.mean(zs), 4),
        },
    }


def anomaly_classification(
    magnitude_uT: Optional[float],
    center_uT: Optional[float],
    scale_uT: Optional[float],
    threshold: float = 3.0,
) -> Dict[str, Any]:
    """
    Robust-z anomaly scoring. Returns 'indeterminate' with a reason when the
    inputs cannot support a classification, rather than defaulting to 'none'.
    """
    if magnitude_uT is None or center_uT is None:
        return {
            "method": "robust_z",
            "center_uT": center_uT,
            "scale_uT": scale_uT,
            "z": None,
            "classification": "indeterminate",
            "reason": "missing magnitude or baseline",
            "threshold": threshold,
        }
    if scale_uT is None or scale_uT <= 0:
        return {
            "method": "robust_z",
            "center_uT": round(center_uT, 4),
            "scale_uT": scale_uT,
            "z": None,
            "classification": "indeterminate",
            "reason": "nonpositive or missing baseline scale",
            "threshold": threshold,
        }
    z = (magnitude_uT - center_uT) / scale_uT
    if z >= threshold:
        cls = "positive_anomaly"
    elif z <= -threshold:
        cls = "negative_anomaly"
    else:
        cls = "none"
    return {
        "method": "robust_z",
        "center_uT": round(center_uT, 4),
        "scale_uT": round(scale_uT, 4),
        "z": round(z, 4),
        "classification": cls,
        "threshold": threshold,
    }

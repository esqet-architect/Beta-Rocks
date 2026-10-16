"""
Shape descriptors for specimen silhouettes and 3D geometry.

Descriptors are rotation- and scale-invariant where possible, and retain
the original landmark coordinates for reproducible comparison.
"""
import math
from typing import List, Tuple, Dict, Any, Optional

Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]


def centroid(points: List[Point2D]) -> Point2D:
    n = len(points)
    if n == 0:
        return (0.0, 0.0)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)


def curvature_profile(points: List[Point2D]) -> List[float]:
    """
    Discrete curvature at each interior point using the turning angle
    between successive segments.
    """
    out = []
    for i in range(1, len(points) - 1):
        a, b, c = points[i - 1], points[i], points[i + 1]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        n1 = math.hypot(*v1) or 1e-12
        n2 = math.hypot(*v2) or 1e-12
        cos_t = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
        cos_t = max(-1.0, min(1.0, cos_t))
        out.append(math.acos(cos_t))
    return out


def fold_angle(points: List[Point2D]) -> Optional[float]:
    """
    Estimate the fold angle of a C- or U-shaped silhouette by locating the
    point of maximum curvature and measuring the angle between the two
    resulting tangent directions.
    """
    if len(points) < 5:
        return None
    curv = curvature_profile(points)
    if not curv:
        return None
    idx = max(range(len(curv)), key=lambda i: curv[i]) + 1
    if idx < 2 or idx >= len(points) - 2:
        return None
    a = points[idx - 2]
    b = points[idx]
    c = points[idx + 2]
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(*v1) or 1e-12
    n2 = math.hypot(*v2) or 1e-12
    cos_t = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    cos_t = max(-1.0, min(1.0, cos_t))
    return math.degrees(math.acos(cos_t))


def endpoint_proximity(points: List[Point2D], radius_fraction: float = 0.15) -> Dict[str, Any]:
    """
    For a folded silhouette, measure how close the two ends are relative to
    the total path length. A closed fold has a small ratio; an open arc has
    a large one.
    """
    if len(points) < 3:
        return {"status": "insufficient_points"}
    path_len = 0.0
    for i in range(1, len(points)):
        path_len += math.dist(points[i - 1], points[i])
    if path_len == 0:
        return {"status": "degenerate"}
    end_gap = math.dist(points[0], points[-1])
    return {
        "status": "ok",
        "path_length": round(path_len, 4),
        "end_gap": round(end_gap, 4),
        "end_gap_fraction": round(end_gap / path_len, 4),
        "closed_fold": end_gap / path_len < radius_fraction,
    }


def bilateral_similarity(points: List[Point2D]) -> Dict[str, Any]:
    """
    Measure asymmetry of a silhouette about its principal axis. Returns 1.0
    for a perfectly symmetric shape and approaches 0.0 for a fully
    asymmetric one.
    """
    if len(points) < 4:
        return {"status": "insufficient_points"}
    cx, cy = centroid(points)
    sxx = sum((p[0] - cx) ** 2 for p in points)
    syy = sum((p[1] - cy) ** 2 for p in points)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in points)
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    left = []
    right = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        perp = -sin_t * dx + cos_t * dy
        if perp >= 0:
            left.append(perp)
        else:
            right.append(-perp)
    if not left or not right:
        return {"status": "degenerate"}
    left_sorted = sorted(left, reverse=True)
    right_sorted = sorted(right, reverse=True)
    n = min(len(left_sorted), len(right_sorted))
    diff = sum(abs(left_sorted[i] - right_sorted[i]) for i in range(n)) / n
    scale = max(max(left_sorted[:n]), max(right_sorted[:n])) or 1e-12
    asymmetry = diff / scale
    return {
        "status": "ok",
        "asymmetry": round(asymmetry, 4),
        "symmetry_score": round(max(0.0, 1.0 - asymmetry), 4),
    }


def describe_shape(points: List[Point2D]) -> Dict[str, Any]:
    """Aggregate descriptor for a 2D silhouette."""
    return {
        "point_count": len(points),
        "fold_angle_deg": fold_angle(points),
        "endpoint_proximity": endpoint_proximity(points),
        "bilateral_similarity": bilateral_similarity(points),
    }

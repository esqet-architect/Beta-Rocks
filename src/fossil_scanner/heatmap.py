"""
Heatmap generation from survey observations.

Renders measured points only. Does not interpolate between points to
manufacture coverage that was never measured.
"""
import os
from typing import Dict, Any, List, Optional


def observations_to_points(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    points = []
    for obs in observations:
        gps = obs.get("gps") or {}
        if gps.get("status") != "acquired" or gps.get("latitude") is None:
            continue
        points.append({
            "observation_id": obs.get("observation_id"),
            "latitude": gps.get("latitude"),
            "longitude": gps.get("longitude"),
            "magnitude_uT": obs.get("field", {}).get("magnitude_uT"),
            "accuracy_m": gps.get("accuracy_m"),
            "visibility": gps.get("visibility"),
            "timestamp_utc": obs.get("timestamp_utc"),
        })
    return points


def export_geojson(points: List[Dict[str, Any]], out_path: str) -> str:
    import json
    features = []
    for p in points:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p["longitude"], p["latitude"]],
            },
            "properties": {
                "observation_id": p["observation_id"],
                "magnitude_uT": p["magnitude_uT"],
                "accuracy_m": p["accuracy_m"],
                "visibility": p["visibility"],
                "timestamp_utc": p["timestamp_utc"],
            },
        })
    fc = {"type": "FeatureCollection", "features": features}
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(fc, f, indent=2)
    return out_path

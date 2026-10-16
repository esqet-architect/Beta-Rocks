"""
GPS acquisition with explicit accuracy retention and privacy visibility.

Never silently rounds coordinates. If a visibility policy is applied, it is
recorded alongside the (possibly redacted) coordinates.

Exception: 'withheld' clears accuracy along with coordinates and altitude.
This exception is intentional and documented.
"""
import datetime
from typing import Dict, Any

from .sensors import read_termux_gps


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def acquire_gps_point(visibility: str = "exact") -> Dict[str, Any]:
    if visibility not in ("exact", "generalized", "withheld"):
        raise ValueError("visibility must be exact, generalized, or withheld")
    gps_res = read_termux_gps()
    ts = _utcnow_iso()

    if not gps_res.get("available"):
        return {
            "timestamp_utc": ts,
            "status": "unavailable",
            "reason": gps_res.get("reason", "GPS hardware or API unavailable"),
            "visibility": visibility,
        }

    data = gps_res.get("data", {})
    lat = data.get("latitude")
    lon = data.get("longitude")
    alt = data.get("altitude")
    acc = data.get("accuracy")
    redacted = False

    if visibility == "generalized" and lat is not None and lon is not None:
        lat = round(lat, 2)
        lon = round(lon, 2)
        redacted = True
    elif visibility == "withheld":
        lat, lon, alt, acc = None, None, None, None
        redacted = True

    return {
        "timestamp_utc": ts,
        "status": "acquired",
        "latitude": lat,
        "longitude": lon,
        "altitude_m": alt,
        "accuracy_m": acc,
        "provider": data.get("provider", "gps"),
        "visibility": visibility,
        "redacted": redacted,
    }

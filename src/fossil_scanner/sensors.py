"""
Tier-1 sensor access via Termux:API.

Never raises on hardware absence; returns {'available': False, 'reason': ...}
so the caller can record the failure as a first-class observation.
"""
import json
import subprocess
from typing import Dict, Any


def check_termux_api() -> bool:
    try:
        res = subprocess.run(
            ["termux-sensor", "-h"],
            capture_output=True, text=True, timeout=5
        )
        return res.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def read_termux_magnetometer(samples: int = 15) -> Dict[str, Any]:
    """
    Return a structured acquisition result:
    {
        available: bool,
        samples: [ {x,y,z}, ... ],
        reason: str | None,
        raw: dict | None,
    }
    """
    if not check_termux_api():
        return {"available": False, "samples": [], "reason": "termux-sensor API unavailable", "raw": None}
    try:
        cmd = ["termux-sensor", "-s", "magnetometer", "-n", str(samples)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0 or not res.stdout.strip():
            return {
                "available": False,
                "samples": [],
                "reason": res.stderr.strip() or "Empty sensor response",
                "raw": None,
            }
        raw = json.loads(res.stdout)
        parsed = _parse_termux_magnetometer(raw)
        return {
            "available": True,
            "samples": parsed,
            "reason": None,
            "raw": raw,
        }
    except Exception as e:
        return {"available": False, "samples": [], "reason": str(e), "raw": None}


def _parse_termux_magnetometer(raw: Any) -> list:
    """Normalize Termux sensor output into a list of {x,y,z} dicts."""
    out = []
    if isinstance(raw, dict):
        for _key, val in raw.items():
            if isinstance(val, dict) and "values" in val:
                for v in val["values"] if isinstance(val["values"], list) and val["values"] and isinstance(val["values"][0], list) else [val["values"]]:
                    if len(v) >= 3:
                        out.append({"x": float(v[0]), "y": float(v[1]), "z": float(v[2])})
    return out


def read_termux_gps(provider: str = "gps", timeout_sec: int = 10) -> Dict[str, Any]:
    if not check_termux_api():
        return {"available": False, "reason": "termux-location API unavailable"}
    try:
        cmd = ["termux-location", "-p", provider, "-r", "once"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if res.returncode == 0 and res.stdout.strip():
            return {"available": True, "data": json.loads(res.stdout)}
        return {"available": False, "reason": res.stderr.strip() or "No GPS fix"}
    except Exception as e:
        return {"available": False, "reason": str(e)}

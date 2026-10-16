"""
Preflight check.

Runs every registered device probe, tests storage read/write, checks
optional environmental feeds, and returns a structured status report.

The report distinguishes:
- available and tested
- available but untested
- unavailable with reason

It never reports 'all clear' for a subsystem it did not actually test.
"""
import os
import shutil
import time
from typing import Dict, Any, List

from .registry import DeviceRegistry, default_registry
from .base import DeviceStatus
from ..schema import append_jsonl


def _storage_check(work_dir: str) -> Dict[str, Any]:
    os.makedirs(work_dir, exist_ok=True)
    probe_path = os.path.join(work_dir, ".preflight_probe")
    try:
        with open(probe_path, "w") as f:
            f.write("ok")
            f.flush()
            os.fsync(f.fileno())
        with open(probe_path) as f:
            read_back = f.read()
        os.unlink(probe_path)
        ok = read_back == "ok"
        return {"status": "ok" if ok else "mismatch", "path": work_dir}
    except Exception as e:
        return {"status": "error", "reason": str(e), "path": work_dir}


def _disk_free(work_dir: str) -> Dict[str, Any]:
    try:
        usage = shutil.disk_usage(work_dir)
        return {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "free_gb": round(usage.free / (1024 ** 3), 2),
        }
    except Exception as e:
        return {"error": str(e)}


def _battery_status() -> Dict[str, Any]:
    """
    Termux does not expose battery via a standard API. We attempt
    termux-battery-status and report 'untested' if unavailable.
    """
    import subprocess, json
    try:
        res = subprocess.run(
            ["termux-battery-status"],
            capture_output=True, text=True, timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            return {"status": "ok", "data": json.loads(res.stdout)}
        return {"status": "unavailable", "reason": res.stderr.strip() or "no output"}
    except Exception as e:
        return {"status": "unavailable", "reason": str(e)}


def run_preflight(
    work_dir: str,
    registry: DeviceRegistry = None,
    log_dir: str = None,
) -> Dict[str, Any]:
    registry = registry or default_registry
    report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "work_dir": work_dir,
        "storage": {
            "read_write": _storage_check(work_dir),
            "capacity": _disk_free(work_dir),
        },
        "battery": _battery_status(),
        "devices": [],
        "summary": {
            "total": 0,
            "available": 0,
            "untested": 0,
            "unavailable": 0,
        },
    }
    for device in registry.all():
        try:
            status = device.probe()
        except Exception as e:
            status = DeviceStatus(
                name=device.name,
                kind=device.kind,
                available=False,
                tested=False,
                reason=f"probe raised: {e}",
            )
        report["devices"].append(status.to_dict())
        report["summary"]["total"] += 1
        if not status.available:
            report["summary"]["unavailable"] += 1
        elif not status.tested:
            report["summary"]["untested"] += 1
        else:
            report["summary"]["available"] += 1

    if log_dir:
        append_jsonl(os.path.join(log_dir, "preflight.jsonl"), report)
    return report


def format_preflight_report(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append(" PREFLIGHT STATUS REPORT")
    lines.append(f" Generated: {report.get('timestamp_utc')}")
    lines.append("=" * 72)
    s = report.get("summary", {})
    lines.append(
        f" Devices: {s.get('available',0)} ready, "
        f"{s.get('untested',0)} untested, "
        f"{s.get('unavailable',0)} unavailable "
        f"(total {s.get('total',0)})"
    )
    lines.append("")
    lines.append(" Storage:")
    rw = report["storage"]["read_write"]
    lines.append(f"   read/write: {rw.get('status')} ({rw.get('path')})")
    cap = report["storage"]["capacity"]
    if "free_gb" in cap:
        lines.append(
            f"   free: {cap['free_gb']} GB of "
            f"{round(cap['total_bytes'] / (1024 ** 3), 2)} GB"
        )
    lines.append(f" Battery: {report['battery'].get('status')}")
    lines.append("")
    lines.append(" Devices:")
    for d in report["devices"]:
        state = "READY" if d["available"] and d["tested"] else (
            "PRESENT-UNTESTED" if d["available"] else "UNAVAILABLE"
        )
        line = f"   [{state:>16}] {d['name']} ({d['kind']})"
        if d.get("reason"):
            line += f" - {d['reason']}"
        lines.append(line)
    lines.append("=" * 72)
    return "\n".join(lines)

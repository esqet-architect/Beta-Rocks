"""High-level photogrammetry workflow (external reconstruction)."""
from typing import Dict, Any, List, Optional

from .colmap_bridge import export_image_set, suggested_colmap_commands


def prepare_reconstruction(
    specimen_dir: str,
    out_dir: str,
    image_records: List[Dict[str, Any]],
    masks_dir: Optional[str] = None,
) -> Dict[str, Any]:
    manifest = export_image_set(specimen_dir, out_dir, image_records, masks_dir)
    commands = suggested_colmap_commands(out_dir)
    return {
        "manifest": manifest,
        "commands": commands,
        "status": "prepared",
        "note": (
            "Reconstruction must run externally. This package does not "
            "claim that a sparse point cloud is a finished scan."
        ),
    }

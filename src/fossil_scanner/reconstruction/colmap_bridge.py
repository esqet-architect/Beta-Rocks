"""
COLMAP bridge.

Exports an image set for external reconstruction, generates a suggested
mask configuration, and provides a helper command list.

The bridge does not run COLMAP on-device. It prepares a directory that a
workstation can consume.
"""
import json
import os
import shutil
from typing import Dict, Any, List, Optional


def export_image_set(
    specimen_dir: str,
    out_dir: str,
    image_records: List[Dict[str, Any]],
    masks_dir: Optional[str] = None,
) -> Dict[str, Any]:
    images_out = os.path.join(out_dir, "images")
    os.makedirs(images_out, exist_ok=True)

    copied = []
    for rec in image_records:
        src = rec["path"]
        if not os.path.exists(src):
            continue
        dst = os.path.join(images_out, os.path.basename(src))
        shutil.copy2(src, dst)
        copied.append({
            "image_id": rec["image_id"],
            "filename": os.path.basename(src),
            "sha256": rec["sha256"],
            "view_label": rec.get("view_label"),
            "turntable_angle_deg": rec.get("turntable_angle_deg"),
        })

    masks_out = None
    if masks_dir and os.path.isdir(masks_dir):
        masks_out = os.path.join(out_dir, "masks")
        os.makedirs(masks_out, exist_ok=True)
        for rec in image_records:
            base = os.path.splitext(os.path.basename(rec["path"]))[0]
            candidate = os.path.join(masks_dir, base + ".png")
            if os.path.exists(candidate):
                shutil.copy2(candidate, os.path.join(masks_out, base + ".png"))

    manifest = {
        "image_count": len(copied),
        "images": copied,
        "masks_provided": masks_out is not None,
        "notes": (
            "Turntable photogrammetry with a stationary background "
            "requires masks. Reconstruction with unmasked background "
            "features may produce unreliable geometry."
        ),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def suggested_colmap_commands(out_dir: str) -> List[str]:
    """Return the command list a workstation would run."""
    return [
        f"colmap feature_extractor --database_path {out_dir}/database.db "
        f"--image_path {out_dir}/images --ImageReader.mask_path {out_dir}/masks",
        f"colmap exhaustive_matcher --database_path {out_dir}/database.db",
        f"colmap mapper --database_path {out_dir}/database.db "
        f"--image_path {out_dir}/images --output_path {out_dir}/sparse",
        f"colmap image_undistorter --image_path {out_dir}/images "
        f"--input_path {out_dir}/sparse/0 --output_path {out_dir}/dense",
        f"colmap patch_match_stereo --workspace_path {out_dir}/dense",
        f"colmap stereo_fusion --workspace_path {out_dir}/dense "
        f"--output_path {out_dir}/dense/fused.ply",
    ]

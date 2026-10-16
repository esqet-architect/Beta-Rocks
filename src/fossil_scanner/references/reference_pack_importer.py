"""
Reference pack importer.

A pack is a directory containing:
    manifest.json
    references.sqlite (optional pre-built)
    media/ (images, models)
    attributions.json

The importer verifies the manifest checksum against the directory contents,
then either opens a pre-built SQLite or builds one from JSON sidecar files.
"""
import hashlib
import json
import os
from typing import Dict, Any, Optional

from .reference_repository import ReferenceRepository


def _dir_checksum(path: str) -> str:
    """Deterministic hash of all file paths and contents in a directory."""
    sha = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for fname in sorted(files):
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, path)
            sha.update(rel.encode("utf-8"))
            with open(full, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha.update(chunk)
    return sha.hexdigest()


def load_manifest(pack_dir: str) -> Dict[str, Any]:
    with open(os.path.join(pack_dir, "manifest.json")) as f:
        return json.load(f)


def install_pack(pack_dir: str, target_db_path: str) -> Dict[str, Any]:
    if not os.path.isdir(pack_dir):
        return {"success": False, "reason": "pack directory not found"}
    try:
        manifest = load_manifest(pack_dir)
    except Exception as e:
        return {"success": False, "reason": f"manifest error: {e}"}

    checksum = _dir_checksum(pack_dir)
    if manifest.get("checksum") and manifest["checksum"] != checksum:
        return {
            "success": False,
            "reason": "checksum mismatch",
            "expected": manifest["checksum"],
            "computed": checksum,
        }

    repo = ReferenceRepository(target_db_path)
    repo.install_manifest(
        pack_id=manifest.get("pack_id", "unknown"),
        version=manifest.get("version", "0.0.0"),
        source=manifest.get("source", ""),
        checksum=checksum,
    )

    taxa_file = os.path.join(pack_dir, "taxa.json")
    if os.path.exists(taxa_file):
        with open(taxa_file) as f:
            for taxon in json.load(f):
                repo.add_taxon(taxon)

    rules_file = os.path.join(pack_dir, "character_rules.json")
    if os.path.exists(rules_file):
        with open(rules_file) as f:
            for entry in json.load(f):
                for rule in entry.get("rules", []):
                    repo.add_character_rule(entry["taxon_id"], rule)

    repo.close()
    return {
        "success": True,
        "pack_id": manifest.get("pack_id"),
        "version": manifest.get("version"),
        "checksum": checksum,
        "db_path": target_db_path,
    }

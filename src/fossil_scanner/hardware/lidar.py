"""
LiDAR / point-cloud / raster import.

This module preserves imported datasets and their metadata. It does not
render or analyze them on-device. Rendering belongs in a viewer; spatial
analysis belongs in a GIS pipeline.

Supported inputs:
- .las / .laz point clouds (metadata only; parsing is delegated)
- .tif / .tiff DEM rasters
- .kml / .kmz overlays
- .geojson vector layers
"""
import os
from typing import Dict, Any, Optional, List

from .base import HardwareDevice, DeviceStatus
from ..hashing import hash_file

SUPPORTED_EXTENSIONS = (".las", ".laz", ".tif", ".tiff", ".kml", ".kmz", ".geojson", ".json")


class LidarDataset:
    def __init__(self, path: str, source: str = "", crs: str = "", datum: str = ""):
        self.path = path
        self.source = source
        self.crs = crs
        self.datum = datum
        self.sha256 = hash_file(path) if os.path.exists(path) else None
        self.bytes = os.path.getsize(path) if os.path.exists(path) else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "filename": os.path.basename(self.path),
            "source": self.source,
            "crs": self.crs,
            "datum": self.datum,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "extension": os.path.splitext(self.path)[1].lower(),
        }


class LidarDevice(HardwareDevice):
    """
    LiDAR here is a dataset registry, not a live sensor. The device
    abstraction is used so preflight can report whether a LiDAR dataset
    has been loaded for the current session.
    """

    def __init__(self):
        self._datasets: List[LidarDataset] = []

    @property
    def name(self) -> str:
        return "lidar"

    @property
    def kind(self) -> str:
        return "dataset"

    def probe(self) -> DeviceStatus:
        return DeviceStatus(
            name=self.name,
            kind=self.kind,
            available=True,
            tested=False,
            reason="dataset registry (no live sensor)",
            details={"loaded": len(self._datasets)},
        )

    def initialize(self) -> bool:
        return True

    def import_dataset(self, path: str, source: str = "", crs: str = "", datum: str = "") -> Dict[str, Any]:
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return {
                "success": False,
                "reason": f"unsupported extension {ext}",
                "supported": list(SUPPORTED_EXTENSIONS),
            }
        if not os.path.exists(path):
            return {"success": False, "reason": "file not found"}
        ds = LidarDataset(path, source=source, crs=crs, datum=datum)
        self._datasets.append(ds)
        return {"success": True, "dataset": ds.to_dict()}

    def list_datasets(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._datasets]

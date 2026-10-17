#!/usr/bin/env python3
"""
ESQET CORE: Module 5 - Rig Orchestrator (GPS + Heatmap Enabled)
"""
import time
import json
import datetime
import os
import subprocess

class FossilRigController:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.specimen_id = f"FS-{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        self.steps = 4 # Reduced for testing
        self.record = {
            "specimen_id": self.specimen_id,
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "gps": self.get_gps(),
            "scans": []
        }

    def get_gps(self):
        """Fetches GPS via Termux API."""
        if self.dry_run:
            return {"lat": 39.7392, "lon": -104.9903, "alt": 1600, "status": "simulated"}
        try:
            # Requires termux-api
            res = subprocess.check_output(["termux-location", "-p", "gps"], timeout=10)
            data = json.loads(res)
            return {
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "alt": data.get("altitude"),
                "status": "acquired"
            }
        except Exception as e:
            return {"status": f"failed: {e}"}

    def trigger_hardware(self, action, payload=None):
        if self.dry_run:
            print(f"  [HW] {action} {payload if payload else ''}")
            time.sleep(0.2)
            return True

    def capture_optical(self, angle, spectrum):
        return f"{self.specimen_id}_{angle}deg_{spectrum}.jpg"

    def poll_sensors(self):
        return {
            "magnetic_uT": 45.2 + (time.time() % 1), # Simulating slight variation
            "acoustic_peaks": [440.0],
            "temp_c": 22.5
        }

    def run_scan_cycle(self):
        print(f"\n--- Initiating Rig Scan: {self.specimen_id} ---")
        print(f"GPS: {self.record['gps']['status']}")
        
        angles = [int(i * (360 / self.steps)) for i in range(self.steps)]
        
        for angle in angles:
            print(f"[Angle: {angle}°]")
            self.trigger_hardware("ROTATE", f"to {angle} degrees")
            
            self.trigger_hardware("SET_LIGHT", "RGB")
            rgb_img = self.capture_optical(angle, "RGB")
            
            sensors = self.poll_sensors()
            
            self.record["scans"].append({
                "angle": angle,
                "images": {"rgb": rgb_img},
                "telemetry": sensors
            })

        # Save to specimen folder
        out_dir = os.path.expanduser("~/Beta-Rocks/specimens")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{self.specimen_id}_rig_scan.json")
        
        with open(out_path, "w") as f:
            json.dump(self.record, f, indent=2)
            
        print(f"\n✅ Scan saved: {out_path}")
        self.update_heatmap()

    def update_heatmap(self):
        """Updates a master GeoJSON heatmap with this scan's location."""
        heatmap_path = os.path.expanduser("~/Beta-Rocks/specimens/field_heatmap.geojson")
        
        # Create base GeoJSON if it doesn't exist
        if not os.path.exists(heatmap_path):
            geojson = {"type": "FeatureCollection", "features": []}
        else:
            with open(heatmap_path, "r") as f:
                geojson = json.load(f)

        gps = self.record["gps"]
        if gps["status"] == "simulated" or gps["status"] == "acquired":
            # Extract average magnetic reading for the feature
            mags = [s["telemetry"]["magnetic_uT"] for s in self.record["scans"]]
            avg_mag = sum(mags) / len(mags) if mags else 0
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [gps["lon"], gps["lat"]]
                },
                "properties": {
                    "specimen_id": self.specimen_id,
                    "magnetic_uT": avg_mag,
                    "timestamp": self.record["timestamp_utc"]
                }
            }
            geojson["features"].append(feature)
            
            with open(heatmap_path, "w") as f:
                json.dump(geojson, f, indent=2)
            print(f"🗺️ Heatmap updated: {heatmap_path}")

if __name__ == "__main__":
    rig = FossilRigController(dry_run=True)
    rig.run_scan_cycle()

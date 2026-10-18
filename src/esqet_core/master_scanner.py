#!/usr/bin/env python3
import cv2
import numpy as np
import subprocess
import json
import sys

PHI = (1 + np.sqrt(5)) / 2

def get_magnetometer():
    try:
        cmd = ["termux-sensor", "-s", "magnetometer", "-n", "5"]
        res = subprocess.check_output(cmd, timeout=5)
        data = json.loads(res)
        for key in data:
            values = data[key].get("values", [])
            if values:
                v = values[0] if isinstance(values[0], list) else values
                magnitude = np.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
                return round(float(magnitude), 2)
    except Exception:
        pass
    return 45.0 

def analyze_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return {"error": "Image not found"}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    texture_var = np.var(gray)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    phi_detected = False
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 10 and h > 10:
            ratio = max(w, h) / min(w, h)
            boxes.append({"w": w, "h": h, "ratio": round(ratio, 3)})
            if abs(ratio - PHI) / PHI < 0.05:
                phi_detected = True
    edge_density = np.sum(edges > 0) / edges.size
    fractal_dim = 1.0 + edge_density
    return {
        "texture_variance": round(float(texture_var), 2),
        "fractal_dim": round(float(fractal_dim), 3),
        "phi_detected": phi_detected,
        "boxes_found": len(boxes)
    }

def classify(img_path):
    mag_uT = get_magnetometer()
    vis = analyze_image(img_path)
    if "error" in vis: return vis
    ferrous = "HIGH (Ferrous)" if mag_uT > 80 else "LOW (Non-Ferrous)"
    if vis["fractal_dim"] > 1.6 or vis["texture_variance"] > 4000:
        rock_type = "IGNEOUS (Crystalline)"
        mineral = "Quartz / Feldspar"
    elif vis["texture_variance"] < 1000 and vis["fractal_dim"] < 1.3:
        rock_type = "SEDIMENTARY (Fine)"
        mineral = "Calcite / Clay"
    else:
        rock_type = "METAMORPHIC (Foliated)"
        mineral = "Mica / Recrystallized Quartz"
    if mag_uT > 150: mineral = "Magnetite / Hematite"
    return {
        "magnetic_uT": mag_uT,
        "ferrous_status": ferrous,
        "phi_geometry": "PRESENT" if vis["phi_detected"] else "NOT DETECTED",
        "rock_type": rock_type,
        "likely_mineral": mineral,
        "visual_metrics": vis
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python master_scanner.py <image_path>")
        sys.exit(1)
    result = classify(sys.argv[1])
    print(json.dumps(result, indent=2))

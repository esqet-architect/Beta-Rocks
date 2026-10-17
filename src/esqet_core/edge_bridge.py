#!/usr/bin/env python3
"""ESQET CORE: Edge Bridge - image -> outline roughness profile -> EquationFinder."""
import argparse
import sys

import cv2
import numpy as np
from equation_finder import EquationFinder

N_POINTS = 512


def extract_profile(path, n=N_POINTS):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"Could not read image: {path}")

    blur = cv2.GaussianBlur(img, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    border = np.concatenate([mask[0], mask[-1], mask[:, 0], mask[:, -1]])
    if border.mean() > 127:
        mask = 255 - mask
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        sys.exit("No object found.")
    pts = max(contours, key=cv2.contourArea)[:, 0, :].astype(float)

    closed = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(closed, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=False)
    x = np.interp(t, s, closed[:, 0])
    y = np.interp(t, s, closed[:, 1])

    r = np.hypot(x - x.mean(), y - y.mean())
    w = max(5, n // 16) | 1
    padded = np.concatenate([r[-w:], r, r[:w]])
    trend = np.convolve(padded, np.ones(w) / w, mode="same")[w:-w]
    return r - trend


def main():
    ap = argparse.ArgumentParser(description="Edge roughness analysis")
    ap.add_argument("image")
    ap.add_argument("--energy", type=float, default=None,
                    help="break energy 0-1; omit to report D and z only")
    a = ap.parse_args()

    prof = extract_profile(a.image)
    f = EquationFinder()
    print(f"Analyzing: {a.image} ({prof.size} points)")

    if a.energy is None:
        d = f.higuchi_fd(prof)
        print(f"fractal_dimension: {d:.4f}")
        print(f"surrogate_z: {f.surrogate_z(prof, d):.2f}")
    else:
        for k, v in f.analyze_fracture(prof, a.energy).items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()

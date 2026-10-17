#!/usr/bin/env python3
"""
ESQET CORE: Module 4 - The Equation Finder
Fracture-edge analysis: Higuchi fractal dimension + surrogate null test.
Scale: D ~ 1 smooth curve, D ~ 2 white noise.
"""
import numpy as np


class EquationFinder:
    # Uncalibrated starting points; tune on real specimens.
    SMOOTH_D = 1.25
    ENERGY_MIN = 0.7

    def __init__(self, k_max=10, n_surrogates=200, seed=0):
        self.k_max = k_max
        self.n_surrogates = n_surrogates
        self.rng = np.random.default_rng(seed)

    def higuchi_fd(self, x, k_max=None):
        """Higuchi's fractal dimension of a 1D sequence (NaN if undefined)."""
        x = np.asarray(x, dtype=float)
        N = x.size
        k_max = min(k_max or self.k_max, N // 4)
        if N < 8 or k_max < 2 or np.ptp(x) == 0:
            return float("nan")

        ks, Ls = [], []
        for k in range(1, k_max + 1):
            Lk = []
            for m in range(k):
                idx = np.arange(m, N, k)
                n = len(idx) - 1  # number of increments
                if n < 1:
                    continue
                d = np.abs(np.diff(x[idx])).sum()
                Lk.append(d * (N - 1) / (n * k) / k)
            if Lk:
                ks.append(k)
                Ls.append(np.mean(Lk))

        slope = np.polyfit(np.log(1.0 / np.array(ks)), np.log(Ls), 1)[0]
        return float(slope)

    def surrogate_z(self, x, dim):
        """z-score of dim vs shuffled copies (destroys order, keeps values)."""
        x = np.asarray(x, dtype=float)
        ds = np.array([self.higuchi_fd(self.rng.permutation(x))
                       for _ in range(self.n_surrogates)])
        ds = ds[~np.isnan(ds)]
        if ds.size < 2 or ds.std() == 0:
            return float("nan")
        return float((dim - ds.mean()) / ds.std())

    def analyze_fracture(self, edge_sequence, break_energy):
        """
        edge_sequence: spatial deviations along the edge
        break_energy: normalized impact force, 0.0 to 1.0
        """
        dim = self.higuchi_fd(edge_sequence)
        if np.isnan(dim):
            return {"fate": "INDETERMINATE",
                    "interpretation": "Sequence too short or constant."}

        z = self.surrogate_z(edge_sequence, dim)

        if dim < self.SMOOTH_D and break_energy > self.ENERGY_MIN:
            fate, rule = "KNAPPED", "Directed Force Vector"
            meaning = "Smooth, ordered edge with high applied energy. Candidate artifact."
        elif dim < self.SMOOTH_D:
            fate, rule = "SETTLED", "Natural Weathering"
            meaning = "Smooth edge without high-energy signature. Rounded or aged."
        else:
            fate, rule = "CRUMBLED", "Impact Turbulence"
            meaning = "Rough, disordered edge. Debris."

        return {
            "fractal_dimension": round(dim, 5),
            "surrogate_z": None if np.isnan(z) else round(z, 2),
            "break_energy": break_energy,
            "fate": fate,
            "generator_rule": rule,
            "interpretation": meaning,
        }


if __name__ == "__main__":
    print("--- Testing Equation Finder ---")
    rng = np.random.default_rng(1)

    knapped_edge = np.sin(np.linspace(0, 2, 100)) * 0.1
    knapped_edge[50:] += 0.5
    crumbled_edge = rng.standard_normal(100) * 0.5
    weathered_edge = np.sin(np.linspace(0, 6, 100)) * 0.1

    finder = EquationFinder()
    for name, edge, e in [("Knapped", knapped_edge, 0.85),
                          ("Crumbled", crumbled_edge, 0.3),
                          ("Weathered", weathered_edge, 0.2)]:
        print(f"\n{name}:")
        print(finder.analyze_fracture(edge, break_energy=e))

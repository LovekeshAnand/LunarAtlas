"""Stand-in for revision_v2/analysis.py (removed from the working tree), providing only what the co-author's
species_corroboration scripts use: S (settings, verbatim from revision_v2/outputs/analysis/settings.json),
RAW, cleaned() and detect() (verbatim logic from revision_v2/analysis.py at commit 520e943).
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[4]          # repository root
S = dict(raw_dir="datasets/uploads", cal_min=220.0, cal_max=800.0, noise_min=560.0, noise_max=580.0,
         prominence_sigma=3.0, sigma_ddof=0, peak_distance_channels=5, match_tol_nm=0.5,
         fwhm_upper_bound_nm=1.1, worked_obs="ch3_lib_002_20230825T104221_00_l1", eval_ids=[1, 3, 4],
         null_draws=10000, null_shift_min_nm=2.0, null_shift_max_nm=20.0, null_seed=20261021)
RAW = ROOT / S["raw_dir"]
PROC = ROOT / "datasets" / "processed" / "calibrated"


def noise_sigma(wl, y):
    w = (wl >= S["noise_min"]) & (wl <= S["noise_max"])
    return float(np.std(y[w], ddof=S["sigma_ddof"]))


def detect(wl, y):
    """Calibrated-range peaks: prominence >= 3 sigma (560-580 nm, ddof=0), >= 5 channels apart."""
    sig = noise_sigma(wl, y)
    c = (wl >= S["cal_min"]) & (wl <= S["cal_max"])
    idx, props = find_peaks(y[c], prominence=S["prominence_sigma"] * sig, distance=S["peak_distance_channels"])
    return np.flatnonzero(c)[idx], props["prominences"], sig


def cleaned(obs, date):
    d = pd.read_csv(PROC / date / obs / f"{obs}_cleaned.csv")
    return {m: g.sort_values("Wavelength_nm") for m, g in d.groupby("Measurement_ID")}

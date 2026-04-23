"""
LunarAtlas Downsampling Engine
==============================

Implements the M4 (MinMaxMinMax) algorithm for spectral data downsampling,
optimised for Chandrayaan-3 LIBS spectroscopy.

Algorithm Theory
----------------
The M4 algorithm divides a dataset into non-overlapping buckets (determined
by zoom level and wavelength range) and extracts exactly four extreme points
per bucket:

    1. **First** — The first data point in the bucket (boundary context).
    2. **Min**   — The point with the lowest intensity in the bucket.
    3. **Max**   — The point with the highest intensity in the bucket.
    4. **Last**  — The last data point in the bucket (boundary context).

These four points are then deduplicated (if any coincide) and sorted by
wavelength to form a faithful visual envelope of the original data.

**Why M4 over LTTB?**
LTTB selects *one* representative point per bucket using triangle-area
maximisation. For spectral data where emission peaks can be 1–3 channels
wide, LTTB may discard scientifically critical peaks if their triangle
area is smaller than nearby baseline variation. M4 guarantees 100% peak
retention because the max-intensity point is always explicitly extracted.

**Complexity:** O(N) time, O(B) space where B = number of buckets.

References
----------
- Jugel et al., "M4: A Visualization-Oriented Time Series Data Aggregation",
  Proc. VLDB Endowment, Vol. 7, No. 10, 2014.
- LunarAtlas Technical Report, Section 5: Peak Preservation.

Author: LunarAtlas Data Processing Team
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DownsampleConfig:
    """
    Configuration parameters for the M4 downsampling algorithm.

    These parameters are calibrated specifically for Chandrayaan-3 LIBS
    data characteristics (2,094 wavelength channels per measurement,
    spanning 164.35–878.26 nm).

    Attributes
    ----------
    BASE_BUCKETS : int
        Number of buckets at zoom level z=0. With BASE_BUCKETS=200 and
        a ~714 nm spectral range, each bucket covers ~3.57 nm at z=0.
        This provides a ~10x data reduction while preserving all emission
        features wider than the bucket size.

        Zoom scaling: n_buckets(z) = BASE_BUCKETS × 2^z
            z=0 → 200 buckets  → ~10x   reduction
            z=1 → 400 buckets  → ~5x    reduction
            z=2 → 800 buckets  → ~2.6x  reduction
            z=3 → 1600 buckets → raw (saturation threshold)

    B_MIN : float
        Minimum bucket size in nanometres. This is floored at the
        instrument's spectral resolution (~0.01 nm for Chandrayaan-3
        LIBS) to prevent sub-resolution bucketing, which would produce
        empty buckets without any scientific benefit.
    """

    BASE_BUCKETS: int = 200
    B_MIN: float = 0.01  # nm — matches Chandrayaan-3 LIBS resolution


def calculate_bucket_size(
    delta_lambda: float,
    zoom_level: int,
    config: DownsampleConfig = DownsampleConfig()
) -> float:
    """
    Calculate the bucket width (in nm) for a given zoom level.

    Implements the zoom-adaptive bucket scaling formula:
        b_size(z) = Δλ / (BASE_BUCKETS × 2^z)
        b_final(z) = max(b_size(z), b_min)

    The minimum-size floor prevents sub-resolution bucketing when the
    user zooms deeply into a narrow spectral region.

    Parameters
    ----------
    delta_lambda : float
        The current viewport wavelength range in nm (λ_max − λ_min).
    zoom_level : int
        Discrete zoom level (0 = most zoomed out).
    config : DownsampleConfig
        Algorithm configuration parameters.

    Returns
    -------
    float
        Final bucket width in nm, guaranteed ≥ config.B_MIN.
    """
    b_size = delta_lambda / (config.BASE_BUCKETS * (2 ** zoom_level))
    b_final = max(b_size, config.B_MIN)
    return b_final


def calculate_zoom_max(
    delta_lambda: float,
    config: DownsampleConfig = DownsampleConfig(),
    n_points: int = 0
) -> int:
    """
    Calculate the maximum useful zoom level using dual saturation criteria.

    Two independent limits constrain how far the user can zoom before
    downsampling becomes pointless:

    1. **Instrument resolution limit:**
       z_instrument = ⌊log₂(Δλ / (BASE_BUCKETS × b_min))⌋
       Beyond this, bucket size clamps to the instrument resolution.

    2. **Data-density limit:**
       z_data = ⌊log₂(n_points / BASE_BUCKETS)⌋
       Beyond this, there are fewer data points than buckets, so
       downsampling would *upsample* — which is nonsensical.

    The effective maximum is: z_max = min(z_instrument, z_data)

    Parameters
    ----------
    delta_lambda : float
        Viewport wavelength range in nm.
    config : DownsampleConfig
        Algorithm configuration parameters.
    n_points : int
        Number of actual data points in the current range.
        If 0, the density limit is ignored.

    Returns
    -------
    int
        Maximum meaningful zoom level (≥ 0).
    """
    if delta_lambda <= 0:
        return 0

    # Limit 1: instrument resolution ceiling
    z_instrument = math.log2(
        delta_lambda / (config.BASE_BUCKETS * config.B_MIN)
    )

    # Limit 2: data density ceiling (if known)
    if n_points > 0 and n_points > config.BASE_BUCKETS:
        z_data = math.log2(n_points / config.BASE_BUCKETS)
    else:
        z_data = z_instrument  # no density constraint available

    z_max = max(0, int(min(z_instrument, z_data)))
    return z_max


def m4_downsample(
    data: np.ndarray,
    zoom_level: int,
    lambda_min: float,
    lambda_max: float,
    config: DownsampleConfig = DownsampleConfig()
) -> Dict:
    """
    M4 (MinMaxMinMax) downsampling algorithm.

    Processes spectral data in non-overlapping wavelength buckets,
    extracting up to four extreme points per bucket (First, Min, Max, Last)
    to guarantee perfect visual envelope preservation.

    The algorithm flow:
        1. Compute bucket width from zoom level and wavelength range.
        2. Check saturation: if n_buckets ≥ n_points, return raw data.
        3. For each bucket, mask data points that fall within [λ_start, λ_end).
        4. Extract indices: first, argmin(intensity), argmax(intensity), last.
        5. Deduplicate (any of the four may coincide) and sort by wavelength.
        6. Append the resulting 1–4 points to the output.

    Parameters
    ----------
    data : np.ndarray
        NumPy array of shape (N, 3) where columns are:
        0: wavelength_nm
        1: intensity (cleaned counts)
        2: raw_plasma (calibrated counts)
    zoom_level : int
        Current discrete zoom level (0 = most zoomed out).
    lambda_min : float
        Viewport minimum wavelength in nm.
    lambda_max : float
        Viewport maximum wavelength in nm.
    config : DownsampleConfig
        Algorithm configuration parameters.

    Returns
    -------
    dict
        Result dictionary containing:
        - mode: "downsampled" | "raw" | "empty" | "error"
        - data: list of {wavelength_nm, intensity} dicts (or raw arrays)
        - original_points: int
        - n_buckets: int
        - reduction_factor: float
        - z_max: int (maximum zoom before saturation)
    """
    # ── Handle empty input ──
    if len(data) == 0:
        return {
            "mode": "empty",
            "data": [],
            "original_points": 0,
            "n_buckets": 0,
            "reduction_factor": 0,
            "message": "No data in range"
        }

    delta_lambda = lambda_max - lambda_min

    # ── Validate wavelength range ──
    if delta_lambda <= 0:
        return {
            "mode": "error",
            "data": [],
            "original_points": len(data),
            "n_buckets": 0,
            "reduction_factor": 0,
            "message": "Invalid wavelength range"
        }

    # ── Calculate bucket geometry ──
    b_final = calculate_bucket_size(delta_lambda, zoom_level, config)
    z_max = calculate_zoom_max(delta_lambda, config, n_points=len(data))
    n_buckets = math.ceil(delta_lambda / b_final)

    # ── Saturation check: return raw when downsampling is pointless ──
    if zoom_level > z_max or n_buckets >= len(data):
        logger.info(
            f"Raw mode: zoom={zoom_level}, z_max={z_max}, "
            f"n_buckets={n_buckets}, n_points={len(data)}"
        )
        return {
            "mode": "raw",
            "z_max": z_max,
            "data": data.tolist(),
            "original_points": len(data),
            "n_buckets": n_buckets,
            "reduction_factor": 0,
            "message": f"Beyond zoom saturation (z_max={z_max}). Returning raw data."
        }

    logger.info(
        f"M4 Downsampling: zoom={zoom_level}, buckets={n_buckets}, "
        f"b_final={b_final:.4f}nm, points={len(data)}"
    )

    # ── M4 bucket processing ──
    m4_data = []

    for j in range(n_buckets):
        # Define strict non-overlapping bucket boundaries
        lambda_start = lambda_min + (j * b_final)
        lambda_end = lambda_start + b_final

        # Boolean mask: select data points within this bucket
        mask = (data[:, 0] >= lambda_start) & (data[:, 0] < lambda_end)
        bucket_data = data[mask]

        if len(bucket_data) == 0:
            continue

        intensities = bucket_data[:, 1]

        # ── Extract M4 extreme indices ──
        idx_first = 0                          # First point in bucket
        idx_last = len(bucket_data) - 1        # Last point in bucket
        idx_min = int(np.argmin(intensities))   # Minimum intensity point
        idx_max = int(np.argmax(intensities))   # Maximum intensity point

        # Deduplicate (some indices may coincide) and sort by wavelength
        unique_indices = sorted(list(set([idx_first, idx_min, idx_max, idx_last])))

        # Emit 1–4 points per bucket
        for idx in unique_indices:
            m4_data.append({
                "wavelength_nm": float(bucket_data[idx, 0]),
                "intensity": float(bucket_data[idx, 1]),
                "raw_plasma": float(bucket_data[idx, 2])
            })

    # ── Calculate reduction factor ──
    reduction_factor = len(data) / len(m4_data) if m4_data else 0

    return {
        "mode": "downsampled",
        "z_max": z_max,
        "zoom_level": zoom_level,
        "b_final": b_final,
        "n_buckets": n_buckets,
        "original_points": len(data),
        "reduction_factor": reduction_factor,
        "data": m4_data
    }


def generate_sample_spectrum(
    lambda_min: float = 200.0,
    lambda_max: float = 800.0,
    n_points: int = 2094,
    num_peaks: int = 10
) -> np.ndarray:
    """
    Generate synthetic LIBS spectral data for testing and demonstration.

    Creates a realistic-looking spectrum with a noisy baseline and
    randomly positioned Gaussian emission peaks. The default n_points=2094
    matches the Chandrayaan-3 LIBS channel count.

    Parameters
    ----------
    lambda_min : float
        Minimum wavelength in nm.
    lambda_max : float
        Maximum wavelength in nm.
    n_points : int
        Number of wavelength channels to generate.
    num_peaks : int
        Number of synthetic emission line peaks to add.

    Returns
    -------
    np.ndarray
        Array of shape (n_points, 3) with columns [wavelength_nm, intensity, raw_plasma].
    """
    wavelengths = np.linspace(lambda_min, lambda_max, n_points)

    # Baseline: constant offset with Gaussian noise
    baseline = 50 + np.random.normal(0, 5, n_points)
    intensities = baseline.copy()

    # Add Gaussian emission peaks at random positions
    for _ in range(num_peaks):
        peak_lambda = np.random.uniform(lambda_min, lambda_max)
        peak_intensity = np.random.uniform(200, 600)
        peak_width = np.random.uniform(0.5, 2.0)

        peak = peak_intensity * np.exp(
            -((wavelengths - peak_lambda) ** 2) / (2 * peak_width ** 2)
        )
        intensities += peak

    raw_plasma = intensities + baseline * 0.5  # synthetic raw plasma
    return np.column_stack([wavelengths, intensities, raw_plasma])

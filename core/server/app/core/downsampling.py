import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DownsampleConfig:
    """Configuration for min-max downsampling.

    BASE_BUCKETS is calibrated for Chandrayaan-3 LIBS data density
    (~2094 wavelength channels per measurement). With BASE_BUCKETS=200
    and the standard 600nm range, three zoom levels provide meaningful
    reduction before the algorithm saturates to raw mode:

        z=0 → 200 buckets → ~10x reduction
        z=1 → 400 buckets → ~5x reduction
        z=2 → 800 buckets → ~2.6x reduction
        z=3 → 1600 buckets → raw (data-density saturation)
    """
    BASE_BUCKETS: int = 200
    B_MIN: float = 0.01  # nm - minimum bucket size (instrument resolution)
    OVERLAP_PCT: float = 0.05  # 5% overlap between buckets


def calculate_bucket_size(
    delta_lambda: float,
    zoom_level: int,
    config: DownsampleConfig = DownsampleConfig()
) -> float:
    """
    Calculate bucket size based on zoom level.

    From LunarAtlas paper - Equation 4:
    b_size(z) = delta_lambda / (BASE_BUCKETS * 2^z)

    Equation 5: enforce minimum bucket size
    b_final(z) = max(b_size(z), b_min)
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
    Calculate maximum useful zoom level using dual saturation criteria.

    Two independent limits constrain the maximum zoom:

    1. Instrument resolution limit (Eq. 6 from paper):
       z_instrument = floor(log2(delta_lambda / (BASE_BUCKETS * b_min)))

    2. Data-density limit (new):
       z_data = floor(log2(n_points / BASE_BUCKETS))
       Downsampling is pointless when n_buckets >= n_points.

    z_max = min(z_instrument, z_data)

    Args:
        delta_lambda: Wavelength range in nm
        config: Downsampling configuration
        n_points: Number of actual data points (0 = ignore density limit)

    Returns:
        Maximum zoom level (integer, >= 0)
    """
    if delta_lambda <= 0:
        return 0

    # Limit 1: instrument resolution
    z_instrument = math.log2(
        delta_lambda / (config.BASE_BUCKETS * config.B_MIN)
    )

    # Limit 2: data density (if known)
    if n_points > 0 and n_points > config.BASE_BUCKETS:
        z_data = math.log2(n_points / config.BASE_BUCKETS)
    else:
        z_data = z_instrument  # no density constraint

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
    MinMaxMinMax (M4) downsampling algorithm.

    Preserves exactly up to 4 extreme points per bucket: First, Min, Max, Last.
    This guarantees visual envelope preservation while massively reducing data size.

    Args:
        data: NumPy array of shape (N, 2) - [wavelength_nm, intensity]
        zoom_level: Current zoom level (0 = most zoomed out)
        lambda_min: Minimum wavelength in view (nm)
        lambda_max: Maximum wavelength in view (nm)
        config: Downsampling configuration

    Returns:
        Dictionary with mode, data, and metadata.
    """
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

    if delta_lambda <= 0:
        return {
            "mode": "error",
            "data": [],
            "original_points": len(data),
            "n_buckets": 0,
            "reduction_factor": 0,
            "message": "Invalid wavelength range"
        }

    # Calculate bucket size
    b_final = calculate_bucket_size(delta_lambda, zoom_level, config)
    z_max = calculate_zoom_max(delta_lambda, config, n_points=len(data))
    n_buckets = math.ceil(delta_lambda / b_final)

    # Check saturation: return raw if zoom beyond z_max OR
    # bucket count >= data points (no reduction benefit)
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

    m4_data = []

    # Process each bucket
    for j in range(n_buckets):
        lambda_start = lambda_min + (j * b_final)
        lambda_end = lambda_start + b_final

        # Strict bucket filtering, no overlap in M4
        mask = (data[:, 0] >= lambda_start) & (data[:, 0] < lambda_end)
        bucket_data = data[mask]

        if len(bucket_data) == 0:
            continue

        intensities = bucket_data[:, 1]

        # M4 Extraction: First, Min, Max, Last
        idx_first = 0
        idx_last = len(bucket_data) - 1
        idx_min = int(np.argmin(intensities))
        idx_max = int(np.argmax(intensities))

        # Deduplicate and sort by X-axis logically (First is always first, Last is last)
        unique_indices = sorted(list(set([idx_first, idx_min, idx_max, idx_last])))

        for idx in unique_indices:
            m4_data.append({
                "wavelength_nm": float(bucket_data[idx, 0]),
                "intensity": float(bucket_data[idx, 1])
            })

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
    Generate synthetic spectral data for testing.

    Default n_points=2094 matches Chandrayaan-3 LIBS channel count.

    Args:
        lambda_min: Minimum wavelength (nm)
        lambda_max: Maximum wavelength (nm)
        n_points: Number of data points
        num_peaks: Number of emission line peaks

    Returns:
        NumPy array of shape (n_points, 2) - [wavelength, intensity]
    """
    wavelengths = np.linspace(lambda_min, lambda_max, n_points)

    # Baseline with noise
    baseline = 50 + np.random.normal(0, 5, n_points)
    intensities = baseline.copy()

    # Add Gaussian peaks (emission lines)
    for _ in range(num_peaks):
        peak_lambda = np.random.uniform(lambda_min, lambda_max)
        peak_intensity = np.random.uniform(200, 600)
        peak_width = np.random.uniform(0.5, 2.0)

        peak = peak_intensity * np.exp(
            -((wavelengths - peak_lambda) ** 2) / (2 * peak_width ** 2)
        )
        intensities += peak

    return np.column_stack([wavelengths, intensities])

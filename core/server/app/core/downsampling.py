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


def adaptive_minmax_downsample(
    data: np.ndarray,
    zoom_level: int,
    lambda_min: float,
    lambda_max: float,
    config: DownsampleConfig = DownsampleConfig()
) -> Dict:
    """
    Adaptive min-max downsampling algorithm.

    Implements Equations 4-9 from the LunarAtlas paper with
    data-density-aware zoom saturation.

    The algorithm preserves emission line peaks at all zoom levels
    by retaining both the minimum and maximum intensity within
    each wavelength bucket.

    Args:
        data: NumPy array of shape (N, 2) - [wavelength_nm, intensity]
        zoom_level: Current zoom level (0 = most zoomed out)
        lambda_min: Minimum wavelength in view (nm)
        lambda_max: Maximum wavelength in view (nm)
        config: Downsampling configuration

    Returns:
        Dictionary with mode, data, and metadata.
    """
    # Validate input
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

    # Calculate bucket size (Eq. 4-5)
    b_final = calculate_bucket_size(delta_lambda, zoom_level, config)

    # Calculate zoom saturation with data-density awareness
    z_max = calculate_zoom_max(delta_lambda, config, n_points=len(data))

    # Number of buckets at this zoom level
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
        f"Downsampling: zoom={zoom_level}, buckets={n_buckets}, "
        f"b_final={b_final:.4f}nm, points={len(data)}"
    )

    # Pre-allocate result list
    buckets = []

    # Process each bucket (Eq. 7-9)
    for j in range(n_buckets):
        lambda_start = lambda_min + (j * b_final)
        lambda_end = lambda_start + b_final

        # Overlap for continuity (Eq. 7)
        if j > 0:
            lambda_start_ext = lambda_start - (config.OVERLAP_PCT * b_final)
        else:
            lambda_start_ext = lambda_start

        if j < n_buckets - 1:
            lambda_end_ext = lambda_end + (config.OVERLAP_PCT * b_final)
        else:
            lambda_end_ext = lambda_end

        # Filter data points in this bucket
        mask = (data[:, 0] >= lambda_start_ext) & (data[:, 0] < lambda_end_ext)
        bucket_data = data[mask]

        if len(bucket_data) == 0:
            continue

        # Eq. 8-9: min and max intensities
        intensities = bucket_data[:, 1]
        wavelengths = bucket_data[:, 0]

        min_idx = np.argmin(intensities)
        max_idx = np.argmax(intensities)

        buckets.append({
            "bucket_id": j,
            "lambda_min": float(wavelengths[min_idx]),
            "intensity_min": float(intensities[min_idx]),
            "lambda_max": float(wavelengths[max_idx]),
            "intensity_max": float(intensities[max_idx]),
            "n_points": int(len(bucket_data)),
            "lambda_center": float((lambda_start + lambda_end) / 2)
        })

    reduction_factor = len(data) / len(buckets) if buckets else 0

    return {
        "mode": "downsampled",
        "z_max": z_max,
        "zoom_level": zoom_level,
        "b_final": b_final,
        "n_buckets": len(buckets),
        "original_points": len(data),
        "reduction_factor": reduction_factor,
        "data": buckets
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

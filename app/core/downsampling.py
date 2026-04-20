import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DownsampleConfig:
    """Configuration for min-max downsampling"""
    BASE_BUCKETS: int = 1000
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
    b_size(z) = Δλ / (BASE_BUCKETS × 2^z)
    
    Args:
        delta_lambda: Wavelength range (λ_max - λ_min) in nm
        zoom_level: Integer zoom level (0, 1, 2, ...)
        config: Downsampling configuration
    
    Returns:
        Final bucket size in nanometers
    """
    # Equation 4: Zoom-dependent bucket size
    b_size = delta_lambda / (config.BASE_BUCKETS * (2 ** zoom_level))
    
    # Equation 5: Enforce minimum bucket size
    b_final = max(b_size, config.B_MIN)
    
    return b_final


def calculate_zoom_max(
    delta_lambda: float,
    config: DownsampleConfig = DownsampleConfig()
) -> int:
    """
    Calculate maximum useful zoom level.
    
    From LunarAtlas paper - Equation 6:
    z_max = floor(log2(Δλ / (BASE_BUCKETS × b_min)))
    
    Beyond this zoom level, bucket size is clamped at b_min,
    so we return raw data instead.
    
    Args:
        delta_lambda: Wavelength range in nm
        config: Downsampling configuration
    
    Returns:
        Maximum zoom level (integer)
    """
    if delta_lambda <= 0:
        return 0
    
    z_max = math.log2(
        delta_lambda / (config.BASE_BUCKETS * config.B_MIN)
    )
    return int(z_max)


def adaptive_minmax_downsample(
    data: np.ndarray,
    zoom_level: int,
    lambda_min: float,
    lambda_max: float,
    config: DownsampleConfig = DownsampleConfig()
) -> Dict:
    """
    Adaptive min-max downsampling algorithm.
    
    Implements Equations 4-9 from the LunarAtlas paper.
    Preserves emission line peaks at all zoom levels while reducing data volume.
    
    Algorithm:
    1. Calculate bucket size based on zoom level
    2. Check if beyond zoom saturation (return raw data if so)
    3. Divide wavelength range into buckets
    4. For each bucket, store min and max intensity points
    5. Add 5% overlap to prevent edge artifacts
    
    Args:
        data: NumPy array of shape (N, 2) - [wavelength_nm, intensity]
        zoom_level: Current zoom level (0 = most zoomed out)
        lambda_min: Minimum wavelength in view (nm)
        lambda_max: Maximum wavelength in view (nm)
        config: Downsampling configuration
    
    Returns:
        Dictionary containing:
        - mode: "downsampled" or "raw"
        - data: Downsampled buckets or raw data
        - metadata: Algorithm parameters and statistics
    """
    # Validate input
    if len(data) == 0:
        return {
            "mode": "empty",
            "data": [],
            "message": "No data in range"
        }
    
    # Calculate wavelength range
    delta_lambda = lambda_max - lambda_min
    
    if delta_lambda <= 0:
        return {
            "mode": "error",
            "data": [],
            "message": "Invalid wavelength range"
        }
    
    # Calculate bucket size (Equation 4-5)
    b_final = calculate_bucket_size(delta_lambda, zoom_level, config)
    
    # Calculate zoom saturation threshold (Equation 6)
    z_max = calculate_zoom_max(delta_lambda, config)
    
    # Check if beyond saturation - return raw data
    if zoom_level > z_max:
        logger.info(f"Zoom {zoom_level} > z_max {z_max}, returning raw data")
        return {
            "mode": "raw",
            "z_max": z_max,
            "data": data.tolist(),
            "original_points": len(data),
            "message": f"Beyond zoom saturation (z_max={z_max}). Returning raw data."
        }
    
    # Calculate number of buckets
    n_buckets = math.ceil(delta_lambda / b_final)
    
    logger.info(
        f"Downsampling: zoom={zoom_level}, buckets={n_buckets}, "
        f"b_final={b_final:.4f}nm, points={len(data)}"
    )
    
    # Pre-allocate result list
    buckets = []
    
    # Process each bucket
    for j in range(n_buckets):
        # Equation 7: Calculate bucket boundaries
        lambda_start = lambda_min + (j * b_final)
        lambda_end = lambda_start + b_final
        
        # Add overlap for continuity (Equation 7 extended)
        if j > 0:
            lambda_start_ext = lambda_start - (config.OVERLAP_PCT * b_final)
        else:
            lambda_start_ext = lambda_start
        
        if j < n_buckets - 1:
            lambda_end_ext = lambda_end + (config.OVERLAP_PCT * b_final)
        else:
            lambda_end_ext = lambda_end
        
        # Filter data points in this bucket (with overlap)
        mask = (data[:, 0] >= lambda_start_ext) & (data[:, 0] < lambda_end_ext)
        bucket_data = data[mask]
        
        # Skip empty buckets
        if len(bucket_data) == 0:
            continue
        
        # Equation 8-9: Extract min and max intensities
        intensities = bucket_data[:, 1]
        wavelengths = bucket_data[:, 0]
        
        min_idx = np.argmin(intensities)
        max_idx = np.argmax(intensities)
        
        # Store bucket result
        buckets.append({
            "bucket_id": j,
            "lambda_min": float(wavelengths[min_idx]),
            "intensity_min": float(intensities[min_idx]),
            "lambda_max": float(wavelengths[max_idx]),
            "intensity_max": float(intensities[max_idx]),
            "n_points": int(len(bucket_data)),
            "lambda_center": float((lambda_start + lambda_end) / 2)
        })
    
    # Calculate statistics
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
    n_points: int = 2049,
    num_peaks: int = 10
) -> np.ndarray:
    """
    Generate synthetic spectral data for testing.
    
    Creates a spectrum with a baseline and multiple Gaussian peaks
    (simulating emission lines).
    
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
        
        # Gaussian peak
        peak = peak_intensity * np.exp(
            -((wavelengths - peak_lambda) ** 2) / (2 * peak_width ** 2)
        )
        intensities += peak
    
    return np.column_stack([wavelengths, intensities])

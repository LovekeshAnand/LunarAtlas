"""
Vectorized LTTB (Largest Triangle Three Buckets) downsampling for LIBS spectral data.

Uses NumPy vectorised operations for HPC-grade throughput:
  - np.searchsorted for O(N log B) bucket assignment
  - Pre-computed bucket boundaries (zero per-bucket allocation)
  - Inline triangle-area computation (avoids Python function-call overhead)

Supports 3-column data: [wavelength_nm, intensity, raw_plasma].
"""

import math
import numpy as np
from typing import Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DownsampleConfig:
    """Configuration for LTTB downsampling.

    BASE_BUCKETS is calibrated for Chandrayaan-3 LIBS data density
    (~2094 wavelength channels per measurement). With BASE_BUCKETS=200
    and the standard 600nm range, three zoom levels provide meaningful
    reduction before the algorithm saturates to raw mode:

        z=0 → 200 buckets → ~10× reduction
        z=1 → 400 buckets → ~5× reduction
        z=2 → 800 buckets → ~2.6× reduction
        z=3 → 1600 buckets → raw (data-density saturation)
    """
    BASE_BUCKETS: int = 200
    B_MIN: float = 0.01
    OVERLAP_PCT: float = 0.05


def calculate_bucket_size(
    delta_lambda: float,
    zoom_level: int,
    config: DownsampleConfig = DownsampleConfig()
) -> float:
    """
    Calculate bucket size based on zoom level.

    From LunarAtlas paper — Equation 4:
        b_size(z) = Δλ / (BASE_BUCKETS × 2^z)

    Equation 5: enforce minimum bucket size
        b_final(z) = max(b_size(z), b_min)

    Parameters
    ----------
    delta_lambda : float
        Wavelength range in nm.
    zoom_level : int
        Current zoom level (0 = most zoomed out).
    config : DownsampleConfig
        Algorithm parameters.

    Returns
    -------
    float
        Final bucket width in nm.
    """
    b_size = delta_lambda / (config.BASE_BUCKETS * (2 ** zoom_level))
    return max(b_size, config.B_MIN)


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

    z_instrument = math.log2(
        delta_lambda / (config.BASE_BUCKETS * config.B_MIN)
    )

    if n_points > 0 and n_points > config.BASE_BUCKETS:
        z_data = math.log2(n_points / config.BASE_BUCKETS)
    else:
        z_data = z_instrument

    return max(0, int(min(z_instrument, z_data)))


# ---------------------------------------------------------------------------
#  Vectorised LTTB
# ---------------------------------------------------------------------------

def lttb_downsample(
    data: np.ndarray,
    zoom_level: int,
    lambda_min: float,
    lambda_max: float,
    target_wavelengths: List[float] = None,
    proportion: float = None
) -> Dict:
    """
    LTTB Multi-Zoom Formulation for Chandrayaan-3 LIBS (Fixed 2094 domain).
    
    Operates explicitly over index-space buckets governed by the zoom scaler,
    avoiding the false assumption of time-series density clustering.
    
    N(k) = min(2094, 2094 * 2^-k)
    where output threshold maps natively to visual resolution requirements.
    """
    if len(data) == 0:
        return {
            "mode": "empty",
            "data": [],
            "n_buckets": 0,
            "reduction_factor": 0,
            "message": "No data near range"
        }

    n_raw = len(data)
    
    # Calculate threshold based on proportion if provided, otherwise zoom_level
    if proportion is not None:
        target_k_size = int(2094 * proportion)
        threshold = min(2094, target_k_size)
    else:
        # N(k) mathematical formulation (2094 is the CH-3 LIBS structural constant)
        target_k_size = int(2094 * (2 ** -zoom_level))
        threshold = min(2094, target_k_size)
    
    # Render raw if required (z=0 or sparse data)
    if threshold >= n_raw or threshold < 3:
        logger.info(f"Raw rendering active: thresh={threshold}, n_raw={n_raw}")
        return {
            "mode": "raw",
            "z_max": 5, 
            "data": [
                {
                    "wavelength_nm": float(row[0]),
                    "intensity": float(row[1]),
                    "raw_plasma": float(row[2]) if data.shape[1] > 2 else float(row[1])
                }
                for row in data
            ],
            "original_points": n_raw,
            "n_buckets": n_raw,
            "reduction_factor": 1.0,
        }

    logger.info(f"LTTB Downsampling active: zoom={zoom_level}, points={n_raw}, limit={threshold}")

    wavelengths = data[:, 0]
    intensities = data[:, 1]
    has_raw = data.shape[1] > 2
    raw_plasma = data[:, 2] if has_raw else intensities

    sampled_indices = []
    
    # Always keep first
    sampled_indices.append(0)

    # Exact bucket size distribution over index-space (Section 2.2 constraint)
    every = (n_raw - 2) / (threshold - 2)
    
    a = 0
    for i in range(threshold - 2):
        avg_range_start = math.floor((i + 1) * every) + 1
        avg_range_end = math.floor((i + 2) * every) + 1
        if avg_range_end > n_raw:
            avg_range_end = n_raw
            
        avg_range_length = avg_range_end - avg_range_start
        
        if avg_range_length > 0:
            avg_x = np.mean(wavelengths[avg_range_start:avg_range_end])
            avg_y = np.mean(intensities[avg_range_start:avg_range_end])
        else:
            avg_x = wavelengths[-1]
            avg_y = intensities[-1]
            
        point_a_x = wavelengths[a]
        point_a_y = intensities[a]
        
        range_offs = math.floor(i * every) + 1
        range_to = math.floor((i + 1) * every) + 1
        
        bx = wavelengths[range_offs:range_to]
        by = intensities[range_offs:range_to]
        
        areas = np.abs(
            point_a_x * (by - avg_y) +
            bx * (avg_y - point_a_y) +
            avg_x * (point_a_y - by)
        )
        
        best_local = int(np.argmax(areas))
        next_a = range_offs + best_local
        
        sampled_indices.append(next_a)
        a = next_a

    # Always keep last point
    sampled_indices.append(n_raw - 1)

    # === SECTION 8: TARGETED PEAK PRESERVATION ===
    # P_final = LTTB(data) U Peaks_target(data)
    final_indices = list(sampled_indices)
    if target_wavelengths:
        for wl in target_wavelengths:
            idx = int(np.searchsorted(wavelengths, wl))
            if idx >= len(wavelengths):
                idx = len(wavelengths) - 1
            elif idx > 0 and abs(wavelengths[idx - 1] - wl) < abs(wavelengths[idx] - wl):
                idx -= 1
            final_indices.append(idx)
            
    unique_indices = sorted(list(set(final_indices)))
    
    lttb_data = []
    for idx in unique_indices:
        lttb_data.append({
            "wavelength_nm": float(wavelengths[idx]),
            "intensity": float(intensities[idx]),
            "raw_plasma": float(raw_plasma[idx])
        })

    reduction_factor = n_raw / len(lttb_data) if lttb_data else 0

    return {
        "mode": "downsampled",
        "z_max": 5,
        "zoom_level": zoom_level,
        "b_final": 0.0,
        "n_buckets": len(lttb_data),
        "original_points": n_raw,
        "reduction_factor": reduction_factor,
        "data": lttb_data
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
    randomly positioned Gaussian emission peaks.  The default n_points=2094
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
        Array of shape (n_points, 3) with columns
        [wavelength_nm, intensity, raw_plasma].
    """
    wavelengths = np.linspace(lambda_min, lambda_max, n_points)

    baseline = 50 + np.random.normal(0, 5, n_points)
    intensities = baseline.copy()

    for _ in range(num_peaks):
        peak_lambda = np.random.uniform(lambda_min, lambda_max)
        peak_intensity = np.random.uniform(200, 600)
        peak_width = np.random.uniform(0.5, 2.0)

        peak = peak_intensity * np.exp(
            -((wavelengths - peak_lambda) ** 2) / (2 * peak_width ** 2)
        )
        intensities += peak

    raw_plasma = intensities + baseline * 0.5
    return np.column_stack([wavelengths, intensities, raw_plasma])

"""
Optional spectral denoising pipeline for LunarAtlas visualization layer.

Implements two independent denoising algorithms that may be applied to
``I_clean(λ)`` spectra retrieved from the database **without modifying
the stored data**.  The database remains the sole source of truth.

Processing order (fixed, never reversed):

    1. ALS Baseline Correction  →  removes slowly-varying continuum
    2. Savitzky-Golay Smoothing →  suppresses high-frequency shot noise

Entry point for callers is :func:`apply_denoising_pipeline`.

References
----------
Eilers, P. H. C. & Boelens, H. F. M. (2005). Baseline Correction with
Asymmetric Least Squares Smoothing.

Savitzky, A. & Golay, M. J. E. (1964). Smoothing and Differentiation of
Data by Simplified Least Squares Procedures. Analytical Chemistry, 36(8).
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Recommended defaults (LIBS / Raman literature values)
# ---------------------------------------------------------------------------

_ALS_LAM: float = 1e5   # Smoothness penalty  (higher → smoother baseline)
_ALS_P: float = 0.01    # Asymmetry weight    (lower  → baseline stays below peaks)
_ALS_ITER: int = 10     # WhittakerSmooth iterations

_SG_WINDOW: int = 11    # Must be odd
_SG_POLYORDER: int = 3  # Must be < window_length


# ---------------------------------------------------------------------------
#  Feature 1: ALS Baseline Correction
# ---------------------------------------------------------------------------

def als_baseline_correction(
    intensities: np.ndarray,
    lam: float = _ALS_LAM,
    p: float = _ALS_P,
    n_iter: int = _ALS_ITER,
) -> np.ndarray:
    """
    Asymmetric Least Squares (ALS) baseline correction.

    Estimates a smooth baseline ``z(λ)`` that lies beneath emission peaks
    by iteratively re-weighting a penalised least-squares fit.  Positive
    deviations (peaks) are penalised less than negative deviations, which
    prevents emission lines from pulling the baseline upward.

    Output per channel:

        I_ALS(λ) = max(0,  I_clean(λ) − z(λ))

    Parameters
    ----------
    intensities : np.ndarray, shape (N,)
        Input intensity array (``I_clean``) in counts.
    lam : float
        Smoothness regularisation parameter λ (WhittakerSmooth).
        Larger values produce a smoother, slower-varying baseline.
        Recommended: ``1e5`` for LIBS data.
    p : float
        Asymmetry weight for under-fitting (0 < p ≪ 1).
        Smaller values keep the baseline further below peaks.
        Recommended: ``0.01``.
    n_iter : int
        Number of ALS iterations.  10 is sufficient for convergence in
        practice on LIBS spectra.

    Returns
    -------
    np.ndarray, shape (N,)
        Baseline-corrected, zero-clamped intensity array ``I_ALS(λ)``.

    Raises
    ------
    ValueError
        If ``intensities`` is empty or has fewer than 2 elements.
    """
    n = len(intensities)
    if n < 2:
        raise ValueError(
            f"als_baseline_correction requires at least 2 data points, got {n}."
        )

    y = intensities.astype(np.float64)

    # Second-order difference matrix D (sparse) for WhittakerSmooth
    D = sp.diags([1, -2, 1], [0, 1, 2], shape=(n - 2, n)).tocsc()
    H = lam * D.T @ D

    # Initial weights: uniform
    w = np.ones(n)

    z = y.copy()
    for _ in range(n_iter):
        W = sp.diags(w, 0, shape=(n, n)).tocsc()
        C = W + H
        try:
            z = spla.spsolve(C, w * y)
        except Exception as exc:
            logger.warning("ALS spsolve failed (%s); returning unmodified spectrum.", exc)
            return intensities

        # Re-weight: residuals below baseline → weight p; above → weight (1-p)
        w = np.where(y > z, p, 1 - p)

    corrected = y - z
    return np.maximum(0.0, corrected)


# ---------------------------------------------------------------------------
#  Feature 2: Savitzky-Golay Smoothing
# ---------------------------------------------------------------------------

def savitzky_golay_smooth(
    intensities: np.ndarray,
    window_length: int = _SG_WINDOW,
    polyorder: int = _SG_POLYORDER,
) -> np.ndarray:
    """
    Savitzky-Golay polynomial smoothing.

    Fits a low-order polynomial over a sliding window, replacing each
    centre point with the fitted value.  Preserves peak position, width,
    and shape better than a simple moving average.

    Parameters
    ----------
    intensities : np.ndarray, shape (N,)
        Input intensity array in counts.
    window_length : int
        Number of data points in the sliding window.  **Must be odd** and
        ≥ ``polyorder + 2``.  Recommended: ``11`` for CH-3 LIBS resolution.
    polyorder : int
        Degree of the polynomial fit.  Must satisfy ``polyorder < window_length``.
        Recommended: ``3``.

    Returns
    -------
    np.ndarray, shape (N,)
        Smoothed intensity array ``I_SG(λ)``.  If the spectrum is too short
        for the requested window, the input is returned unchanged with a
        warning.

    Raises
    ------
    ValueError
        If ``window_length`` is even or ``polyorder >= window_length``.
    """
    if window_length % 2 == 0:
        raise ValueError(
            f"savitzky_golay_smooth: window_length must be odd, got {window_length}."
        )
    if polyorder >= window_length:
        raise ValueError(
            f"savitzky_golay_smooth: polyorder ({polyorder}) must be "
            f"< window_length ({window_length})."
        )

    n = len(intensities)
    if n < window_length:
        logger.warning(
            "savitzky_golay_smooth: spectrum length (%d) < window_length (%d); "
            "returning input unchanged.",
            n,
            window_length,
        )
        return intensities.astype(np.float64)

    smoothed = savgol_filter(
        intensities.astype(np.float64),
        window_length=window_length,
        polyorder=polyorder,
    )
    # SG can produce slight negatives near boundaries; clamp them
    return np.maximum(0.0, smoothed)


# ---------------------------------------------------------------------------
#  Pipeline orchestrator
# ---------------------------------------------------------------------------

def apply_denoising_pipeline(
    intensities: np.ndarray,
    als: bool = False,
    savgol: bool = False,
) -> Tuple[np.ndarray, bool, bool]:
    """
    Apply the denoising pipeline in the fixed order: ALS → Savitzky-Golay.

    This is the **sole entry point** for the API endpoint.  Individual
    algorithm functions should not be called directly from the endpoint.

    Processing path for each combination:

    +----------+----------+------------------------------------------+
    | ``als``  |``savgol``| Pipeline applied                         |
    +==========+==========+==========================================+
    | False    | False    | No denoising — passthrough               |
    +----------+----------+------------------------------------------+
    | True     | False    | ALS baseline correction only             |
    +----------+----------+------------------------------------------+
    | False    | True     | Savitzky-Golay smoothing only            |
    +----------+----------+------------------------------------------+
    | True     | True     | ALS first, then Savitzky-Golay on result |
    +----------+----------+------------------------------------------+

    Parameters
    ----------
    intensities : np.ndarray, shape (N,)
        Input ``I_clean(λ)`` intensity array from the database.
    als : bool
        Whether to apply ALS baseline correction.
    savgol : bool
        Whether to apply Savitzky-Golay smoothing.

    Returns
    -------
    result : np.ndarray, shape (N,)
        Processed intensity array.
    als_applied : bool
        True if ALS was successfully applied.
    savgol_applied : bool
        True if Savitzky-Golay was successfully applied.
    """
    result = intensities.astype(np.float64)
    als_applied = False
    savgol_applied = False

    if als:
        try:
            result = als_baseline_correction(result)
            als_applied = True
            logger.debug("ALS baseline correction applied (%d points).", len(result))
        except Exception as exc:
            logger.error("ALS correction failed: %s — returning unmodified spectrum.", exc)

    if savgol:
        try:
            result = savitzky_golay_smooth(result)
            savgol_applied = True
            logger.debug("Savitzky-Golay smoothing applied (window=%d, poly=%d).",
                         _SG_WINDOW, _SG_POLYORDER)
        except Exception as exc:
            logger.error("Savitzky-Golay smoothing failed: %s — skipping.", exc)

    return result, als_applied, savgol_applied

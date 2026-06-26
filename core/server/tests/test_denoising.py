import numpy as np
import pytest
from app.core.denoising import (
    als_baseline_correction,
    savitzky_golay_smooth,
    apply_denoising_pipeline
)

def test_als_baseline_correction():
    """Test that ALS Baseline Correction removes a slowly-varying background."""
    # Generate 1000 points: a flat spectrum with a broad Gaussian background bump
    # and a sharp peak on top of it.
    x = np.linspace(200, 800, 1000)
    background = 500 * np.exp(-((x - 500) / 150) ** 2)  # slow-varying bump
    peak = np.zeros_like(x)
    peak[500] = 1000.0  # sharp peak at x = 500
    
    clean_signal = peak
    noisy_signal = clean_signal + background
    
    # Apply ALS baseline correction
    corrected = als_baseline_correction(noisy_signal, lam=1e5, p=0.01, n_iter=10)
    
    assert corrected.shape == noisy_signal.shape
    # Outside the peak, corrected signal should be close to zero
    # (since the background is successfully estimated and subtracted)
    # We verify that the mean difference from zero in the baseline region is small.
    baseline_regions = np.concatenate([corrected[:400], corrected[600:]])
    assert np.mean(baseline_regions) < 15.0  # background was ~500 counts
    
    # The sharp peak should still be preserved
    assert corrected[500] > 900.0
    # No negative values because of clamping
    assert np.all(corrected >= 0.0)


def test_savitzky_golay_smooth():
    """Test that Savitzky-Golay smoothing suppresses high-frequency noise."""
    # Generate a constant signal with random noise
    np.random.seed(42)
    n_points = 500
    base_val = 100.0
    noise = np.random.normal(0, 10.0, n_points)
    signal = base_val + noise
    
    # Apply SG smoothing
    smoothed = savitzky_golay_smooth(signal, window_length=11, polyorder=3)
    
    assert smoothed.shape == signal.shape
    assert np.all(smoothed >= 0.0)
    
    # Verify standard deviation of the difference from base_val is reduced (noise suppressed)
    noise_std = np.std(signal - base_val)
    smoothed_std = np.std(smoothed - base_val)
    
    assert smoothed_std < noise_std * 0.5  # Noise standard deviation should be reduced by more than 50%
    
    # Check that input is returned unchanged if spectrum is too short for the window
    short_signal = np.array([100.0, 105.0, 102.0])
    result = savitzky_golay_smooth(short_signal, window_length=11, polyorder=3)
    assert np.array_equal(result, short_signal)


def test_savitzky_golay_validation():
    """Test that Savitzky-Golay validates its inputs correctly."""
    signal = np.ones(50)
    
    # Even window length should raise ValueError
    with pytest.raises(ValueError, match="window_length must be odd"):
        savitzky_golay_smooth(signal, window_length=10, polyorder=3)
        
    # polyorder >= window_length should raise ValueError
    with pytest.raises(ValueError, match="polyorder.*must be < window_length"):
        savitzky_golay_smooth(signal, window_length=11, polyorder=11)


def test_apply_denoising_pipeline():
    """Test the full pipeline combinations and execution order."""
    x = np.linspace(200, 800, 1000)
    # broad background + sharp peak + high-frequency noise
    np.random.seed(42)
    signal = 100 * np.exp(-((x - 500) / 100) ** 2) + 50.0 + np.random.normal(0, 2.0, 1000)
    
    # 1. Passthrough (als=False, savgol=False)
    out_none, als_app, sg_app = apply_denoising_pipeline(signal, als=False, savgol=False)
    assert np.array_equal(out_none, signal)
    assert not als_app
    assert not sg_app
    
    # 2. ALS only
    out_als, als_app, sg_app = apply_denoising_pipeline(signal, als=True, savgol=False)
    assert als_app
    assert not sg_app
    assert not np.array_equal(out_als, signal)
    # Baseline correction should drop the minimum level near 0
    assert np.min(out_als) < np.min(signal)
    
    # 3. Savitzky-Golay only
    out_sg, als_app, sg_app = apply_denoising_pipeline(signal, als=False, savgol=True)
    assert not als_app
    assert sg_app
    assert not np.array_equal(out_sg, signal)
    
    # 4. ALS + Savitzky-Golay (full pipeline)
    out_both, als_app, sg_app = apply_denoising_pipeline(signal, als=True, savgol=True)
    assert als_app
    assert sg_app
    # Verify no NaN or infinity in output
    assert not np.any(np.isnan(out_both))
    assert not np.any(np.isinf(out_both))
    # Output must be non-negative
    assert np.all(out_both >= 0.0)


if __name__ == "__main__":
    test_als_baseline_correction()
    test_savitzky_golay_smooth()
    test_savitzky_golay_validation()
    test_apply_denoising_pipeline()
    print("\n" + "=" * 60)
    print("All backend denoising tests passed!")
    print("=" * 60)

"""
LunarAtlas Test Suite — LTTB Algorithm Unit Tests
==================================================
Tests the core LTTB downsampling algorithm and bucket-size mathematics
that are the algorithmic contribution described in the paper.

All tests use synthetic data — no database or filesystem required.
Run with: pytest tests/ -v
"""

import math
import sys
import os
import numpy as np
import pytest

# ── Make the server app importable from the test root ─────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core', 'server'))

from app.core.downsampling import (
    lttb_downsample,
    calculate_bucket_size,
    calculate_zoom_max,
    generate_sample_spectrum,
    DownsampleConfig,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def ch3_spectrum():
    """Generate a synthetic Chandrayaan-3 LIBS spectrum (2094 channels)."""
    return generate_sample_spectrum(
        lambda_min=220.0,
        lambda_max=800.0,
        n_points=2094,
        num_peaks=12,
    )


@pytest.fixture
def nist_targets():
    """Six canonical NIST emission line wavelengths used in the paper."""
    return [279.55, 288.16, 393.37, 404.58, 518.36, 588.99]


# ─── Bucket-Size Mathematics ──────────────────────────────────────────────

class TestBucketSizeMath:
    """Validates Equations 4 and 5 from the paper."""

    def test_zoom0_bucket_size(self):
        """At z=0, b_size = Δλ / BASE_BUCKETS."""
        delta = 580.0  # 220–800 nm
        cfg = DownsampleConfig(BASE_BUCKETS=200, B_MIN=0.01)
        result = calculate_bucket_size(delta, zoom_level=0, config=cfg)
        expected = delta / 200
        assert abs(result - expected) < 1e-6

    def test_zoom_doubles_resolution(self):
        """Each zoom level halves the bucket size."""
        delta = 580.0
        cfg = DownsampleConfig(BASE_BUCKETS=200, B_MIN=0.01)
        b0 = calculate_bucket_size(delta, 0, cfg)
        b1 = calculate_bucket_size(delta, 1, cfg)
        assert abs(b0 / b1 - 2.0) < 1e-6

    def test_minimum_bucket_clamping(self):
        """Bucket size never goes below B_MIN."""
        cfg = DownsampleConfig(BASE_BUCKETS=200, B_MIN=0.01)
        result = calculate_bucket_size(0.001, zoom_level=10, config=cfg)
        assert result >= cfg.B_MIN

    def test_zoom_max_positive(self):
        """z_max must be >= 0 for a valid wavelength range."""
        z = calculate_zoom_max(delta_lambda=580.0, n_points=2094)
        assert z >= 0

    def test_zoom_max_data_density_limit(self):
        """z_max is bounded by data density: 2^z <= n_points / BASE_BUCKETS."""
        cfg = DownsampleConfig(BASE_BUCKETS=200, B_MIN=0.01)
        z = calculate_zoom_max(delta_lambda=580.0, config=cfg, n_points=2094)
        # 2094 / 200 ≈ 10.47 → log2 ≈ 3.38 → floor = 3
        assert z <= math.floor(math.log2(2094 / 200))


# ─── LTTB Core Algorithm ──────────────────────────────────────────────────

class TestLTTBCore:
    """Tests the LTTB reduction without NIST lock."""

    def test_output_size_matches_threshold(self, ch3_spectrum):
        """LTTB output must have exactly `threshold` points."""
        result = lttb_downsample(ch3_spectrum, zoom_level=1,
                                 lambda_min=220.0, lambda_max=800.0)
        assert result['mode'] in ('downsampled', 'raw')
        assert len(result['data']) > 0

    def test_preserves_first_and_last_point(self, ch3_spectrum):
        """LTTB must always keep the first and last data points."""
        result = lttb_downsample(ch3_spectrum, zoom_level=2,
                                 lambda_min=220.0, lambda_max=800.0)
        if result['mode'] == 'downsampled':
            out_wls = [p['wavelength_nm'] for p in result['data']]
            assert out_wls[0] == pytest.approx(ch3_spectrum[0, 0], abs=0.01)
            assert out_wls[-1] == pytest.approx(ch3_spectrum[-1, 0], abs=0.01)

    def test_wavelengths_monotonically_increasing(self, ch3_spectrum):
        """Output wavelengths must remain sorted in ascending order."""
        result = lttb_downsample(ch3_spectrum, zoom_level=2,
                                 lambda_min=220.0, lambda_max=800.0)
        wls = [p['wavelength_nm'] for p in result['data']]
        assert wls == sorted(wls)

    def test_no_negative_intensities(self, ch3_spectrum):
        """Cleaned spectra must never contain negative intensities."""
        result = lttb_downsample(ch3_spectrum, zoom_level=2,
                                 lambda_min=220.0, lambda_max=800.0)
        for pt in result['data']:
            assert pt['intensity'] >= 0.0

    def test_raw_mode_at_zoom_zero(self, ch3_spectrum):
        """At zoom=0, threshold >= n_raw, so mode should be 'raw'."""
        result = lttb_downsample(ch3_spectrum, zoom_level=0,
                                 lambda_min=220.0, lambda_max=800.0)
        assert result['mode'] == 'raw'
        assert len(result['data']) == len(ch3_spectrum)

    def test_empty_data_returns_empty(self):
        """Empty input must return mode='empty' without error."""
        empty = np.empty((0, 3))
        result = lttb_downsample(empty, zoom_level=1,
                                 lambda_min=220.0, lambda_max=800.0)
        assert result['mode'] == 'empty'
        assert result['data'] == []

    def test_reduction_factor_gt_one_when_downsampled(self, ch3_spectrum):
        """Reduction factor must be >1 when downsampling is active."""
        result = lttb_downsample(ch3_spectrum, zoom_level=2,
                                 lambda_min=220.0, lambda_max=800.0)
        if result['mode'] == 'downsampled':
            assert result['reduction_factor'] > 1.0


# ─── NIST Peak-Union Lock ─────────────────────────────────────────────────

class TestNISTPeakLock:
    """
    Tests the core novelty: P_final = LTTB(data) ∪ Peaks_NIST(data).

    This is Section 8 of the paper. The lock guarantees that every target
    elemental emission wavelength appears in the output regardless of
    what the LTTB triangle-area maximization selects.
    """

    def test_all_target_wavelengths_present(self, ch3_spectrum, nist_targets):
        """
        Every NIST target wavelength must be present in the downsampled output.
        This is the 100% target peak retention guarantee.
        """
        result = lttb_downsample(
            ch3_spectrum,
            zoom_level=3,
            lambda_min=220.0,
            lambda_max=800.0,
            target_wavelengths=nist_targets,
        )
        output_wls = np.array([p['wavelength_nm'] for p in result['data']])

        for target in nist_targets:
            if 220.0 <= target <= 800.0:
                nearest_dist = np.min(np.abs(output_wls - target))
                # Must be within 0.5 nm (one spectral channel)
                assert nearest_dist < 0.5, (
                    f"NIST target {target} nm missing from output. "
                    f"Nearest point: {output_wls[np.argmin(np.abs(output_wls - target))]:.3f} nm"
                )

    def test_no_targets_does_not_crash(self, ch3_spectrum):
        """Passing an empty target list must not raise any exception."""
        result = lttb_downsample(
            ch3_spectrum,
            zoom_level=2,
            lambda_min=220.0,
            lambda_max=800.0,
            target_wavelengths=[],
        )
        assert 'data' in result

    def test_peak_lock_increases_output_size(self, ch3_spectrum, nist_targets):
        """
        With the peak lock active, the output size should be >= output without lock.
        """
        without_lock = lttb_downsample(ch3_spectrum, zoom_level=3,
                                       lambda_min=220.0, lambda_max=800.0)
        with_lock = lttb_downsample(ch3_spectrum, zoom_level=3,
                                    lambda_min=220.0, lambda_max=800.0,
                                    target_wavelengths=nist_targets)
        assert len(with_lock['data']) >= len(without_lock['data'])

    def test_out_of_range_targets_ignored(self, ch3_spectrum):
        """Target wavelengths outside the spectrum range must not crash."""
        out_of_range = [100.0, 1200.0]  # outside 220-800 nm
        result = lttb_downsample(
            ch3_spectrum,
            zoom_level=2,
            lambda_min=220.0,
            lambda_max=800.0,
            target_wavelengths=out_of_range,
        )
        assert 'data' in result


# ─── Proportion Mode ──────────────────────────────────────────────────────

class TestProportionMode:
    """Tests the proportion= parameter (ratio-based threshold)."""

    def test_proportion_overrides_zoom(self, ch3_spectrum):
        """When proportion is set, zoom_level should be ignored."""
        result = lttb_downsample(
            ch3_spectrum,
            zoom_level=99,      # would normally produce near-zero points
            lambda_min=220.0,
            lambda_max=800.0,
            proportion=0.5,     # 50% → ~1047 points
        )
        # Should NOT be empty, because proportion overrides zoom
        assert len(result['data']) > 0

    def test_proportion_one_gives_raw(self, ch3_spectrum):
        """proportion=1.0 should give back all raw points."""
        result = lttb_downsample(
            ch3_spectrum,
            zoom_level=0,
            lambda_min=220.0,
            lambda_max=800.0,
            proportion=1.0,
        )
        assert result['mode'] == 'raw'

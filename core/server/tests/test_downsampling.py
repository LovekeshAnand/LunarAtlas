import numpy as np
from app.core.downsampling import (
    lttb_downsample,
    generate_sample_spectrum
)

def test_generate_spectrum():
    """Test synthetic spectrum generation with CH3 channel count (3-column)"""
    spectrum = generate_sample_spectrum(
        lambda_min=200.0,
        lambda_max=800.0,
        n_points=2094,
        num_peaks=10
    )
    
    assert spectrum.shape == (2094, 3), f"Spectrum shape incorrect: {spectrum.shape}"
    assert np.all(spectrum[:, 0] >= 200.0), "Wavelengths below minimum"
    assert np.all(spectrum[:, 0] <= 800.0), "Wavelengths above maximum"
    print("[OK] Spectrum generation test passed (3-column)")

def test_zoom_levels():
    """Test downsampling provides meaningful reduction across multiple zoom levels.
    
    With BASE_BUCKETS=200 and 2094 data points:
        z=0 -> 200 buckets -> ~10x reduction
        z=1 -> 400 buckets -> ~5x reduction
        z=2 -> 800 buckets -> ~2.6x reduction
        z=3 -> 1600 buckets -> raw (bail-out)
    """
    spectrum = generate_sample_spectrum(n_points=2094)
    
    downsampled_count = 0
    
    for zoom in range(0, 6):
        result = lttb_downsample(
            data=spectrum,
            zoom_level=zoom,
            lambda_min=200.0,
            lambda_max=800.0
        )
        
        print(f"\nZoom {zoom}:")
        print(f"  Mode: {result['mode']}")
        print(f"  Original points: {result.get('original_points', 0)}")
        print(f"  Output points: {len(result['data'])}")
        print(f"  Reduction: {result.get('reduction_factor', 0):.2f}x")
        
        assert result['mode'] in ['downsampled', 'raw'], f"Invalid mode at zoom {zoom}"
        
        if result['mode'] == 'downsampled':
            downsampled_count += 1
            assert result['reduction_factor'] >= 1.0, f"No reduction at zoom {zoom}"
            
            # Verify flat dict output format
            for pt in result['data'][:3]:
                assert 'wavelength_nm' in pt, "Missing wavelength_nm in output"
                assert 'intensity' in pt, "Missing intensity in output"
                assert 'raw_plasma' in pt, "Missing raw_plasma in output"
    
    # Must have downsampling when zoomed in
    assert downsampled_count > 0, "No zoom level triggered LTTB downsampling"
    
    # z=0 must NOT reduce points (Render Full Data constraint)
    result_z0 = lttb_downsample(
        data=spectrum, zoom_level=0,
        lambda_min=200.0, lambda_max=800.0
    )
    assert result_z0['mode'] == 'raw', "z=0 failed to render in raw mode"
    
    print(f"\n[OK] Zoom level test passed ({downsampled_count} levels downsampled)")

def test_zoom_saturation():
    """Test that extreme zooms just result in exact points without error, because 2094*2^-k goes to 0"""
    spectrum = generate_sample_spectrum(
        lambda_min=200.0, lambda_max=300.0, n_points=2094
    )
    
    # Beyond z_max: must return raw or downsampled with exact pts
    result = lttb_downsample(
        data=spectrum,
        zoom_level=12, # Extremely high zoom
        lambda_min=200.0,
        lambda_max=300.0
    )
    
    # 2094 * 2^-12 < 3, so should return raw
    assert result['mode'] == 'raw', "Should return raw at extreme zoom"
    
    print("[OK] Zoom saturation test passed")

def test_peak_retention():
    """Test that LTTB retains the global maximum even under heavy downsampling"""
    spectrum = generate_sample_spectrum(
        lambda_min=200.0, lambda_max=800.0, n_points=2094, num_peaks=5
    )
    
    # Find the true global maximum
    global_max = float(np.max(spectrum[:, 1]))
    
    result = lttb_downsample(
        data=spectrum,
        zoom_level=1,  # Downsampling active
        lambda_min=200.0,
        lambda_max=800.0
    )
    
    assert result['mode'] == 'downsampled'
    output_max = max(pt['intensity'] for pt in result['data'])
    
    assert output_max == global_max, (
        f"Peak lost: original max={global_max:.2f}, output max={output_max:.2f}"
    )
    
    print(f"[OK] Peak retention test passed (max={global_max:.2f})")

def test_raw_plasma_preserved():
    """Test that raw_plasma column is preserved through LTTB downsampling"""
    spectrum = generate_sample_spectrum(n_points=2094)
    
    result = lttb_downsample(
        data=spectrum,
        zoom_level=1,
        lambda_min=200.0,
        lambda_max=800.0
    )
    
    assert result['mode'] == 'downsampled'
    for pt in result['data']:
        assert 'raw_plasma' in pt, "raw_plasma missing from output"
        assert pt['raw_plasma'] > 0, "raw_plasma should be positive"
    
    print("[OK] raw_plasma preservation test passed")

def test_monotonicity():
    """Test that output wavelengths are monotonically increasing"""
    spectrum = generate_sample_spectrum(n_points=2094)
    
    result = lttb_downsample(
        data=spectrum,
        zoom_level=1,
        lambda_min=200.0,
        lambda_max=800.0
    )
    
    assert result['mode'] == 'downsampled'
    wavelengths = [pt['wavelength_nm'] for pt in result['data']]
    for i in range(1, len(wavelengths)):
        assert wavelengths[i] > wavelengths[i-1], (
            f"Monotonicity violated at index {i}: "
            f"{wavelengths[i-1]:.4f} >= {wavelengths[i]:.4f}"
        )
    
    print("[OK] Monotonicity test passed")

if __name__ == "__main__":
    test_generate_spectrum()
    test_zoom_levels()
    test_zoom_saturation()
    test_peak_retention()
    test_raw_plasma_preserved()
    test_monotonicity()
    print("\n" + "=" * 60)
    print("All LTTB tests passed!")
    print("=" * 60)

import numpy as np
from app.core.downsampling import (
    adaptive_minmax_downsample,
    generate_sample_spectrum,
    calculate_zoom_max,
    DownsampleConfig
)

def test_generate_spectrum():
    """Test synthetic spectrum generation with CH3 channel count"""
    spectrum = generate_sample_spectrum(
        lambda_min=200.0,
        lambda_max=800.0,
        n_points=2094,
        num_peaks=10
    )
    
    assert spectrum.shape == (2094, 2), "Spectrum shape incorrect"
    assert np.all(spectrum[:, 0] >= 200.0), "Wavelengths below minimum"
    assert np.all(spectrum[:, 0] <= 800.0), "Wavelengths above maximum"
    print("[OK] Spectrum generation test passed")

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
        result = adaptive_minmax_downsample(
            data=spectrum,
            zoom_level=zoom,
            lambda_min=200.0,
            lambda_max=800.0
        )
        
        print(f"\nZoom {zoom}:")
        print(f"  Mode: {result['mode']}")
        print(f"  Original points: {result.get('original_points', 0)}")
        print(f"  Buckets: {result.get('n_buckets', 0)}")
        print(f"  Reduction: {result.get('reduction_factor', 0):.2f}x")
        
        assert result['mode'] in ['downsampled', 'raw'], f"Invalid mode at zoom {zoom}"
        
        if result['mode'] == 'downsampled':
            downsampled_count += 1
            assert result['reduction_factor'] >= 1.0, f"No reduction at zoom {zoom}"
    
    # Must have at least 3 zoom levels with effective downsampling
    assert downsampled_count >= 3, (
        f"Only {downsampled_count} zoom levels downsampled (expected >= 3). "
        f"BASE_BUCKETS is likely too high for the data density."
    )
    
    # z=0 must give significant reduction (>= 5x)
    result_z0 = adaptive_minmax_downsample(
        data=spectrum, zoom_level=0,
        lambda_min=200.0, lambda_max=800.0
    )
    assert result_z0['reduction_factor'] >= 5.0, (
        f"z=0 reduction {result_z0['reduction_factor']:.1f}x < 5x. "
        f"BASE_BUCKETS too high."
    )
    
    print(f"\n[OK] Zoom level test passed ({downsampled_count} levels downsampled)")

def test_zoom_saturation():
    """Test that zoom saturation respects both instrument and data-density limits"""
    spectrum = generate_sample_spectrum(
        lambda_min=200.0, lambda_max=300.0, n_points=2094
    )
    
    config = DownsampleConfig()
    z_max = calculate_zoom_max(100.0, config, n_points=2094)
    
    print(f"\nZoom saturation test:")
    print(f"  z_max = {z_max} (with density awareness)")
    
    # At z_max: should still be downsampled or just at the edge
    result = adaptive_minmax_downsample(
        data=spectrum,
        zoom_level=int(z_max),
        lambda_min=200.0,
        lambda_max=300.0
    )
    print(f"  At z_max: mode = {result['mode']}, buckets = {result.get('n_buckets', 0)}")
    assert result['mode'] in ['downsampled', 'raw'], "Should be downsampled or raw at z_max"
    
    # Beyond z_max: must return raw
    result = adaptive_minmax_downsample(
        data=spectrum,
        zoom_level=int(z_max) + 1,
        lambda_min=200.0,
        lambda_max=300.0
    )
    print(f"  Beyond z_max: mode = {result['mode']}")
    assert result['mode'] == 'raw', "Should return raw beyond z_max"
    
    print("[OK] Zoom saturation test passed")

if __name__ == "__main__":
    test_generate_spectrum()
    test_zoom_levels()
    test_zoom_saturation()
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)

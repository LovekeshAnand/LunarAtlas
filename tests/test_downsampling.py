import numpy as np
from app.core.downsampling import (
    adaptive_minmax_downsample,
    generate_sample_spectrum,
    calculate_zoom_max,
    DownsampleConfig
)

def test_generate_spectrum():
    """Test synthetic spectrum generation"""
    spectrum = generate_sample_spectrum(
        lambda_min=200.0,
        lambda_max=800.0,
        n_points=2049,
        num_peaks=10
    )
    
    assert spectrum.shape == (2049, 2), "Spectrum shape incorrect"
    assert np.all(spectrum[:, 0] >= 200.0), "Wavelengths below minimum"
    assert np.all(spectrum[:, 0] <= 800.0), "Wavelengths above maximum"
    print("✓ Spectrum generation test passed")

def test_zoom_levels():
    """Test downsampling at different zoom levels"""
    spectrum = generate_sample_spectrum()
    
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
    
    print("\n✓ Zoom level test passed")

def test_zoom_saturation():
    """Test zoom saturation behavior"""
    spectrum = generate_sample_spectrum(lambda_min=200.0, lambda_max=300.0)
    
    config = DownsampleConfig()
    z_max = calculate_zoom_max(100.0, config)  # 100nm range
    
    print(f"\nZoom saturation test:")
    print(f"  z_max = {z_max}")
    
    # Test at z_max - should downsample
    result = adaptive_minmax_downsample(
        data=spectrum,
        zoom_level=int(z_max),
        lambda_min=200.0,
        lambda_max=300.0
    )
    print(f"  At z_max: mode = {result['mode']}")
    assert result['mode'] == 'downsampled', "Should downsample at z_max"
    
    # Test beyond z_max - should return raw
    result = adaptive_minmax_downsample(
        data=spectrum,
        zoom_level=int(z_max) + 1,
        lambda_min=200.0,
        lambda_max=300.0
    )
    print(f"  Beyond z_max: mode = {result['mode']}")
    assert result['mode'] == 'raw', "Should return raw beyond z_max"
    
    print("✓ Zoom saturation test passed")

if __name__ == "__main__":
    test_generate_spectrum()
    test_zoom_levels()
    test_zoom_saturation()
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)

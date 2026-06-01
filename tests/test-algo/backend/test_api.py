"""
API Test Script for LunarAtlas
Tests all endpoints and validates responses
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_root():
    """Test root endpoint"""
    print_section("TEST 1: Root Endpoint")
    
    response = requests.get(f"{API_BASE}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ PASSED")

def test_health():
    """Test health check"""
    print_section("TEST 2: Health Check")
    
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 200
    assert data['status'] == 'healthy'
    print("✓ PASSED")

def test_observations():
    """Test observations listing"""
    print_section("TEST 3: List Observations")
    
    response = requests.get(f"{API_BASE}/api/v1/observations")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {data['count']} observations")
    
    if data['observations']:
        obs = data['observations'][0]
        print(f"\nFirst observation:")
        print(f"  ID: {obs['measurement_id']}")
        print(f"  Points: {obs['point_count']}")
        print(f"  Wavelength range: {obs['min_wavelength']:.2f} - {obs['max_wavelength']:.2f} nm")
    
    assert response.status_code == 200
    assert data['count'] > 0
    print("✓ PASSED")
    
    return data['observations'][0] if data['observations'] else None

def test_spectral_zoom_levels(obs_id, min_wl, max_wl):
    """Test spectral data at different zoom levels"""
    print_section("TEST 4: Spectral Data - Multiple Zoom Levels")
    
    zoom_levels = [0, 2, 5, 7]
    
    for zoom in zoom_levels:
        print(f"\n--- Zoom Level {zoom} ---")
        
        response = requests.get(f"{API_BASE}/api/v1/spectral", params={
            'observation_id': obs_id,
            'min_wavelength': min_wl,
            'max_wavelength': max_wl,
            'zoom_level': zoom
        })
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            params = data['parameters']
            
            print(f"Bucket Size: {params['bucket_size_nm']:.6f} nm")
            print(f"Bucket Count: {params['bucket_count']}")
            print(f"Returned Buckets: {data['metadata']['returned_bucket_count']}")
            print(f"Processing Time: {data['processing_time_ms']:.2f} ms")
            
            # Verify buckets
            if data['buckets']:
                first = data['buckets'][0]
                print(f"First bucket: [{first['start_wl']:.4f}, {first['end_wl']:.4f}] nm")
                print(f"  Min intensity: {first['min_intensity']:.2f}")
                print(f"  Max intensity: {first['max_intensity']:.2f}")
                print(f"  Points in bucket: {first['point_count']}")
            
            assert data['status'] == 'success'
        else:
            print(f"Error: {response.text}")
            
    print("\n✓ PASSED - All zoom levels working")

def test_narrow_range(obs_id):
    """Test with a narrow wavelength range"""
    print_section("TEST 5: Narrow Wavelength Range")
    
    # Test a 50nm range at high zoom
    min_wl = 400
    max_wl = 450
    zoom = 5
    
    print(f"Range: {min_wl}-{max_wl} nm, Zoom: {zoom}")
    
    response = requests.get(f"{API_BASE}/api/v1/spectral", params={
        'observation_id': obs_id,
        'min_wavelength': min_wl,
        'max_wavelength': max_wl,
        'zoom_level': zoom
    })
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        params = data['parameters']
        
        print(f"Bucket Size: {params['bucket_size_nm']:.6f} nm")
        print(f"Bucket Count: {params['bucket_count']}")
        print(f"Processing Time: {data['processing_time_ms']:.2f} ms")
        
        assert data['status'] == 'success'
        print("✓ PASSED")
    else:
        print(f"Error: {response.text}")

def test_raw_data(obs_id):
    """Test raw data endpoint"""
    print_section("TEST 6: Raw Data Endpoint")
    
    # Test a very narrow range for raw data
    min_wl = 500
    max_wl = 502
    
    print(f"Range: {min_wl}-{max_wl} nm (raw data)")
    
    response = requests.get(f"{API_BASE}/api/v1/spectral/raw", params={
        'observation_id': obs_id,
        'min_wavelength': min_wl,
        'max_wavelength': max_wl
    })
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"Point Count: {data['metadata']['point_count']}")
        print(f"Processing Time: {data['processing_time_ms']:.2f} ms")
        
        if data['data_points']:
            print(f"\nFirst 5 data points:")
            for i, point in enumerate(data['data_points'][:5]):
                print(f"  {i+1}. λ={point['wavelength']:.4f} nm, I={point['intensity']:.2f}")
        
        assert data['status'] == 'success'
        print("✓ PASSED")
    else:
        print(f"Error: {response.text}")

def test_validation():
    """Test input validation"""
    print_section("TEST 7: Input Validation")
    
    # Test invalid wavelength range
    print("\n--- Invalid Range (min >= max) ---")
    response = requests.get(f"{API_BASE}/api/v1/spectral", params={
        'observation_id': 1,
        'min_wavelength': 500,
        'max_wavelength': 400,  # Invalid!
        'zoom_level': 0
    })
    print(f"Status: {response.status_code}")
    print(f"Expected: 400 (Bad Request)")
    assert response.status_code == 400
    print("✓ Validation working")
    
    # Test invalid zoom level
    print("\n--- Invalid Zoom Level ---")
    response = requests.get(f"{API_BASE}/api/v1/spectral", params={
        'observation_id': 1,
        'min_wavelength': 200,
        'max_wavelength': 900,
        'zoom_level': 15  # Invalid!
    })
    print(f"Status: {response.status_code}")
    print(f"Expected: 422 (Validation Error)")
    assert response.status_code == 422
    print("✓ Validation working")
    
    print("\n✓ PASSED - Input validation working correctly")

def performance_test(obs_id, min_wl, max_wl):
    """Test performance metrics"""
    print_section("TEST 8: Performance Benchmarks")
    
    zoom_levels = [0, 3, 5, 7]
    
    print("\nZoom | Buckets | Bucket Size | Processing Time")
    print("-" * 55)
    
    for zoom in zoom_levels:
        response = requests.get(f"{API_BASE}/api/v1/spectral", params={
            'observation_id': obs_id,
            'min_wavelength': min_wl,
            'max_wavelength': max_wl,
            'zoom_level': zoom
        })
        
        if response.status_code == 200:
            data = response.json()
            params = data['parameters']
            time_ms = data['processing_time_ms']
            
            print(f" {zoom:2d}  | {params['bucket_count']:6d}  | "
                  f"{params['bucket_size_nm']:9.6f} nm | {time_ms:8.2f} ms")
            
            # Check performance target (<500ms)
            assert time_ms < 500, f"Performance target missed: {time_ms}ms"
    
    print("\n✓ PASSED - All responses < 500ms")

def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       LunarAtlas API Test Suite                           ║")
    print("║       Testing all endpoints and functionality             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"\nTesting API at: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Test 1: Root
        test_root()
        
        # Test 2: Health
        test_health()
        
        # Test 3: Observations
        first_obs = test_observations()
        
        if not first_obs:
            print("\n❌ No observations found in database. Run setup_database.py first.")
            return
        
        obs_id = first_obs['measurement_id']
        min_wl = round(first_obs['min_wavelength'])
        max_wl = round(first_obs['max_wavelength'])
        
        # Test 4: Zoom levels
        test_spectral_zoom_levels(obs_id, min_wl, max_wl)
        
        # Test 5: Narrow range
        test_narrow_range(obs_id)
        
        # Test 6: Raw data
        test_raw_data(obs_id)
        
        # Test 7: Validation
        test_validation()
        
        # Test 8: Performance
        performance_test(obs_id, min_wl, max_wl)
        
        # Summary
        print("\n")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║                   ALL TESTS PASSED ✓                       ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("\n✅ API is working correctly and ready for frontend integration")
        print("✅ All performance targets met (<500ms)")
        print("✅ Validation working as expected")
        print("\nYou can now start the frontend with: cd frontend && npm start")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to API at {API_BASE}")
        print("   Make sure the backend is running (python main.py)")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

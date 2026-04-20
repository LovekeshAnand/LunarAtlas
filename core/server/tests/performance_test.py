import time
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_performance():
    """Test API response times"""
    
    async with httpx.AsyncClient() as client:
        print("Performance Testing")
        print("=" * 60)
        
        try:
            # Test 1: Health check
            start = time.time()
            response = await client.get(f"{BASE_URL}/health")
            elapsed = (time.time() - start) * 1000
            print(f"Health check: {elapsed:.2f}ms - Status: {response.status_code}")
            
            response = await client.get(f"{BASE_URL}/measurements?limit=10")
            elapsed = (time.time() - start) * 1000
            print(f"List measurements: {elapsed:.2f}ms - Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[FAIL] Measurements query failed: {response.json()}")
                return
            
            measurements = response.json()
            if not measurements:
                print("\n[WARNING] No measurements found in DB. /spectrum tests will be skipped.")
                return
                
            # Use the first real measurement ID
            target_id = measurements[0]['measurement_id']
            print(f"\nTargeting Measurement ID: {target_id}")
            
            # Test 3: Get spectrum (first call - cache MISS)
            print("\nSpectrum queries (cache testing):")
            
            for zoom in [0, 2, 4]:
                # First call (cache MISS)
                start = time.time()
                try:
                    response = await client.get(
                        f"{BASE_URL}/spectrum",
                        params={
                            "measurement_id": target_id,
                            "lambda_min": 200,
                            "lambda_max": 800,
                            "zoom_level": zoom,
                            "use_cache": True
                        },
                        timeout=10.0
                    )
                except Exception as req_err:
                    print(f"  Zoom {zoom}: Request failed - {req_err}")
                    continue
                elapsed_miss = (time.time() - start) * 1000
                
                if response.status_code != 200:
                    print(f"  Zoom {zoom}: Status {response.status_code} - {response.text[:200]}")
                    continue
                
                data = response.json()
                
                # Second call (cache HIT)
                start = time.time()
                response = await client.get(
                    f"{BASE_URL}/spectrum",
                    params={
                        "measurement_id": target_id,
                        "lambda_min": 200,
                        "lambda_max": 800,
                        "zoom_level": zoom,
                        "use_cache": True
                    }
                )
                elapsed_hit = (time.time() - start) * 1000
                
                print(f"  Zoom {zoom}:")
                print(f"    Cache MISS: {elapsed_miss:.2f}ms")
                print(f"    Cache HIT:  {elapsed_hit:.2f}ms")
                if elapsed_hit > 0:
                    print(f"    Speedup: {elapsed_miss/elapsed_hit:.2f}x")
                print(f"    Mode: {data.get('mode', 'N/A')}, Points: {len(data.get('data', []))}")
                
                if response.status_code != 200:
                    print(f"    Error detail: {data}")
        
        except Exception as e:
            print(f"\n[FAIL] Performance test failed: {e}")
            print("Make sure the API server is running at http://localhost:8000")

        print("\n" + "=" * 60)
        print("Performance test complete!")

if __name__ == "__main__":
    asyncio.run(test_performance())

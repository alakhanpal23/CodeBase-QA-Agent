#!/usr/bin/env python3
"""
Performance and Load Testing Suite
Tests system performance under various load conditions
"""

import requests
import time
import threading
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import json

API_BASE = "http://localhost:8000"

class PerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.errors = []
    
    def add_result(self, response_time: float, success: bool, error: str = None):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.response_times:
            return {"error": "No data collected"}
        
        return {
            "total_requests": len(self.response_times),
            "success_rate": self.success_count / len(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
            "p99_response_time": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times),
            "errors": self.errors[:10]  # Show first 10 errors
        }

def make_health_request() -> tuple:
    """Make a health check request and return (response_time, success, error)"""
    start_time = time.time()
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        response_time = time.time() - start_time
        success = response.status_code == 200
        error = None if success else f"HTTP {response.status_code}"
        return response_time, success, error
    except Exception as e:
        response_time = time.time() - start_time
        return response_time, False, str(e)

def make_query_request() -> tuple:
    """Make a query request and return (response_time, success, error)"""
    start_time = time.time()
    try:
        payload = {
            "question": "How does the application work?",
            "repo_ids": ["test-repo"],
            "k": 3
        }
        response = requests.post(f"{API_BASE}/query", json=payload, timeout=30)
        response_time = time.time() - start_time
        success = response.status_code == 200
        error = None if success else f"HTTP {response.status_code}"
        return response_time, success, error
    except Exception as e:
        response_time = time.time() - start_time
        return response_time, False, str(e)

def test_baseline_performance():
    """Test baseline performance with single requests"""
    print("📊 Testing Baseline Performance...")
    
    metrics = PerformanceMetrics()
    
    # Test health endpoint
    for i in range(10):
        response_time, success, error = make_health_request()
        metrics.add_result(response_time, success, error)
        time.sleep(0.1)  # Small delay between requests
    
    stats = metrics.get_stats()
    print(f"Health Endpoint Baseline:")
    print(f"  Average Response Time: {stats['avg_response_time']*1000:.0f}ms")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  P95 Response Time: {stats['p95_response_time']*1000:.0f}ms")
    
    # Evaluate results
    if stats['avg_response_time'] < 1.0 and stats['success_rate'] > 0.95:
        print("✅ Baseline Performance: PASS")
        return True
    else:
        print("❌ Baseline Performance: FAIL")
        return False

def test_concurrent_load():
    """Test system under concurrent load"""
    print("\n⚡ Testing Concurrent Load...")
    
    test_scenarios = [
        {"name": "Light Load", "concurrent_users": 5, "requests_per_user": 10},
        {"name": "Medium Load", "concurrent_users": 10, "requests_per_user": 10},
        {"name": "Heavy Load", "concurrent_users": 20, "requests_per_user": 5},
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\n🔄 Running {scenario['name']} Test...")
        metrics = PerformanceMetrics()
        
        def user_simulation():
            user_metrics = PerformanceMetrics()
            for _ in range(scenario['requests_per_user']):
                response_time, success, error = make_health_request()
                user_metrics.add_result(response_time, success, error)
                time.sleep(0.1)  # Small delay between requests
            return user_metrics
        
        # Run concurrent users
        with ThreadPoolExecutor(max_workers=scenario['concurrent_users']) as executor:
            futures = [executor.submit(user_simulation) for _ in range(scenario['concurrent_users'])]
            
            for future in as_completed(futures):
                user_metrics = future.result()
                metrics.response_times.extend(user_metrics.response_times)
                metrics.success_count += user_metrics.success_count
                metrics.error_count += user_metrics.error_count
                metrics.errors.extend(user_metrics.errors)
        
        stats = metrics.get_stats()
        results[scenario['name']] = stats
        
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
        print(f"  Average Response Time: {stats['avg_response_time']*1000:.0f}ms")
        print(f"  P95 Response Time: {stats['p95_response_time']*1000:.0f}ms")
        
        # Evaluate results
        if stats['success_rate'] > 0.9 and stats['avg_response_time'] < 2.0:
            print(f"  ✅ {scenario['name']}: PASS")
        else:
            print(f"  ❌ {scenario['name']}: FAIL")
    
    return results

def test_sustained_load():
    """Test system under sustained load"""
    print("\n🔄 Testing Sustained Load...")
    
    duration_seconds = 60  # 1 minute test
    requests_per_second = 2
    
    metrics = PerformanceMetrics()
    start_time = time.time()
    
    def make_sustained_requests():
        while time.time() - start_time < duration_seconds:
            response_time, success, error = make_health_request()
            metrics.add_result(response_time, success, error)
            time.sleep(1.0 / requests_per_second)
    
    # Run sustained load
    threads = []
    for _ in range(2):  # 2 threads for sustained load
        thread = threading.Thread(target=make_sustained_requests)
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    stats = metrics.get_stats()
    
    print(f"Sustained Load Results:")
    print(f"  Duration: {duration_seconds}s")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Requests/Second: {stats['total_requests']/duration_seconds:.1f}")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  Average Response Time: {stats['avg_response_time']*1000:.0f}ms")
    
    # Evaluate results
    if stats['success_rate'] > 0.95 and stats['avg_response_time'] < 1.5:
        print("✅ Sustained Load: PASS")
        return True
    else:
        print("❌ Sustained Load: FAIL")
        return False

def test_memory_usage():
    """Test for memory leaks by monitoring response times over time"""
    print("\n🧠 Testing Memory Usage Patterns...")
    
    metrics = PerformanceMetrics()
    batch_size = 50
    num_batches = 5
    
    batch_averages = []
    
    for batch in range(num_batches):
        print(f"  Running batch {batch + 1}/{num_batches}...")
        batch_metrics = PerformanceMetrics()
        
        for _ in range(batch_size):
            response_time, success, error = make_health_request()
            batch_metrics.add_result(response_time, success, error)
            metrics.add_result(response_time, success, error)
            time.sleep(0.05)  # Small delay
        
        batch_stats = batch_metrics.get_stats()
        batch_averages.append(batch_stats['avg_response_time'])
        print(f"    Batch {batch + 1} avg response time: {batch_stats['avg_response_time']*1000:.0f}ms")
    
    # Check if response times are increasing (potential memory leak)
    if len(batch_averages) > 1:
        trend = batch_averages[-1] - batch_averages[0]
        if trend > 0.5:  # More than 500ms increase
            print(f"⚠️  Potential memory leak detected (response time increased by {trend*1000:.0f}ms)")
            return False
        else:
            print(f"✅ Memory Usage: PASS (stable response times)")
            return True
    
    return True

def test_error_recovery():
    """Test system recovery after errors"""
    print("\n🔄 Testing Error Recovery...")
    
    # First, make some normal requests
    print("  Making baseline requests...")
    baseline_metrics = PerformanceMetrics()
    for _ in range(10):
        response_time, success, error = make_health_request()
        baseline_metrics.add_result(response_time, success, error)
        time.sleep(0.1)
    
    baseline_stats = baseline_metrics.get_stats()
    baseline_avg = baseline_stats['avg_response_time']
    
    # Then make some potentially problematic requests
    print("  Making potentially problematic requests...")
    for _ in range(5):
        try:
            # Make requests with very short timeout to potentially cause errors
            requests.get(f"{API_BASE}/health", timeout=0.001)
        except:
            pass  # Expected to fail
        time.sleep(0.1)
    
    # Then test recovery
    print("  Testing recovery...")
    recovery_metrics = PerformanceMetrics()
    for _ in range(10):
        response_time, success, error = make_health_request()
        recovery_metrics.add_result(response_time, success, error)
        time.sleep(0.1)
    
    recovery_stats = recovery_metrics.get_stats()
    recovery_avg = recovery_stats['avg_response_time']
    
    # Check if system recovered
    if recovery_stats['success_rate'] > 0.9 and abs(recovery_avg - baseline_avg) < 0.5:
        print("✅ Error Recovery: PASS")
        return True
    else:
        print("❌ Error Recovery: FAIL")
        return False

def test_api_endpoints_performance():
    """Test performance of different API endpoints"""
    print("\n🎯 Testing API Endpoints Performance...")
    
    endpoints = [
        {"name": "Health", "method": "GET", "url": f"{API_BASE}/health", "timeout": 5},
        {"name": "Repos List", "method": "GET", "url": f"{API_BASE}/repos", "timeout": 10},
        {"name": "Stats", "method": "GET", "url": f"{API_BASE}/stats", "timeout": 10},
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"  Testing {endpoint['name']} endpoint...")
        metrics = PerformanceMetrics()
        
        for _ in range(10):
            start_time = time.time()
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(endpoint['url'], timeout=endpoint['timeout'])
                else:
                    response = requests.post(endpoint['url'], timeout=endpoint['timeout'])
                
                response_time = time.time() - start_time
                success = response.status_code == 200
                error = None if success else f"HTTP {response.status_code}"
                
            except Exception as e:
                response_time = time.time() - start_time
                success = False
                error = str(e)
            
            metrics.add_result(response_time, success, error)
            time.sleep(0.1)
        
        stats = metrics.get_stats()
        results[endpoint['name']] = stats
        
        print(f"    Average Response Time: {stats['avg_response_time']*1000:.0f}ms")
        print(f"    Success Rate: {stats['success_rate']*100:.1f}%")
        
        # Evaluate results
        if stats['success_rate'] > 0.9 and stats['avg_response_time'] < endpoint['timeout']:
            print(f"    ✅ {endpoint['name']}: PASS")
        else:
            print(f"    ❌ {endpoint['name']}: FAIL")
    
    return results

def main():
    """Run all performance tests"""
    print("⚡ Starting Performance and Load Testing Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run all performance tests
    test_results.append(test_baseline_performance())
    concurrent_results = test_concurrent_load()
    test_results.append(all(stats['success_rate'] > 0.9 for stats in concurrent_results.values()))
    test_results.append(test_sustained_load())
    test_results.append(test_memory_usage())
    test_results.append(test_error_recovery())
    endpoint_results = test_api_endpoints_performance()
    test_results.append(all(stats['success_rate'] > 0.9 for stats in endpoint_results.values()))
    
    # Summary
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"PERFORMANCE TEST SUMMARY: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL PERFORMANCE TESTS PASSED!")
        print("💪 System is ready for production load!")
        return 0
    else:
        print("⚠️  Some performance tests failed.")
        print("🔧 Consider optimizing before production deployment.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Performance tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during performance testing: {e}")
        sys.exit(1)
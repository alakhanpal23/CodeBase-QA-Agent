#!/usr/bin/env python3
"""
Master Test Runner - Runs all test suites and provides comprehensive report
"""

import subprocess
import sys
import time
import os
import json
from datetime import datetime
from typing import Dict, List, Any

class TestSuite:
    def __init__(self, name: str, script: str, description: str, required: bool = True):
        self.name = name
        self.script = script
        self.description = description
        self.required = required
        self.result = None
        self.duration = 0
        self.output = ""

class MasterTestRunner:
    def __init__(self):
        self.test_suites = [
            TestSuite(
                "Comprehensive API Tests",
                "tests/test_comprehensive.py",
                "End-to-end API functionality, security, and integration tests",
                required=True
            ),
            TestSuite(
                "Performance Tests",
                "tests/test_performance.py",
                "Load testing, concurrent requests, and performance benchmarks",
                required=True
            ),
            TestSuite(
                "Frontend E2E Tests",
                "tests/test_frontend_e2e.py",
                "Frontend user interface and user experience tests",
                required=False  # Optional since it requires Selenium
            ),
            TestSuite(
                "Basic Deployment Test",
                "test_deployment.py",
                "Basic deployment verification and smoke tests",
                required=True
            )
        ]
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("🔍 Checking Prerequisites...")
        
        # Check if backend is running
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is running")
            else:
                print("❌ Backend is not responding correctly")
                return False
        except Exception as e:
            print(f"❌ Backend is not accessible: {e}")
            print("💡 Make sure to start the backend first:")
            print("   cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return False
        
        # Check if frontend is running
        try:
            response = requests.get("http://localhost:3001", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is running")
            else:
                print("⚠️  Frontend may not be running (some tests will be skipped)")
        except Exception as e:
            print("⚠️  Frontend is not accessible (some tests will be skipped)")
        
        # Check Python dependencies
        required_packages = ["requests"]
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} is available")
            except ImportError:
                print(f"❌ {package} is not installed")
                return False
        
        # Check optional dependencies
        try:
            import selenium
            print("✅ Selenium is available (frontend tests will run)")
        except ImportError:
            print("⚠️  Selenium not available (frontend tests will be skipped)")
            # Mark frontend tests as not required
            for suite in self.test_suites:
                if "Frontend" in suite.name:
                    suite.required = False
        
        return True
    
    def run_test_suite(self, suite: TestSuite) -> bool:
        """Run a single test suite"""
        print(f"\n🚀 Running {suite.name}...")
        print(f"📝 {suite.description}")
        print("-" * 50)
        
        if not os.path.exists(suite.script):
            print(f"❌ Test script not found: {suite.script}")
            suite.result = False
            return False
        
        start_time = time.time()
        
        try:
            # Run the test script
            result = subprocess.run(
                [sys.executable, suite.script],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test suite
            )
            
            suite.duration = time.time() - start_time
            suite.output = result.stdout + result.stderr
            suite.result = result.returncode == 0
            
            # Print the output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            if suite.result:
                print(f"✅ {suite.name} completed successfully in {suite.duration:.1f}s")
            else:
                print(f"❌ {suite.name} failed after {suite.duration:.1f}s")
            
            return suite.result
            
        except subprocess.TimeoutExpired:
            suite.duration = time.time() - start_time
            suite.result = False
            suite.output = "Test suite timed out after 5 minutes"
            print(f"⏰ {suite.name} timed out after {suite.duration:.1f}s")
            return False
            
        except Exception as e:
            suite.duration = time.time() - start_time
            suite.result = False
            suite.output = str(e)
            print(f"💥 {suite.name} failed with error: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "summary": {
                "total_suites": len(self.test_suites),
                "passed_suites": sum(1 for suite in self.test_suites if suite.result),
                "failed_suites": sum(1 for suite in self.test_suites if suite.result is False),
                "skipped_suites": sum(1 for suite in self.test_suites if suite.result is None),
                "required_passed": sum(1 for suite in self.test_suites if suite.required and suite.result),
                "required_total": sum(1 for suite in self.test_suites if suite.required)
            },
            "suites": []
        }
        
        for suite in self.test_suites:
            suite_report = {
                "name": suite.name,
                "description": suite.description,
                "required": suite.required,
                "result": suite.result,
                "duration": suite.duration,
                "output_length": len(suite.output) if suite.output else 0
            }
            report["suites"].append(suite_report)
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Print test summary"""
        print(f"\n{'='*80}")
        print(f"🎯 MASTER TEST REPORT")
        print(f"{'='*80}")
        print(f"📅 Timestamp: {report['timestamp']}")
        print(f"⏱️  Total Duration: {report['total_duration']:.1f} seconds")
        print(f"\n📊 SUMMARY:")
        print(f"   Total Test Suites: {report['summary']['total_suites']}")
        print(f"   ✅ Passed: {report['summary']['passed_suites']}")
        print(f"   ❌ Failed: {report['summary']['failed_suites']}")
        print(f"   ⏭️  Skipped: {report['summary']['skipped_suites']}")
        print(f"   🎯 Required Passed: {report['summary']['required_passed']}/{report['summary']['required_total']}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for suite_report in report['suites']:
            status_icon = "✅" if suite_report['result'] else "❌" if suite_report['result'] is False else "⏭️"
            required_text = "(Required)" if suite_report['required'] else "(Optional)"
            print(f"   {status_icon} {suite_report['name']} {required_text} - {suite_report['duration']:.1f}s")
            print(f"      {suite_report['description']}")
        
        # Overall assessment
        required_passed = report['summary']['required_passed']
        required_total = report['summary']['required_total']
        
        print(f"\n🏆 OVERALL ASSESSMENT:")
        if required_passed == required_total:
            print("   🎉 ALL REQUIRED TESTS PASSED!")
            print("   🚀 System is PRODUCTION READY!")
            if report['summary']['failed_suites'] > 0:
                print("   ℹ️  Some optional tests failed, but core functionality is working")
        else:
            print("   ⚠️  SOME REQUIRED TESTS FAILED")
            print("   🔧 Please fix issues before production deployment")
        
        print(f"{'='*80}")
    
    def save_report(self, report: Dict[str, Any]):
        """Save report to file"""
        try:
            os.makedirs("test_reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_reports/test_report_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📄 Detailed report saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save report: {e}")
    
    def run_all_tests(self) -> bool:
        """Run all test suites and return overall success"""
        print("🧪 MASTER TEST RUNNER - CodeBase QA Agent")
        print("=" * 80)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Cannot run tests.")
            return False
        
        self.start_time = time.time()
        
        # Run each test suite
        for suite in self.test_suites:
            try:
                self.run_test_suite(suite)
            except KeyboardInterrupt:
                print(f"\n🛑 Test suite {suite.name} interrupted by user")
                suite.result = None
                break
            except Exception as e:
                print(f"\n💥 Unexpected error in {suite.name}: {e}")
                suite.result = False
        
        self.end_time = time.time()
        
        # Generate and display report
        report = self.generate_report()
        self.print_summary(report)
        self.save_report(report)
        
        # Return overall success
        required_passed = report['summary']['required_passed']
        required_total = report['summary']['required_total']
        return required_passed == required_total

def main():
    """Main entry point"""
    runner = MasterTestRunner()
    
    try:
        success = runner.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
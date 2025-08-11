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
        required_packages = ["requests", "concurrent.futures"]
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
            }\n            report["suites"].append(suite_report)\n        \n        return report\n    \n    def print_summary(self, report: Dict[str, Any]):\n        \"\"\"Print test summary\"\"\"\n        print(f\"\\n{'='*80}\")\n        print(f\"🎯 MASTER TEST REPORT\")\n        print(f\"{'='*80}\")\n        print(f\"📅 Timestamp: {report['timestamp']}\")\n        print(f\"⏱️  Total Duration: {report['total_duration']:.1f} seconds\")\n        print(f\"\\n📊 SUMMARY:\")\n        print(f\"   Total Test Suites: {report['summary']['total_suites']}\")\n        print(f\"   ✅ Passed: {report['summary']['passed_suites']}\")\n        print(f\"   ❌ Failed: {report['summary']['failed_suites']}\")\n        print(f\"   ⏭️  Skipped: {report['summary']['skipped_suites']}\")\n        print(f\"   🎯 Required Passed: {report['summary']['required_passed']}/{report['summary']['required_total']}\")\n        \n        print(f\"\\n📋 DETAILED RESULTS:\")\n        for suite_report in report['suites']:\n            status_icon = \"✅\" if suite_report['result'] else \"❌\" if suite_report['result'] is False else \"⏭️\"\n            required_text = \"(Required)\" if suite_report['required'] else \"(Optional)\"\n            print(f\"   {status_icon} {suite_report['name']} {required_text} - {suite_report['duration']:.1f}s\")\n            print(f\"      {suite_report['description']}\")\n        \n        # Overall assessment\n        required_passed = report['summary']['required_passed']\n        required_total = report['summary']['required_total']\n        \n        print(f\"\\n🏆 OVERALL ASSESSMENT:\")\n        if required_passed == required_total:\n            print(\"   🎉 ALL REQUIRED TESTS PASSED!\")\n            print(\"   🚀 System is PRODUCTION READY!\")\n            if report['summary']['failed_suites'] > 0:\n                print(\"   ℹ️  Some optional tests failed, but core functionality is working\")\n        else:\n            print(\"   ⚠️  SOME REQUIRED TESTS FAILED\")\n            print(\"   🔧 Please fix issues before production deployment\")\n        \n        print(f\"{'='*80}\")\n    \n    def save_report(self, report: Dict[str, Any]):\n        \"\"\"Save report to file\"\"\"\n        try:\n            os.makedirs(\"test_reports\", exist_ok=True)\n            timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n            filename = f\"test_reports/test_report_{timestamp}.json\"\n            \n            with open(filename, 'w') as f:\n                json.dump(report, f, indent=2)\n            \n            print(f\"📄 Detailed report saved to: {filename}\")\n        except Exception as e:\n            print(f\"⚠️  Could not save report: {e}\")\n    \n    def run_all_tests(self) -> bool:\n        \"\"\"Run all test suites and return overall success\"\"\"\n        print(\"🧪 MASTER TEST RUNNER - CodeBase QA Agent\")\n        print(\"=\" * 80)\n        \n        # Check prerequisites\n        if not self.check_prerequisites():\n            print(\"❌ Prerequisites not met. Cannot run tests.\")\n            return False\n        \n        self.start_time = time.time()\n        \n        # Run each test suite\n        for suite in self.test_suites:\n            try:\n                self.run_test_suite(suite)\n            except KeyboardInterrupt:\n                print(f\"\\n🛑 Test suite {suite.name} interrupted by user\")\n                suite.result = None\n                break\n            except Exception as e:\n                print(f\"\\n💥 Unexpected error in {suite.name}: {e}\")\n                suite.result = False\n        \n        self.end_time = time.time()\n        \n        # Generate and display report\n        report = self.generate_report()\n        self.print_summary(report)\n        self.save_report(report)\n        \n        # Return overall success\n        required_passed = report['summary']['required_passed']\n        required_total = report['summary']['required_total']\n        return required_passed == required_total\n\ndef main():\n    \"\"\"Main entry point\"\"\"\n    runner = MasterTestRunner()\n    \n    try:\n        success = runner.run_all_tests()\n        return 0 if success else 1\n    except KeyboardInterrupt:\n        print(\"\\n🛑 Testing interrupted by user\")\n        return 1\n    except Exception as e:\n        print(f\"\\n💥 Unexpected error: {e}\")\n        return 1\n\nif __name__ == \"__main__\":\n    exit_code = main()\n    sys.exit(exit_code)
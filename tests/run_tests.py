#!/usr/bin/env python3
"""
DoomBox Test Runner
Runs all tests and provides a comprehensive report
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

class TestRunner:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.tests_dir = self.project_root / "tests"
        self.results = []
        
    def run_test(self, test_path, test_name):
        """Run a single test and capture results"""
        print(f"🧪 Running: {test_name}")
        
        try:
            # Make sure the test file is executable
            os.chmod(test_path, 0o755)
            
            # Run the test
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            
            test_result = {
                "name": test_name,
                "path": str(test_path),
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(test_result)
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status}")
            
            if not success and result.stderr:
                print(f"   Error: {result.stderr[:200]}...")
                
            return success
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ TIMEOUT")
            self.results.append({
                "name": test_name,
                "path": str(test_path),
                "success": False,
                "error": "timeout",
                "timestamp": datetime.now().isoformat()
            })
            return False
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.results.append({
                "name": test_name,
                "path": str(test_path),
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
            
    def discover_tests(self):
        """Discover all test files"""
        test_files = []
        
        for test_file in self.tests_dir.rglob("*.py"):
            if test_file.name.startswith("test_") or test_file.name.startswith("test-"):
                relative_path = test_file.relative_to(self.tests_dir)
                test_files.append((test_file, str(relative_path)))
                
        return sorted(test_files)
        
    def run_all_tests(self):
        """Run all discovered tests"""
        print("🚀 DoomBox Test Runner")
        print("=" * 50)
        
        # Discover tests
        test_files = self.discover_tests()
        
        if not test_files:
            print("❌ No test files found")
            return False
            
        print(f"📋 Found {len(test_files)} test files")
        print()
        
        # Run tests
        passed = 0
        total = len(test_files)
        
        for test_path, test_name in test_files:
            success = self.run_test(test_path, test_name)
            if success:
                passed += 1
                
        # Generate report
        self.generate_report(passed, total)
        
        return passed == total
        
    def generate_report(self, passed, total):
        """Generate test report"""
        print()
        print("📊 Test Results Summary")
        print("=" * 50)
        
        # Summary
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        print()
        
        # Detailed results
        for result in self.results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{result['name']:.<40} {status}")
            
            if not result["success"]:
                if "error" in result:
                    print(f"   Error: {result['error']}")
                elif result.get("stderr"):
                    print(f"   Error: {result['stderr'][:100]}...")
                    
        print()
        
        # Save detailed report
        report_file = self.project_root / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": (passed/total)*100
                },
                "results": self.results
            }, f, indent=2)
            
        print(f"📄 Detailed report saved to: {report_file}")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")

def main():
    """Main entry point"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"📁 Project root: {project_root}")
    
    # Create test runner
    runner = TestRunner(project_root)
    
    # Run tests
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test runner script for hotel controller integration tests
"""
import sys
import os
import subprocess

# Add the parent directory to Python path to access the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    """Run the integration tests"""
    print("🚀 Running Hotel Controller Integration Tests...")
    print("=" * 50)
    
    # Set environment variables for testing
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'test_hotel_controller_integration.py',
            '-v', '-s', '--tb=short'
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

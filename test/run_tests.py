#!/usr/bin/env python3
"""
Comprehensive test runner for Discord bots.

This script runs all tests for the Discord bot collection and provides
detailed reporting on test results, coverage, and performance.
"""

import os
import sys
import pytest
import time
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_suite():
    """Run the complete test suite for all Discord bots"""
    print("🤖 Discord Bots Test Suite")
    print("=" * 50)
    
    start_time = time.time()
    
    # Test configuration
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker handling
        "--durations=10",  # Show 10 slowest tests
        "-x",  # Stop on first failure (optional, remove for full run)
    ]
    
    # Add coverage if available
    try:
        import coverage
        test_args.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:test_reports/coverage_html",
            "--cov-fail-under=70"  # Require 70% coverage
        ])
        print("📊 Coverage reporting enabled")
    except ImportError:
        print("⚠️  Coverage not available (install pytest-cov for coverage reports)")
    
    # Create test reports directory
    reports_dir = Path(__file__).parent / "test_reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Add JUnit XML report for CI/CD
    test_args.extend([
        f"--junitxml={reports_dir}/junit.xml"
    ])
    
    print(f"📂 Test reports will be saved to: {reports_dir}")
    print("\n🚀 Starting tests...\n")
    
    # Run the tests
    test_directory = Path(__file__).parent
    exit_code = pytest.main(test_args + [str(test_directory)])
    
    # Calculate test duration
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"⏱️  Total test duration: {duration:.2f} seconds")
    
    # Test result summary
    if exit_code == 0:
        print("✅ All tests passed!")
        print("🎉 Your Discord bots are ready to deploy!")
    else:
        print("❌ Some tests failed!")
        print("🔧 Please review the test output and fix the issues.")
    
    print(f"\n📋 Test reports available in: {reports_dir}")
    
    return exit_code

def run_specific_bot_tests(bot_name):
    """Run tests for a specific bot"""
    print(f"🎯 Running tests for {bot_name} bot...")
    
    test_file = Path(__file__).parent / f"test_{bot_name}_bot.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    exit_code = pytest.main(["-v", str(test_file)])
    
    if exit_code == 0:
        print(f"✅ {bot_name} bot tests passed!")
    else:
        print(f"❌ {bot_name} bot tests failed!")
    
    return exit_code

def check_test_dependencies():
    """Check if required test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-mock"
    ]
    
    optional_packages = [
        "pytest-cov",
        "pytest-html",
        "pytest-xdist"
    ]
    
    print("🔍 Checking test dependencies...")
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} (required)")
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Install with: pip install " + " ".join(missing_optional))
    
    print("\n✅ Dependencies check complete!")
    return True

def setup_test_environment():
    """Set up the test environment"""
    print("🔧 Setting up test environment...")
    
    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "DISCORD_TOKEN": "test_token",
        "NOTION_TOKEN": "test_notion_token",
        "OPENROUTER_API_KEY": "test_openrouter_key",
        "TODOIST_API_KEY": "test_todoist_key",
    }
    
    for key, value in test_env.items():
        os.environ.setdefault(key, value)
    
    print("✅ Test environment configured!")

def list_available_tests():
    """List all available test files"""
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    
    print("📋 Available test files:")
    for test_file in test_files:
        bot_name = test_file.stem.replace("test_", "").replace("_bot", "")
        print(f"  • {bot_name} bot ({test_file.name})")

def main():
    """Main entry point for the test runner"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            return 0 if check_test_dependencies() else 1
        elif command == "list":
            list_available_tests()
            return 0
        elif command == "setup":
            setup_test_environment()
            return 0
        elif command.startswith("bot:"):
            bot_name = command.split(":", 1)[1]
            return run_specific_bot_tests(bot_name)
        else:
            print(f"Unknown command: {command}")
            print("Available commands: check, list, setup, bot:<name>")
            return 1
    
    # Check dependencies first
    if not check_test_dependencies():
        return 1
    
    # Set up test environment
    setup_test_environment()
    
    # Run full test suite
    return run_test_suite()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
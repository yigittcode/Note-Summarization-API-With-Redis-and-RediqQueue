#!/usr/bin/env python3
"""
Simple test runner script that can run tests either in Docker or locally.
This ensures tests are isolated and don't affect the production database.
"""

import sys
import subprocess
import os


def run_tests_docker():
    """Run tests using Docker compose."""
    print("🐳 Running tests in Docker...")
    try:
        result = subprocess.run([
            "docker", "compose", "--profile", "test", "run", "--rm", "test"
        ], check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker or run tests locally.")
        return 1
    except Exception as e:
        print(f"❌ Error running tests in Docker: {e}")
        return 1


def run_tests_local():
    """Run tests locally (requires dependencies installed)."""
    print("🏠 Running tests locally...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v"
        ], check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running tests locally: {e}")
        return 1


def main():
    """Main test runner."""
    print("🧪 AI Summarizer API Test Runner")
    print("==================================")

    # Set test environment variables
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

    # Try Docker first, fallback to local
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        return run_tests_local()

    print("Attempting to run tests in Docker...")
    docker_result = run_tests_docker()

    if docker_result != 0:
        print("Docker tests failed or Docker unavailable. Trying local...")
        return run_tests_local()

    return docker_result


if __name__ == "__main__":
    sys.exit(main())
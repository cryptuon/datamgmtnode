#!/usr/bin/env python3
"""Build script for Vue.js dashboard.

This script builds the Vue.js dashboard and copies the output
to the Python package's static directory.

Usage:
    python scripts/build_dashboard.py
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    """Build the Vue.js dashboard."""
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    web_dir = project_root / 'web'
    static_dir = project_root / 'datamgmtnode' / 'dashboard' / 'static'

    print("=" * 60)
    print("DataMgmt Node Dashboard Builder")
    print("=" * 60)

    # Check if web directory exists
    if not web_dir.exists():
        print(f"Error: Web directory not found at {web_dir}")
        sys.exit(1)

    # Check if npm is available
    try:
        subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: npm is not installed or not in PATH")
        print("Please install Node.js and npm first.")
        sys.exit(1)

    # Check if package.json exists
    if not (web_dir / 'package.json').exists():
        print(f"Error: package.json not found in {web_dir}")
        sys.exit(1)

    # Install dependencies
    print("\n[1/3] Installing npm dependencies...")
    try:
        subprocess.run(
            ['npm', 'install'],
            cwd=web_dir,
            check=True
        )
        print("      Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

    # Build the Vue.js app
    print("\n[2/3] Building Vue.js application...")
    try:
        subprocess.run(
            ['npm', 'run', 'build'],
            cwd=web_dir,
            check=True
        )
        print("      Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error building application: {e}")
        sys.exit(1)

    # Copy dist to static directory
    print("\n[3/3] Copying build output to static directory...")
    dist_dir = web_dir / 'dist'

    if not dist_dir.exists():
        print(f"Error: Build output not found at {dist_dir}")
        sys.exit(1)

    # Remove existing static directory
    if static_dir.exists():
        shutil.rmtree(static_dir)
        print(f"      Removed existing static directory.")

    # Copy dist to static
    shutil.copytree(dist_dir, static_dir)
    print(f"      Copied build output to {static_dir}")

    # Print summary
    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    print(f"\nDashboard files are now available at:")
    print(f"  {static_dir}")
    print("\nTo serve the dashboard, start the node:")
    print("  poetry run python -m datamgmtnode.main")
    print("\nThen visit: http://localhost:8082")
    print()


if __name__ == '__main__':
    main()

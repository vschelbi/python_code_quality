#!/usr/bin/env python

"""
Setup script for MyPy with dynamic pydantic plugin detection.
Similar to setup_pylint.py, this script chooses the appropriate mypy configuration
based on whether pydantic is available.
"""

import subprocess
import sys
from pathlib import Path


def _pydantic_is_available() -> bool:
    """Check if pydantic is available for import."""
    try:
        import pydantic  # pylint: disable=unused-import,import-outside-toplevel # noqa: F401

        return True
    except ImportError:
        return False


def main() -> int:
    """Run mypy with the appropriate configuration."""
    if len(sys.argv) < 2:
        print("Usage: setup_mypy.py <file1> [file2] ...", file=sys.stderr)
        return 1

    # Determine the script's directory (where config files are located)
    script_dir = Path(__file__).parent.absolute()

    # Choose config file based on pydantic availability
    if _pydantic_is_available():
        config_file = script_dir / "mypy-pydantic.ini"
    else:
        config_file = script_dir / "mypy.ini"

    # Run mypy with the chosen config file
    try:
        cmd = ["mypy", f"--config-file={config_file}"] + sys.argv[1:]
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: mypy not found. Please install mypy first.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

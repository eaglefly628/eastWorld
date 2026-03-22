#!/usr/bin/env python3
"""Launch EastWorld server.

Usage: python run.py
Dependencies are auto-installed on first run.
"""

import subprocess
import sys


def ensure_deps():
    """Auto-install dependencies if missing."""
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import websockets  # noqa: F401
        import pydantic  # noqa: F401
    except ImportError:
        print("  📦  First run — installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q",
            "fastapi", "uvicorn[standard]", "websockets", "pydantic",
        ])
        print("  ✅  Done!\n")


if __name__ == "__main__":
    ensure_deps()
    import uvicorn
    print("\n  🤠  EastWorld is starting...")
    print("  📍  Open http://localhost:8000 in your browser\n")
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)

#!/usr/bin/env python3
"""Launch EastWorld server."""

import os
import sys

# Load vendored dependencies (no pip install needed)
_vendor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(_vendor):
    sys.path.insert(0, _vendor)

import uvicorn

if __name__ == "__main__":
    print("\n  🤠  EastWorld is starting...")
    print("  📍  Open http://localhost:8000 in your browser\n")
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)

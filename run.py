#!/usr/bin/env python3
"""Launch EastWorld server."""

import uvicorn

if __name__ == "__main__":
    print("\n  🤠  EastWorld is starting...")
    print("  📍  Open http://localhost:8000 in your browser\n")
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)

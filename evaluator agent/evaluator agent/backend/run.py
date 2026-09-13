#!/usr/bin/env python
"""Run Evaluator Agent with correct imports."""

import sys
from pathlib import Path

# Add current directory to path so relative imports work
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from server import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)

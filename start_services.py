#!/usr/bin/env python
"""Start all five backend services using subprocess."""

import subprocess
import sys
import time
import os
from pathlib import Path

# Get root directory
root_dir = Path(__file__).parent
venv_python = root_dir / ".venv" / "Scripts" / "python.exe"

if not venv_python.exists():
    print(f"ERROR: venv python not found at {venv_python}")
    sys.exit(1)

services = [
    {
        "name": "Risk Detector",
        "port": 8003,
        "cwd": root_dir / "Risk Agent" / "Risk Agent" / "backend",
        "cmd": [str(venv_python), "main.py"],
    },
    {
        "name": "Pitch Evaluator",
        "port": 8001,
        "cwd": root_dir / "Pitch Evaluator Agent" / "Pitch Evaluator Agent",
        "cmd": [str(venv_python), "-m", "uvicorn", "pitch_evaluator.api:app", "--host", "0.0.0.0", "--port", "8001"],
    },
    {
        "name": "PS Finder",
        "port": 8002,
        "cwd": root_dir / "PS Finder",
        "cmd": [str(venv_python), "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"],
    },
    {
        "name": "Orchestrator",
        "port": 8000,
        "cwd": root_dir / "orchestrator",
        "cmd": [str(venv_python), "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"],
    },
    {
        "name": "Evaluator Agent",
        "port": 8004,
        "cwd": root_dir / "evaluator agent" / "evaluator agent" / "backend",
        "cmd": [str(venv_python), "server.py"],
    },
]

processes = []

print("Starting all services...")
print("-" * 60)

for service in services:
    print(f"Starting {service['name']} on port {service['port']}...")
    try:
        proc = subprocess.Popen(
            service["cmd"],
            cwd=service["cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        processes.append({"name": service["name"], "port": service["port"], "process": proc})
        time.sleep(1)
    except Exception as e:
        print(f"ERROR starting {service['name']}: {e}")

print("-" * 60)
print("\nAll services started!")
print("\nService URLs:")
print("  Orchestrator:     http://localhost:8000")
print("  Pitch Evaluator:  http://localhost:8001")
print("  PS Finder:        http://localhost:8002")
print("  Risk Detector:    http://localhost:8003")
print("  Evaluator Agent:  http://localhost:8004")
print("\nPress Ctrl+C to stop all services.")
print("-" * 60)

try:
    while True:
        time.sleep(1)
        # Check if any process died
        for proc_info in processes:
            if proc_info["process"].poll() is not None:
                print(f"\n⚠️  {proc_info['name']} (port {proc_info['port']}) exited with code {proc_info['process'].returncode}")
except KeyboardInterrupt:
    print("\n\nStopping all services...")
    for proc_info in processes:
        try:
            proc_info["process"].terminate()
            proc_info["process"].wait(timeout=5)
        except:
            proc_info["process"].kill()
    print("All services stopped.")

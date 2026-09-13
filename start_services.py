#!/usr/bin/env python
"""Start all services with proper sys.path configuration."""

import subprocess
import sys
import time
import os
from pathlib import Path

root_dir = Path(__file__).parent.resolve()
venv_python = root_dir / ".venv" / "Scripts" / "python.exe"

if not venv_python.exists():
    print("FAIL: venv python not found")
    sys.exit(1)

SERVICES = [
    {
        "name": "Orchestrator",
        "port": 8000,
        "cwd": root_dir,
        "cmd": [str(venv_python), "-m", "uvicorn", "orchestrator.server:app", "--host", "0.0.0.0", "--port", "8000"],
    },
    {
        "name": "Pitch Evaluator",
        "port": 8001,
        "cwd": root_dir / "Pitch Evaluator Agent" / "Pitch Evaluator Agent",
        "cmd": [str(venv_python), "-c", "import sys; sys.path.insert(0, " + repr(str(root_dir)) + "); from pitch_evaluator.api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8001)"],
    },
    {
        "name": "PS Finder",
        "port": 8002,
        "cwd": root_dir / "PS Finder",
        "cmd": [str(venv_python), "-c", "import sys; sys.path.insert(0, " + repr(str(root_dir)) + "); from src.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8002)"],
    },
    {
        "name": "Risk Detector",
        "port": 8003,
        "cwd": root_dir / "Risk Agent" / "Risk Agent" / "backend",
        "cmd": [str(venv_python), "-c", "import sys; sys.path.insert(0, " + repr(str(root_dir)) + "); exec(open('main.py').read())"],
    },
    {
        "name": "Evaluator Agent",
        "port": 8004,
        "cwd": root_dir / "evaluator agent" / "evaluator agent" / "backend",
        "cmd": [str(venv_python), "run.py"],
    },
]

processes = []

print("=" * 80)
print("STARTING ALL SERVICES WITH ROOT PYTHONPATH")
print("=" * 80)
print()

env = os.environ.copy()
env["PYTHONPATH"] = str(root_dir)

for service in SERVICES:
    print("Starting " + service["name"] + "...", end="", flush=True)
    try:
        proc = subprocess.Popen(
            service["cmd"],
            cwd=service["cwd"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append({"name": service["name"], "port": service["port"], "process": proc})
        print(" started (PID " + str(proc.pid) + ")")
        time.sleep(1)
    except Exception as e:
        print(" FAILED: " + str(e))

print()
print("Waiting 10 seconds for initialization...")
time.sleep(10)

print()
print("=" * 80)
print("SERVICE STATUS")
print("=" * 80)

alive_count = 0
for proc_info in processes:
    poll = proc_info["process"].poll()
    alive = poll is None
    status = "[ALIVE]" if alive else "[EXIT " + str(poll) + "]"
    print(status + " " + proc_info["name"].ljust(20) + " port " + str(proc_info["port"]))
    if alive:
        alive_count += 1

print()
print("Alive: " + str(alive_count) + "/" + str(len(processes)))
print()

if alive_count == 0:
    print("ERROR: No services running.")
    for proc_info in processes:
        print("\n" + proc_info["name"] + " stderr:")
        try:
            proc_info["process"].wait(timeout=0.1)
        except:
            pass
        if proc_info["process"].stderr:
            lines = proc_info["process"].stderr.readlines()
            for line in lines[-10:]:
                print("  " + line.rstrip())
    sys.exit(1)

print("Services running. Press Ctrl+C to stop.")
print("=" * 80)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nStopping...")
    for proc_info in processes:
        try:
            proc_info["process"].terminate()
            proc_info["process"].wait(timeout=2)
        except:
            try:
                proc_info["process"].kill()
            except:
                pass
    print("Done.")

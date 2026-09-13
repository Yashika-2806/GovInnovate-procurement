#!/usr/bin/env python
"""Simple direct service starter for testing."""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

root = Path(__file__).parent.resolve()
venv_python = root / ".venv" / "Scripts" / "python.exe"

if not venv_python.exists():
    print(f"ERROR: No venv python at {venv_python}")
    sys.exit(1)

print("=" * 80)
print("GOVINNOVATE SERVICES LAUNCHER")
print("=" * 80)
print()

services = []

# Orchestrator on 8000
print("[1/5] Starting Orchestrator (8000)...")
env = os.environ.copy()
env["PYTHONPATH"] = str(root)
p1 = subprocess.Popen(
    [str(venv_python), "-m", "uvicorn", "orchestrator.server:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=str(root),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
services.append(("Orchestrator", p1))
time.sleep(2)

# Pitch Evaluator on 8001
print("[2/5] Starting Pitch Evaluator (8001)...")
p2 = subprocess.Popen(
    [str(venv_python), "-c", """
import sys
sys.path.insert(0, '.')
import os
os.chdir('Pitch Evaluator Agent/Pitch Evaluator Agent')
from pitch_evaluator.api import create_app
from pitch_evaluator.service import PitchEvaluator
app = create_app(PitchEvaluator())
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='critical')
"""],
    cwd=str(root),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
services.append(("Pitch Evaluator", p2))
time.sleep(2)

# PS Finder on 8002
print("[3/5] Starting PS Finder (8002)...")
p3 = subprocess.Popen(
    [str(venv_python), "-m", "uvicorn", "PS Finder.src.main:app", "--host", "0.0.0.0", "--port", "8002"],
    cwd=str(root),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
services.append(("PS Finder", p3))
time.sleep(2)

# Risk Detector on 8003 - requires GEMINI_API_KEY
print("[4/5] Starting Risk Detector (8003)...")
risk_env = env.copy()
risk_env["PYTHONPATH"] = str(root / "risk_backend")
# Load .env if it exists
risk_env_file = root / "risk_backend" / ".env"
if risk_env_file.exists():
    import dotenv
    dotenv.load_dotenv(risk_env_file)
p4 = subprocess.Popen(
    [str(venv_python), "-c", """
import sys, os
sys.path.insert(0, '.')
os.chdir('risk_backend')
from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8003, log_level='critical')
"""],
    cwd=str(root),
    env=risk_env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
services.append(("Risk Detector", p4))
time.sleep(2)

# Evaluator on 8004
print("[5/5] Starting Evaluator (8004)...")
p5 = subprocess.Popen(
    [str(venv_python), "-c", """
import sys
sys.path.insert(0, '.')
from backend.server import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8004, log_level='critical')
"""],
    cwd=str(root / "evaluator agent" / "evaluator agent" / "backend"),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
services.append(("Evaluator", p5))
time.sleep(2)

print()
print("=" * 80)
print("Verifying services...")
print("=" * 80)

import httpx

healthy = 0
for name, port in [("Orchestrator", 8000), ("Pitch Evaluator", 8001), ("PS Finder", 8002), ("Risk Detector", 8003), ("Evaluator", 8004)]:
    try:
        r = httpx.get(f"http://localhost:{port}/", timeout=2)
        print(f"[OK] {name:20} port {port} - HTTP {r.status_code}")
        healthy += 1
    except:
        print(f"[  ] {name:20} port {port} - unreachable")

print()
print(f"Services ready: {healthy}/5")
print()
print("Press Ctrl+C to stop all services.")
print("=" * 80)

def cleanup(*args):
    print("\nStopping services...")
    for name, proc in services:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()

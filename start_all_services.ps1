# Start all five services in separate Windows terminal windows
# Each service uses the root .venv

$rootPath = Get-Location
$pythonExe = "$rootPath\.venv\Scripts\python.exe"

# 1. Pitch Evaluator (8001)
Write-Host "Starting Pitch Evaluator Agent on port 8001..."
$pitchEvalPath = "$rootPath\Pitch Evaluator Agent\Pitch Evaluator Agent"
Start-Process cmd -ArgumentList "/c", "cd `"$pitchEvalPath`" && `"$pythonExe`" -m uvicorn pitch_evaluator.api:app --host 0.0.0.0 --port 8001"

Start-Sleep -Seconds 2

# 2. PS Finder (8002)
Write-Host "Starting PS Finder (Problem Collector) on port 8002..."
$psFinderPath = "$rootPath\PS Finder"
Start-Process cmd -ArgumentList "/c", "cd `"$psFinderPath`" && `"$pythonExe`" -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload"

Start-Sleep -Seconds 2

# 3. Risk Detector (8003)
Write-Host "Starting Risk Detector Agent on port 8003..."
$riskPath = "$rootPath\Risk Agent\Risk Agent\backend"
Start-Process cmd -ArgumentList "/c", "cd `"$riskPath`" && `"$pythonExe`" main.py"

Start-Sleep -Seconds 2

# 4. Evaluator Agent (8004)
Write-Host "Starting Evaluator Agent on port 8004..."
$evaluatorPath = "$rootPath\evaluator agent\evaluator agent\backend"
Start-Process cmd -ArgumentList "/c", "cd `"$evaluatorPath`" && `"$pythonExe`" server.py"

Start-Sleep -Seconds 2

# 5. Orchestrator (8000) - starts last so adapters are ready
Write-Host "Starting Orchestrator on port 8000..."
$orchestratorPath = "$rootPath\orchestrator"
Start-Process cmd -ArgumentList "/c", "cd `"$orchestratorPath`" && `"$pythonExe`" -m uvicorn server:app --host 0.0.0.0 --port 8000"

Write-Host "All services started!"
Write-Host "Orchestrator: http://localhost:8000"
Write-Host "Pitch Evaluator: http://localhost:8001"
Write-Host "PS Finder: http://localhost:8002"
Write-Host "Risk Detector: http://localhost:8003"
Write-Host "Evaluator: http://localhost:8004"

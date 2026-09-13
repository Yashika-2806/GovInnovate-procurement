# Start all five services from ROOT directory with PYTHONPATH set
# Windows PowerShell version

$rootPath = (Get-Location).Path
$pythonExe = Join-Path $rootPath ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python not found at $pythonExe"
    exit 1
}

Write-Host "=========================================="
Write-Host "Starting all services from ROOT directory"
Write-Host "=========================================="
Write-Host "Root: $rootPath"
Write-Host "Python: $pythonExe"
Write-Host "PYTHONPATH: $rootPath"
Write-Host ""

# Prepare environment
$env:PYTHONPATH = $rootPath

# Service configurations: name, port, working_directory, command
$services = @(
    @{
        name = "Orchestrator"
        port = 8000
        cwd = $rootPath
        args = @("-m", "uvicorn", "orchestrator.server:app", "--host", "0.0.0.0", "--port", "8000")
    },
    @{
        name = "Pitch Evaluator"
        port = 8001
        cwd = Join-Path $rootPath "Pitch Evaluator Agent\Pitch Evaluator Agent"
        args = @("-m", "uvicorn", "pitch_evaluator.api:app", "--host", "0.0.0.0", "--port", "8001")
    },
    @{
        name = "PS Finder"
        port = 8002
        cwd = Join-Path $rootPath "PS Finder"
        args = @("-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002")
    },
    @{
        name = "Risk Detector"
        port = 8003
        cwd = Join-Path $rootPath "Risk Agent\Risk Agent\backend"
        args = @("main.py")
    },
    @{
        name = "Evaluator Agent"
        port = 8004
        cwd = Join-Path $rootPath "evaluator agent\evaluator agent\backend"
        args = @("server.py")
    }
)

$processes = @()

foreach ($service in $services) {
    Write-Host "Starting $($service.name) on port $($service.port)"
    Write-Host "  CWD: $($service.cwd)"

    try {
        $proc = Start-Process -FilePath $pythonExe `
                              -ArgumentList $service.args `
                              -WorkingDirectory $service.cwd `
                              -PassThru `
                              -NoNewWindow

        $processes += @{
            name = $service.name
            port = $service.port
            process = $proc
        }

        Write-Host "  [STARTED] PID $($proc.Id)"
        Start-Sleep -Milliseconds 500
    }
    catch {
        Write-Host "  [FAILED] $_"
    }
}

Write-Host ""
Write-Host "Waiting 3 seconds for initialization..."
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=========================================="
Write-Host "SERVICE STATUS"
Write-Host "=========================================="

$alive = 0
foreach ($proc_info in $processes) {
    if ($proc_info.process.HasExited) {
        Write-Host "[EXITED] $($proc_info.name) port $($proc_info.port)"
    }
    else {
        Write-Host "[ALIVE] $($proc_info.name) port $($proc_info.port)"
        $alive++
    }
}

Write-Host ""
Write-Host "Alive: $alive/$($processes.Count)"
Write-Host ""
Write-Host "Service URLs:"
Write-Host "  Orchestrator:     http://localhost:8000"
Write-Host "  Pitch Evaluator:  http://localhost:8001"
Write-Host "  PS Finder:        http://localhost:8002"
Write-Host "  Risk Detector:    http://localhost:8003"
Write-Host "  Evaluator Agent:  http://localhost:8004"
Write-Host ""
Write-Host "Press Ctrl+C to stop all services."
Write-Host "=========================================="

try {
    while ($true) {
        Start-Sleep -Seconds 1

        foreach ($proc_info in $processes) {
            if ($proc_info.process.HasExited) {
                Write-Host "WARNING: $($proc_info.name) exited"
            }
        }
    }
}
finally {
    Write-Host ""
    Write-Host "Stopping all services..."

    foreach ($proc_info in $processes) {
        if (-not $proc_info.process.HasExited) {
            try {
                Stop-Process -InputObject $proc_info.process -Force -ErrorAction SilentlyContinue
            }
            catch {
                # Already stopped
            }
        }
    }

    Write-Host "All services stopped."
}

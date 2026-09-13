# GovInnovate Procurement — SIH 2026 Prototype

**Problem Statement**: Enable government departments to identify, pilot, procure, and scale innovative solutions from eligible start-ups.

## Architecture

### Five Services, Four AI Agents

| Service | Port | Type | Role |
|---------|------|------|------|
| **Orchestrator** | 8000 | Deterministic State Machine | Workflow coordination, API gateway, adapter dispatcher |
| **Pitch Evaluator** | 8001 | LLM/Mock Agent | Multimodal startup pitch analysis with criterion scores |
| **PS Finder** | 8002 | LangGraph Agent | Discovery and verification of genuine public-sector opportunities |
| **Risk Detector** | 8003 | LangGraph Agent | Comprehensive startup risk analysis with comparable evidence |
| **Evaluator** | 8004 | LangGraph Agent | Execution evaluation, milestone assessment, scale recommendation |
| **Frontend** | 3000 | React App | User interface for workflow management |

**Key Design**: The Orchestrator is NOT an AI agent. It is a deterministic finite state machine that:
- Manages workflow state transitions
- Routes requests to the four AI agents via HTTP adapters
- Persists workflow context to SQLite
- Maintains audit trail
- Enforces human gates for critical decisions
- Never fabricates AI results; fails clearly on unavailable services

### The Four AI Agents

**1. Problem Statement Collector / PS Finder**
- Discovers verified, public-sector opportunities
- Preserves source provenance, URL, retrieval timestamp
- Uses configured external sources (e.g., government RFP portals)
- LangGraph-powered discovery graph

**2. Pitch Evaluator**
- Accepts structured startup pitches (multimodal)
- Returns deterministic weighted criterion scores
- Scores are NOT probabilities; they measure criterion compliance
- Evidence provided where supported

**3. Risk Detector**
- Analyzes startup and problem context
- Identifies risk categories (market, technical, regulatory, competitive, organizational)
- Provides evidence/comparable patterns where available
- Distinguishes evidence from inference
- Never predicts "failure probability"

**4. Evaluator Agent**
- Evaluates execution against milestones
- Assesses evidence collection and KPI performance
- Makes PASS/FAIL/REMEDIATION recommendations
- Computes scale/procurement recommendation

## Workflow States

```
OPPORTUNITY_DISCOVERED
    ↓
PITCH_SUBMITTED
    ↓
PITCH_EVALUATED (via PitchEvaluatorAdapter @ 8001)
    ↓
RISK_ASSESSED (via RiskDetectorAdapter @ 8003)
    ↓
AWAITING_HUMAN_REVIEW (human gate: APPROVE/REJECT)
    ↓
STARTUP_SELECTED (startup ID set)
    ↓
PROBLEM_ALLOCATED (pilot created)
    ↓
PILOT_CREATED
    ↓
MILESTONE_TRACKED
    ↓
EVIDENCE_COLLECTED
    ↓
MILESTONE_EVALUATED
    ↓
FINAL_EVALUATION (via EvaluatorAdapter @ 8004)
    ↓
PERFORMANCE_UPDATED
    ↓
SCALE_RECOMMENDATION
    ↓
AWAITING_FINAL_DECISION (human gate: APPROVE/REJECT)
    ↓
COMPLETED
```

All transitions are deterministic. Invalid transitions return HTTP 409 Conflict.

## Setup

### Prerequisites
- **Python**: 3.12
- **Platform**: Windows (tested), Linux/macOS support via path translation
- **Database**: SQLite (`procurement.db`)

### Installation

```bash
# Create venv (one shared root venv for all services)
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify
pip check
```

### Environment Variables

Create `.env` files as needed for API keys. Do NOT commit.

```
# risk_backend/.env
GEMINI_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here

# PS Finder/src/.env (if needed)
OPTIONAL_EXTERNAL_SOURCE_KEY=...
```

## Running Services

### Quick Start

```bash
# All services (Windows)
.venv\Scripts\python.exe start.py

# Or use PowerShell startup script
.\start_all_services.ps1
```

This starts:
- Orchestrator on 8000
- Pitch Evaluator on 8001
- PS Finder on 8002
- Risk Detector on 8003
- Evaluator on 8004

### Manual Startup (Advanced)

Always set `PYTHONPATH` and run from repository root:

```bash
# Orchestrator
set PYTHONPATH=.
.venv\Scripts\python.exe -m uvicorn orchestrator.server:app --host 0.0.0.0 --port 8000

# Pitch Evaluator (from root)
.venv\Scripts\python.exe -c "
import sys; sys.path.insert(0, '.')
import os; os.chdir('Pitch Evaluator Agent/Pitch Evaluator Agent')
from pitch_evaluator.api import create_app
from pitch_evaluator.service import PitchEvaluator
app = create_app(PitchEvaluator())
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8001)
"

# PS Finder (from root)
.venv\Scripts\python.exe -m uvicorn PS\ Finder.src.main:app --host 0.0.0.0 --port 8002

# Risk Detector (requires Gemini API key; see .env setup)
cd risk_backend
.venv\Scripts\python.exe main.py

# Evaluator (from evaluator agent backend)
.venv\Scripts\python.exe run.py
```

## API Workflow

### 1. Create Workflow

```bash
POST /api/workflows
{
  "id": "opp-123",
  "title": "Energy Infrastructure Pilot",
  "description": "Renewable energy solution procurement",
  "organization": "Ministry of Energy",
  "status": "active"
}

Response:
{
  "workflow_id": "wf-abc123",
  "state": "OPPORTUNITY_DISCOVERED"
}
```

### 2. Submit Pitch

```bash
POST /api/workflows/{workflow_id}/pitch
{
  "id": "pitch-1",
  "startup_id": "startup-123",
  "opportunity_id": "opp-123",
  "metadata": {...}
}

Response:
{
  "status": "pitch_submitted"
}
```

### 3. Evaluate Pitch

```bash
POST /api/workflows/{workflow_id}/pitch/evaluate

Response (if service available):
{
  "status": "pitch_evaluated",
  "adapter_called": "PitchEvaluatorAdapter",
  "service_target": "localhost:8001"
}

Response (if service unavailable):
{
  "detail": "PitchEvaluator service unavailable at localhost:8001 (...). 
             No AI result fabricated. Workflow state preserved."
}
```

### 4. Assess Risk

```bash
POST /api/workflows/{workflow_id}/risk/assess

Response:
{
  "status": "risk_assessed",
  "adapter_called": "RiskDetectorAdapter",
  "service_target": "localhost:8003"
}
```

### 5. Human Review Gate

```bash
POST /api/workflows/{workflow_id}/human-review
{
  "decision": "APPROVE"  # or "REJECT"
}
```

Transitions to `AWAITING_HUMAN_REVIEW` (APPROVE) or `FAILED` (REJECT).

### 6. Select Startup

```bash
POST /api/workflows/{workflow_id}/startup-selection
{
  "startup_id": "startup-123",
  "justification": "Best technical fit"
}
```

### 7. Create Pilot

```bash
POST /api/workflows/{workflow_id}/pilot
{
  "pilot_id": "pilot-1",
  "startup_id": "startup-123",
  "start_date": "2026-01-01",
  "end_date": "2026-06-01"
}
```

### 8. Track Milestones

```bash
POST /api/workflows/{workflow_id}/milestones
{
  "milestone_id": "m1",
  "title": "Phase 1 Prototype",
  "target_date": "2026-02-01",
  "kpis": ["feature_completion", "stability_test"]
}

GET /api/workflows/{workflow_id}/milestones
GET /api/workflows/{workflow_id}/milestones/{milestone_id}
```

### 9. Submit Evidence

```bash
POST /api/workflows/{workflow_id}/milestones/{milestone_id}/evidence
{
  "evidence_id": "ev-1",
  "type": "document",
  "source_url": "https://...",
  "provenance": "Verified by: ...",
  "timestamp": "2026-02-15T10:30:00Z"
}

GET /api/workflows/{workflow_id}/milestones/{milestone_id}/evidence
```

### 10. Evaluate Milestone

```bash
POST /api/workflows/{workflow_id}/milestones/{milestone_id}/evaluate

Response:
{
  "status": "milestone_evaluated_pass",
  "result": "PASS",  # or "FAIL"
  "milestone_id": "m1"
}
```

### 11. Final Evaluation

```bash
POST /api/workflows/{workflow_id}/final-evaluation
{
  "evaluation_result": {...}
}

Response:
{
  "status": "final_evaluation_complete",
  "adapter_called": "EvaluatorAdapter",
  "service_target": "localhost:8004",
  "human_decision_remains_required": true
}
```

### 12. Scale Recommendation

```bash
POST /api/workflows/{workflow_id}/scale-recommendation
{
  "recommendation": "SCALE",  # or "PILOT_EXTENSION", "REJECT"
  "justification": "Met all KPIs"
}
```

### 13. Final Decision (Human Gate)

```bash
POST /api/workflows/{workflow_id}/final-decision
{
  "decision": "APPROVE"  # or "REJECT"
}

→ Transitions to COMPLETED
```

### Get Workflow & Audit Trail

```bash
GET /api/workflows/{workflow_id}
{
  "workflow_id": "...",
  "state": "...",
  "context": {...}
}

GET /api/workflows/{workflow_id}/audit
[
  {"timestamp": "...", "event": "...", "agent": "...", ...},
  ...
]
```

## Database

SQLite database (`procurement.db`) auto-created on startup.

**Schema**:
- `workflows` table: workflow_id, state, context (JSON)
- All state persisted with nested milestone/evidence/pilot data
- Audit trail embedded in context["history"]

**Reload after restart**:
```bash
GET /api/workflows/{workflow_id}
```

Full state persists including:
- Current milestone tracking
- Evidence collection
- Performance metrics
- Audit events

## Frontend

React application on port 3000.

```bash
cd frontend
npm install
npm run dev
```

Communicates with Orchestrator API on `http://localhost:8000/api`.

## Testing

### Integration Test

```bash
.venv\Scripts\python.exe test_integration.py
```

Tests all five service endpoints and basic workflow transitions.

### Unit Tests

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

## Critical Design Decisions

### 1. **No Fabricated AI Results**

If any agent service is unavailable:
- The HTTP adapter fails with 503 Service Unavailable
- The workflow state is preserved (NO transition)
- An audit entry records the attempt and failure
- The response clearly states no AI result was fabricated

Example:
```json
{
  "detail": "PitchEvaluator service unavailable at localhost:8001 (...). 
             No AI result fabricated. Workflow state preserved at PITCH_SUBMITTED."
}
```

### 2. **Human Gates Are Mandatory**

- Startup selection (after risk assessment)
- Final procurement decision (after evaluation)

AI agents provide analysis and recommendation. Humans make the approval/rejection decision.

### 3. **Provenance and Audit Trail**

- Every operation recorded with timestamp, agent, status
- Evidence includes source URL, retrieval timestamp, verification status
- No backdating or manual state manipulation in production

### 4. **Deterministic Orchestrator**

- All transitions defined in `orchestrator/state.py`
- Invalid transitions return 409 Conflict
- No probabilistic or non-deterministic state logic

### 5. **One Shared Virtual Environment**

All five services use `.venv` at repository root.

No per-service venvs. No duplicate dependency files. One `requirements.txt`.

## Architecture Diagrams

### Data Flow

```
FRONTEND (React, port 3000)
    ↓
ORCHESTRATOR (port 8000)
    ├─→ ProblemCollectorAdapter → PS Finder (8002)
    ├─→ PitchEvaluatorAdapter → Pitch Evaluator (8001)
    ├─→ RiskDetectorAdapter → Risk Detector (8003)
    ├─→ EvaluatorAdapter → Evaluator (8004)
    ↓
SQLITE (procurement.db)
```

### Service Internals

**Orchestrator**:
- FastAPI application
- State machine (orchestrator/state.py)
- Adapters (adapters/*.py)
- Database persistence (orchestrator/persistence.py)

**PS Finder**:
- FastAPI + LangGraph
- Discovery graph, explain graph, monitoring graph
- SQLite repository with versioning
- Supports real external sources (configured)

**Pitch Evaluator**:
- FastAPI
- Mock or LLM engine (selectable)
- Criterion-based scoring
- Multimodal document analysis

**Risk Detector**:
- FastAPI + LangGraph
- Background async analysis
- Requires Gemini API key
- Returns structured risk report

**Evaluator**:
- FastAPI + LangGraph
- Thread-checkpointed execution graph
- Exports Markdown reports
- Performance tracking

## Known Limitations

1. **Risk Detector**: Requires Google Gemini API key. Without it, the service can be stubbed for demo.
2. **External Sources**: PS Finder is configured for demo data; real government API integration requires authentication.
3. **Frontend**: Basic read-only demo UI. Production would need permissions UX, evidence upload, etc.
4. **Scale**: SQLite for dev/demo. Production requires PostgreSQL + pgvector for RAG.

## Troubleshooting

### "ModuleNotFoundError: No module named 'orchestrator'"

**Cause**: PYTHONPATH not set or running from wrong directory.

**Fix**: Always run from repository root with PYTHONPATH=.

```bash
set PYTHONPATH=.
.venv\Scripts\python.exe -m uvicorn orchestrator.server:app
```

### "ConnectionError: Cannot connect to localhost:8001"

**Cause**: Pitch Evaluator service not running on port 8001.

**Fix**: Start all services with `start.py` or manually start each service.

### "Workflow state validation failed"

**Cause**: Invalid state transition attempted.

**Fix**: Check orchestrator/state.py for valid transitions. Return 409 is correct; adjust client logic.

### "Service unavailable at localhost:8003"

**Cause**: Risk Detector service is down or missing Gemini API key.

**Fix**: Start Risk Detector service; set GEMINI_API_KEY in risk_backend/.env

## Development

### Code Structure

```
.
├── orchestrator/           # Deterministic state machine & API
│   ├── server.py          # FastAPI app & routes
│   ├── state.py           # State machine definition
│   ├── instance.py        # Workflow instance logic
│   └── persistence.py     # SQLite ORM
├── adapters/              # HTTP adapters to agents
│   ├── problem_collector.py
│   ├── pitch_evaluator.py
│   ├── risk_detector.py
│   └── evaluator.py
├── shared/                # Shared schemas & types
│   ├── schemas/          # Pydantic models
│   ├── enums/            # Workflow states, etc.
│   └── types/            # TypedDict types
├── PS Finder/            # Problem discovery LangGraph agent
├── Pitch Evaluator Agent/ # Pitch evaluation agent
├── Risk Agent/           # Risk analysis agent (copied to risk_backend/)
├── evaluator agent/      # Execution evaluation LangGraph agent
├── frontend/             # React UI
├── tests/                # Test suite
├── start.py              # Service launcher
├── start_services.py     # Alternative launcher
├── requirements.txt      # All dependencies
└── procurement.db        # SQLite (auto-created)
```

### Contributing

1. Branch from `main` to `feature/...`
2. Ensure services start and basic workflow completes
3. Add tests for new routes/logic
4. Update README if API changes
5. Submit PR with detailed description

## Contact & Support

**Team**: GovInnovate Procurement (SIH 2026 - Team ALPHA)
**Problem**: SIH26136 — Startup-Friendly Public Procurement Mechanism

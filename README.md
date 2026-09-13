# GovInnovate Procurement Multi-Agent Platform

**Backend Architecture**: Five microservices orchestrated by a deterministic state machine.

## Services

| Service | Port | Role |
|---------|------|------|
| **Orchestrator** | 8000 | Deterministic workflow state machine, API gateway, adapter coordinator |
| **Pitch Evaluator** | 8001 | Multimodal pitch analysis and deterministic scoring |
| **PS Finder (Problem Collector)** | 8002 | LangGraph agent: discovers and verifies genuine opportunities |
| **Risk Detector** | 8003 | LangGraph agent: comprehensive startup risk analysis |
| **Evaluator Agent** | 8004 | LangGraph agent: milestone evaluation and escrow authorization |

## Environment Setup

### Python Environment
- **Python**: 3.12
- **Virtual Environment**: Root `.venv`
- All services use the shared root `.venv` (no per-service venvs)

### Installation

```bash
python -m venv .venv
.venv/Scripts/activate  # On Windows
source .venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

### Database
- **SQLite**: `procurement.db` (local development)
- **Schema**: Workflows, Audits tables auto-created on startup

### Secrets & Configuration
- `.env` files: Never committed (security)
- Environment variables: API keys for Gemini, OpenAI, Groq, Tavily
- Each service reads its own .env if needed

## Running Services

### Start All Services

```bash
python start_services.py
```

Or individually:

```bash
# Terminal 1: Orchestrator (port 8000)
cd orchestrator
python -m uvicorn server:app --host 0.0.0.0 --port 8000

# Terminal 2: Pitch Evaluator (port 8001)
cd "Pitch Evaluator Agent/Pitch Evaluator Agent"
python -m uvicorn pitch_evaluator.api:app --host 0.0.0.0 --port 8001

# Terminal 3: PS Finder (port 8002)
cd "PS Finder"
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002

# Terminal 4: Risk Detector (port 8003)
cd "Risk Agent/Risk Agent/backend"
python main.py

# Terminal 5: Evaluator Agent (port 8004)
cd "evaluator agent/evaluator agent/backend"
python server.py
```

## API Workflow

### 1. Create Workflow
```bash
POST /api/workflows
{
  "opportunity_id": "opp-123",
  "title": "Energy Infrastructure",
  "description": "Renewable energy pilot program",
  "organization": "EnergyCorp",
  "status": "active"
}
```

### 2. Full Lifecycle
- **Opportunity Discovery** → `OPPORTUNITY_DISCOVERED`
- **Pitch Submission** → `PITCH_SUBMITTED`
- **Pitch Evaluation** → `PITCH_EVALUATED`
- **Risk Assessment** → `RISK_ASSESSED`
- **Human Review Gate** → `STARTUP_SELECTED` (if approved)
- **Pilot Allocation** → `PILOT_CREATED`
- **Milestone Tracking** → `MILESTONE_TRACKED`
- **Evidence Collection** → `EVIDENCE_COLLECTED`
- **Milestone Evaluation** → `MILESTONE_EVALUATED`
- **Final Evaluation** → `FINAL_EVALUATION`
- **Performance Review** → `PERFORMANCE_UPDATED`
- **Scale Recommendation** → `AWAITING_FINAL_DECISION`
- **Final Human Decision** → `COMPLETED` (if approved)

### 3. Persistence
- All workflow state and audit logs stored in `procurement.db`
- `COMPLETED` state persists across service restarts
- Audit trail tracks all agent calls and decisions

## Architecture

### Orchestrator (Port 8000)
- **Role**: Deterministic state machine + HTTP API gateway
- **Type**: Not a fifth agent—pure business logic
- **Pattern**: Adapter calls use real HTTP (no fabrication)
- **State**: Persisted to SQLite

### Four LangGraph Agents
- **PS Finder**: Opportunity discovery via web search and verification
- **Pitch Evaluator**: Deterministic multimodal analysis
- **Risk Detector**: Market, competitive, and operational risk synthesis
- **Evaluator Agent**: Milestone KPI verification + escrow authorization

### Adapters
- Located in `/adapters/`
- Each adapter calls its corresponding service over HTTP
- Pattern: `POST /endpoint` with canonical Pydantic models
- No result fabrication; service unavailability → HTTP error propagation

## Frontend

**Port**: 3000 (React dev server or production build)

- Orchestrator CORS enabled for `*` (all origins)
- Frontend communicates with Orchestrator API at `http://localhost:8000`

## Testing

```bash
# Run end-to-end lifecycle test
pytest orchestrator/tests/test_final_e2e.py -v

# Run orchestrator API tests
pytest orchestrator/tests/ -v
```

## Key Design Decisions

1. **Single Root `.venv`**: All services share one Python environment
   - Simplifies dependency management
   - Reduces disk footprint
   - Ensures version consistency

2. **Deterministic Orchestrator**: State machine is pure business logic
   - Handles state transitions (no LangGraph)
   - Coordinates adapter calls
   - Persists workflow history

3. **Real HTTP Adapters**: No fabrication or mocking
   - Adapters fail transparently if service unavailable
   - Errors propagated to caller
   - Full observability

4. **Persistent COMPLETED State**
   - Workflow reaches `COMPLETED` only after final human approval
   - State survives service restarts
   - Audit trail immutable

5. **Canonical Models**: Shared schemas across all services
   - Located in `/shared/schemas/`
   - Pydantic validation enforced at boundaries
   - Type safety across HTTP

## Git Workflow

- **Branch**: `feature/backend-orchestrator`
- **Commits**: Incremental, tested at each checkpoint
- **Attribution**: Co-authored by Claude Code

## Token Budget

Token usage optimized for:
- Minimal venv duplication
- Consolidated requirements
- Deterministic orchestrator (no agent overhead)
- Real HTTP calls (no agent loop latency)

---

**Status**: Backend integration complete. Five services running on root `.venv`. Deterministic orchestrator coordinating four LangGraph agents. All adapters use real HTTP. Full lifecycle tested to `COMPLETED` state with persistence.

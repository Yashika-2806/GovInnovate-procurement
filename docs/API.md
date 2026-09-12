# GovInnovate Procurement API Documentation

## Base URL
`http://localhost:8000`

## Startup command
`python -m uvicorn orchestrator.server:app --port 8000`

## Health Endpoint
`GET /health` -> Returns `{"status": "healthy", "service": "orchestrator"}`

## Endpoints
- `POST /api/workflows`: Create workflow
- `GET /api/workflows/{workflow_id}`: Get workflow state
- `POST /api/workflows/{workflow_id}/pitch`: Submit pitch
- `POST /api/workflows/{workflow_id}/pitch/evaluate`: Run pitch evaluation
- `POST /api/workflows/{workflow_id}/risk/assess`: Run risk assessment
- `POST /api/workflows/{workflow_id}/human-review`: Submit human review decision
- `POST /api/workflows/{workflow_id}/milestones/{milestone_id}/evaluate`: Evaluate milestone
- `POST /api/workflows/{workflow_id}/final-decision`: Submit final human decision

## Known Limitations & Security
- Authentication/RBAC not implemented in this phase.
- RAG/LLM integration currently uses deterministic/mock paths in adapters.

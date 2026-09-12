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

## Known Limitations & Security
- Authentication/RBAC not implemented in this phase.
- RAG/LLM integration currently uses deterministic/mock paths.

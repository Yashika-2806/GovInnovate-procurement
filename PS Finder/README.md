# Verified Problem & Challenge Discovery Agent
### ALPHA SIH Multi-Agent Platform (Problem Statement ID: SIH26136)

This repository contains the official implementation of the **Verified Problem & Challenge Discovery Agent** for the ALPHA SIH multi-agent platform. Powered by **LangGraph**, it continuously discovers, verifies, extracts, explains, and daily-monitors genuine publicly published solution-seeking opportunities from authoritative government and public enterprise sources.

---

## Core Product Principle
> **"We do not generate problems. We discover and verify problems/challenges that organizations have actually published for innovators or solution providers to address."**

- Only source-supported facts become verified opportunity data.
- Routine procurement ("Supply 500 standard CCTV cameras") and inferred problems are strictly rejected.
- Zero startup matching or solution generation logic leaks into this agent; it provides clean, verified intelligence to downstream agents in the ALPHA platform.

---

## Architecture & Workflows

```
                           [ SOURCE REGISTRY ]
                                    │
               ┌────────────────────┴────────────────────┐
               ↓                                         ↓
      Startup India Adapter                       MyGov Adapter
               │                                         │
               └────────────────────┬────────────────────┘
                                    ↓
                            [ CANDIDATE URLS ]
                                    ↓
                         [ SAFE FETCH & PARSE ]
                                    ↓
                       [ VERIFICATION & AUTHORITY ]
                         (Tier 1 Official Hierarchy)
                                    ↓
                       [ ELIGIBILITY CLASSIFIER ]
                      (Rejects Routine Procurement)
                                    ↓
                       [ STRUCTURED EXTRACTION ]
                       (Preserves Source Terminology)
                                    ↓
                        [ DEDUPLICATION SERVICE ]
                        (Automated Linking: 9B)
                                    ↓
                      [ PERSISTENCE & VERSIONING ]
                     (PostgreSQL + pgvector / SQLite)
                                    │
            ┌───────────────────────┴───────────────────────┐
            ↓                                               ↓
  [ EXPLAIN GRAPH (7A) ]                         [ MONITORING GRAPH (8B) ]
  • Grounded RAG retrieval                       • Daily deadline recheck
  • Generator Node                               • Status transitions (ACTIVE/EXPIRED)
  • Citation Critic Validation                   • Version history diffs
            │                                               │
            └───────────────────────┬───────────────────────┘
                                    ↓
                      [ FASTAPI REST API (46/47) ]
                      • Frontend UI Consumption
                      • Downstream Multi-Agent Contracts
```

---

## Quickstart

### 1. Setup Environment
```bash
# Clone and navigate to project root
cd "PS Finder"

# Virtual environment is already configured in .venv
.\.venv\Scripts\pip install -e .[dev]
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configurations:
- `GEMINI_API_KEY`: Google Gemini API Key (optional for local deterministic runs, required for LLM extraction).
- `DATABASE_URL`: PostgreSQL connection string (defaults to local SQLite fallback if Postgres is not running).
- `USE_SQLITE_FALLBACK=true`: Automatically uses `./data/ps_finder.db` and `./data/chroma`.

### 3. Seed Verified Sources & Initial Challenges
Run the seed script to register official sources and discover initial challenges:
```bash
.\.venv\Scripts\python scripts/seed_sources.py
```

### 4. Start the FastAPI Service
```bash
.\.venv\Scripts\python -m uvicorn src.main:app --port 8000 --reload
```
Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## REST API Endpoints (Section 47)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck and storage status |
| `GET` | `/api/opportunities` | Search and filter verified opportunities (`q`, `organization_type`, `domain`, `status`, pagination) |
| `GET` | `/api/opportunities/{id}` | Complete opportunity record with source evidence and provenance |
| `POST` | `/api/opportunities/search` | Agentic search endpoint for downstream multi-agent platform |
| `POST` | `/api/opportunities/{id}/explain` | Grounded 12-section explanation with citation critic approval |
| `GET` | `/api/opportunities/{id}/source` | Original authoritative source metadata and verification timestamp |
| `GET` | `/api/opportunities/{id}/history` | Historical version diffs and status changes |
| `POST` | `/api/discovery/run` | Triggers the LangGraph Discovery Graph |
| `POST` | `/api/monitoring/run` | Triggers the LangGraph Daily Monitoring Graph |

---

## Running Tests
Run the complete automated test suite:
```bash
.\.venv\Scripts\pytest -v
```
Tests cover:
- Verification authority checks (Tier 1 vs. secondary media).
- Eligibility filtering (qualifying problem statements vs. rejecting routine CCTV/AMC procurement).
- Deduplication and `unverified_duplicate_of` reference linking.
- LangGraph Discovery, Grounded Explain with Citation Critic, and Monitoring.
- FastAPI REST API endpoints and version history.

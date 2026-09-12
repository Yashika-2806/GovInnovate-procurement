# Pitch Evaluator Agent

**GovInnovate Procurement** — Smart India Hackathon 2026

---

## 1. What Pitch Evaluator Does

The **Pitch Evaluator Agent** is a specialized, deterministic, and multimodal evaluation microservice for analyzing startup procurement pitches. It executes a rigorous, evidence-first 8-stage evaluation pipeline:

1. **Multimodal Content Extraction**: Normalizes text, documents (PDF/PPTX), audio, and video pitches into timestamped, referenced segments (`NormalizedPitch`).
2. **Evidence Extraction**: Identifies and links concrete pitch claims to specific segments across modalities (`EvidenceCitation[]`).
3. **Criterion Analysis**: Analyzes evidence against configurable evaluation criteria using LLM or deterministic mock engines (`CriterionAnalysis[]`).
4. **Deterministic Weighted Scoring**: Calculates weighted totals purely mathematically using validated criteria weights without hallucination (`weighted_total`).
5. **Confidence Scoring**: Computes overall confidence as the weighted average of criterion confidences.
6. **Evidence Quality Calculation**: Measures verification levels, citation counts, and modality diversity.
7. **Risk Signals Extraction**: Deterministically scans weaknesses, uncertainties, and information gaps for structured downstream risk indicators (`RiskSignals`).
8. **PitchEvaluation Assembly**: Emits a complete, schema-validated `PitchEvaluation` JSON artifact with calculation audit trails.

---

## 2. What Pitch Evaluator Does NOT Do

To maintain architectural integrity, clear operational boundaries are enforced:

- **Pitch Evaluator != Workflow Orchestrator**: It does **not** manage procurement workflows, stage transitions, tender state, or lifecycle state.
- **Pitch Evaluator != Evaluator Agent**: It does **not** make procurement decisions, pass/fail recommendations, or bid rankings.
- **Pitch Evaluator != Risk Detector**: It extracts raw deterministic pattern signals (`RiskSignals`), but does **not** perform legal, financial, or organizational risk assessment.
- **No Database / Vector Store**: It is a stateless execution service; persistence and retrieval are handled by upstream platform layers.

---

## 3. Semantic Distinctions

> [!IMPORTANT]
> **Score ≠ Probability of Success**
> - **`criterion_scores` & `weighted_total` (0–100)**: Measure alignment against explicit criteria requirements based strictly on supplied evidence.
> - **`confidence` (0.0–1.0)**: Reflects the evaluator's certainty in its analysis based on evidence depth and clarity.
> - **`evidence_quality` (0.0–1.0)**: Reflects the richness, diversity, and verification tier of the submitted material.
> - These are **independent dimensions** and must never be conflated.

---

## 4. Supported Inputs & Formats

| Modality | Formats | Processing Method |
| :--- | :--- | :--- |
| **TEXT** | `.txt`, `.md`, `.markdown`, `.text` | Direct ingestion, structured paragraph & sentence segmentation |
| **AUDIO** | `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg` | Speech-to-Text transcription (`MockSTTEngine` or `FasterWhisperSTT`) |
| **VIDEO** | `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v` | Audio track extraction to STT + visual keyframe sampling |
| **DOCUMENT** | `.pdf`, `.pptx`, `.ppt` | Text, table, and image extraction with page and slide reference tracking |

---

## 5. Multimodal Extraction Pipeline

Raw input files are routed via `ExtractionFactory` into specific extractors that enforce:
- **File size limits**: Text (10MB), Documents (50MB), Audio (100MB), Video (500MB).
- **Strict format allowlists**: Rejects unsupported extensions with `UnsupportedFormatError`.
- **Resource cleanup**: Temporary files generated during audio/video extraction are automatically deleted.
- **Unified output**: Produces `NormalizedPitch` with `PitchSegment[]` preserving source modality, timecodes, and page numbers.

---

## 6. Evidence-First Approach

Evaluation is strictly anchored in extracted evidence citations (`EvidenceCitation`):
- **Citations link claims to source segments**: Every citation references one or more segment IDs.
- **Verification Levels**:
  - `independently_verified` (1.0) — Formal audit reports or certificates.
  - `third_party` (0.8) — Customer reviews, external publications, partner statements.
  - `system_generated` (0.6) — Automated system logs, telemetry, code repos.
  - `self_reported` (0.4) — Startup pitch claims or assertions.
  - `unknown` (0.2) — Unverified claims.
- **Prompt Injection Defense**: Evaluators treat all pitch text as untrusted data. Injected instructions are treated strictly as pitch text and never executed.

---

## 7. Criterion Analysis & Scoring Framework

Configured via `config/evaluation_criteria.yaml`, 14 standard criteria are supported:
- **Core Criteria**: Problem Validation (0.20), Scalability (0.15), Feasibility (0.15), Cost (0.15), Practicality (0.10).
- **Additional Criteria**: Solution Fit (0.05), Innovation (0.05), Technical Feasibility (~0.021), Market Validation (~0.021), Team Capability (~0.021), Implementation Readiness (~0.021), Government Fit (~0.021), Business/Sustainability (~0.021), Competitive Differentiation (~0.021).
- **Deterministic Math**: Total score is computed strictly as $\sum (\text{raw\_score}_i \times \text{weight}_i)$. Weights must sum to 1.0. An exact calculation audit trail is returned in `calculation_audit`.

---

## 8. Risk Signals

Deterministic keyword scanning extracts pattern indicators into structured categories:
- `technical_risk_indicators` (e.g., prototype, scalability, architecture gaps)
- `regulatory_risk_indicators` (e.g., compliance, GDPR, security certifications)
- `team_risk_indicators` (e.g., bandwidth, founder experience, hiring needs)
- `market_risk_indicators` (e.g., traction, pricing, competition)
- `financial_risk_indicators` (e.g., runway, unit economics, budget fit)

---

## 9. Operating Modes

### Mock Mode (Deterministic & Testable)
Default execution mode for unit tests, local development, and CI/CD without API keys or external services:
- Uses `MockEvidenceEngine` for deterministic keyword-based citation extraction.
- Uses `MockCriterionAnalysisEngine` for reproducible scoring based on evidence quantity.

### LLM Mode (Production)
Compatible with any OpenAI-compatible API endpoint (Ollama, vLLM, OpenAI):
- Configurable parameters:
  - `base_url` (env: `OPENAI_BASE_URL`, default `http://localhost:11434/v1`)
  - `api_key` (env: `OPENAI_API_KEY`, default `ollama`)
  - `model` (default `llama3.1:70b`)
  - `timeout_seconds` (default 120s)
- Pydantic structured output validation guarantees valid JSON schemas.

---

## 10. Orchestrator Integration Contract

Downstream systems (specifically the **Workflow Orchestrator**) can invoke the Pitch Evaluator either in-process via Python or out-of-process via HTTP REST.

### A. Invocation Methods

#### 1. In-Process Python Call
```python
from pitch_evaluator.service import EvaluatePitchRequest, PitchEvaluator

evaluator = PitchEvaluator(engine="mock", evidence_engine="mock")

request = EvaluatePitchRequest(
    pitch_id="pitch_demo_001",
    startup_id="startup_demo_001",
    problem_statement_id="prob_demo_001",
    pitch_content="Problem Validation: We conducted user research with 45 officers...",
    # or file_path="/path/to/pitch_deck.pdf",
    context={"procurement_tier": "municipal"},
)

evaluation = evaluator.evaluate_pitch(request)
```

#### 2. HTTP REST Endpoint
```http
POST /evaluate HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "pitch_id": "pitch_demo_001",
  "startup_id": "startup_demo_001",
  "problem_statement_id": "prob_demo_001",
  "pitch_content": "Problem Validation: We conducted user research with 45 officers...",
  "file_path": null,
  "evaluation_config": null,
  "context": {
    "procurement_tier": "municipal"
  }
}
```

### B. Request Schema (`EvaluatePitchRequest`)

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `pitch_id` | `string` | **Yes** | — | Unique identifier for the pitch submission (min length: 1). |
| `startup_id` | `string` | **Yes** | — | Unique identifier for the submitting startup (min length: 1). |
| `problem_statement_id` | `string` | No | `"default_problem_statement"` | Problem statement / tender challenge identifier. |
| `pitch_content` | `string \| null` | Conditional | `null` | Direct text pitch. Must provide either `pitch_content` or `file_path`. |
| `file_path` | `string \| null` | Conditional | `null` | Filesystem path to pitch document/media (`.pdf`, `.pptx`, `.mp3`, etc.). |
| `evaluation_config` | `dict \| null` | No | `null` | Optional runtime criteria/weight overrides. |
| `context` | `dict[str, Any]` | No | `{}` | Arbitrary contextual metadata from upstream orchestrator. |

*See [`examples/evaluate_request.json`](file:///home/saptak/Pitch%20Evaluator%20Agent/examples/evaluate_request.json) for a complete synthetic example.*

### C. Response Schema (`PitchEvaluation`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `pitch_evaluation_id` | `string` | Globally unique identifier for this evaluation run. |
| `pitch_id` | `string` | Correlated pitch ID from the request. |
| `startup_id` | `string` | Correlated startup ID from the request. |
| `problem_statement_id` | `string` | Correlated problem statement ID from the request. |
| `criterion_scores` | `dict[str, int]` | Individual scores (0–100) keyed by criteria name. |
| `weighted_total` | `integer` | Deterministic weighted score (0–100) computed strictly via criteria weights. |
| `confidence` | `float` | Evaluator certainty (0.0–1.0), computed as weighted average of criterion confidences. |
| `evidence_quality` | `float` | Independent evidence richness metric (0.0–1.0) based on citations and tiers. |
| `evidence_citations` | `list[EvidenceCitation]` | Preserved list of structured citations linking claims to source segments. |
| `strengths` | `list[string]` | Consolidated list of identified strengths across criteria. |
| `weaknesses` | `list[string]` | Consolidated list of identified weaknesses and vulnerabilities. |
| `missing_information` | `list[string]` | Critical required information omitted from the submission. |
| `uncertainties` | `list[string]` | Ambiguities, conflicting statements, or unverified claims flagged. |
| `risk_signals` | `RiskSignals` | Structured indicators categorized by technical, regulatory, team, market, financial. |
| `calculation_audit` | `list[dict]` | Exact audit entries: `criterion`, `raw_score`, `weight`, `weighted_contribution`. |
| `metadata` | `EvaluationMetadata` | Run metadata including timestamps, criteria config version, and modality. |

*See [`examples/pitch_evaluation_response.json`](file:///home/saptak/Pitch%20Evaluator%20Agent/examples/pitch_evaluation_response.json) for a complete 27-citation synthetic response.*

### D. Structured Evidence Format (`EvidenceCitation`)

> [!IMPORTANT]
> `evidence_citations` is **never a list of plain strings**. Every citation is a structured object with full segment provenance:

```json
{
  "claim": "We conducted user research with 45 public procurement officers across municipal jurisdictions",
  "criterion": "Problem Validation",
  "source_segments": [
    {
      "segment_id": "text_seg_1",
      "source_modality": "text",
      "start_ref": 36,
      "end_ref": 277,
      "excerpt": "Problem Validation: We conducted user research with 45 public procurement officers..."
    }
  ],
  "evidence_type": "user_research",
  "verification_level": "self_reported",
  "confidence": 0.85,
  "notes": "Direct user research metric reported with specific sample size."
}
```

### E. Semantic Distinctions & Boundaries

- **Score ≠ Confidence ≠ Evidence Quality**:
  - `weighted_total` (0–100) measures how well the pitch satisfies criteria rules.
  - `confidence` (0.0–1.0) measures how certain the model is based on evidence completeness.
  - `evidence_quality` (0.0–1.0) measures the verification tier and diversity of the evidence submitted.
- **What Pitch Evaluator Does NOT Own**:
  - **No Workflow Transitions**: The Orchestrator alone manages stages (e.g. screening -> review -> shortlist).
  - **No Decision / Ranking**: Evaluator Agent owns comparative ranking and pass/fail thresholds.
  - **No Comprehensive Risk Clearance**: Risk Detector owns legal, financial, and organizational risk audits.
  - **No State / Persistence**: Pitch Evaluator is completely stateless.

---

## 11. Run Configuration

All behavior can be controlled via standard environment variables:

| Variable | Type | Allowed Values | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `PITCH_EVALUATOR_ENGINE` | `string` | `mock`, `llm` | `mock` | Engine for criterion scoring analysis. |
| `PITCH_EVIDENCE_ENGINE` | `string` | `mock`, `llm` | `mock` | Engine for multimodal evidence extraction. |
| `OPENAI_BASE_URL` | `string` | Valid URL | `http://localhost:11434/v1` | Endpoint for LLM inference (Ollama, vLLM, OpenAI). |
| `OPENAI_API_KEY` | `string` | Auth Token | `ollama` | API key for the LLM endpoint. |
| `OPENAI_MODEL` | `string` | Model ID | `llama3.1:70b` | Model identifier used for inference. |

- **Default Zero-Dependency Execution**: When environment variables are unset, the service automatically runs in `mock` mode. It produces deterministic, reproducible, fully structured evaluations locally without requiring GPU access, external networks, or API keys.
- **Criteria Configuration**: Stored at `config/evaluation_criteria.yaml`. Defines 14 criteria with scoring rubrics, descriptions, and normalized weights summing to 1.0.

---

## 12. Run Locally Runbook

Follow these copy-paste commands to set up, test, and run the service locally:

### 1. Activate the Conda Environment
```bash
conda activate GovInnovate-procurement
```

### 2. Run Test Suite and Linters
```bash
# Run all unit, integration, and contract tests (161 passing, 1 skipped)
pytest tests/

# Run Ruff linter
ruff check src/ tests/

# Run Mypy strict static type check
mypy src/
```

### 3. Start the FastAPI Service
```bash
# Option A: Standard module entrypoint
uvicorn pitch_evaluator.api:app --host 0.0.0.0 --port 8000

# Option B: Factory entrypoint
uvicorn src.pitch_evaluator.api:create_app --factory --host 0.0.0.0 --port 8000
```

### 4. Health Check
```bash
curl -s http://localhost:8000/health | jq
```
Expected response:
```json
{
  "status": "healthy",
  "service": "pitch-evaluator-agent",
  "version": "0.1.0",
  "active_criteria": 14
}
```

### 5. Send Test Evaluation Request
```bash
curl -s -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @examples/evaluate_request.json | jq
```

---

## 13. Container Deployment (Docker)

The repository includes a production-grade, unprivileged Dockerfile based on `python:3.12-slim` with `ffmpeg` and `libgl1` for multimodal support:

### Build Docker Image
```bash
docker build -t pitch-evaluator .
```

### Run Docker Container
```bash
# Run in deterministic mock mode (port 8000)
docker run -d --name pitch-evaluator -p 8000:8000 \
  -e PITCH_EVALUATOR_ENGINE=mock \
  -e PITCH_EVIDENCE_ENGINE=mock \
  pitch-evaluator

# Verify health inside container
docker exec pitch-evaluator python -c \
  "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```


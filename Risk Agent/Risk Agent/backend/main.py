import uuid
import traceback
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.utils.llm_client import GeminiClient
from src.utils.search_client import SearchClient
from src.utils.citation_tracker import CitationTracker
from src.agents.orchestrator import RunOrchestrator

app = FastAPI(title="AI Startup Risk Evaluator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    problem_statement: str


# Initialize clients
llm_client = GeminiClient()
search_client = SearchClient()
citation_tracker = CitationTracker()
orchestrator = RunOrchestrator(llm_client, search_client, citation_tracker)


async def run_analysis(problem_statement: str, analysis_id: str):
    try:
        await orchestrator.run(problem_statement, analysis_id)
    except Exception as e:
        orchestrator.analyses[analysis_id]['status'] = 'error'
        orchestrator.analyses[analysis_id]['error'] = str(e)
        print(f"Analysis {analysis_id} failed: {traceback.format_exc()}")


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    analysis_id = str(uuid.uuid4())
    orchestrator.analyses[analysis_id] = {
        'status': 'processing',
        'progress': 0,
        'current_step': 'Starting...',
        'result': None,
        'error': None
    }
    background_tasks.add_task(run_analysis, req.problem_statement, analysis_id)
    return {"analysis_id": analysis_id}


@app.get("/api/status/{analysis_id}")
async def status(analysis_id: str):
    return orchestrator.get_status(analysis_id)


@app.get("/api/results/{analysis_id}")
async def results(analysis_id: str):
    result = orchestrator.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found or not complete")
    return result.model_dump(mode='json')


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from typing import Dict, Any
from shared.schemas.evaluation_result import EvaluationResult
import httpx

class EvaluatorAdapter:
    def __init__(self, api_url: str):
        self.api_url = api_url

    async def evaluate(self, state: Dict[str, Any]) -> EvaluationResult:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_url}/api/evaluate", json={"state": state})
            response.raise_for_status()
            data = response.json()["result"]
            # Map canonical JSON back to EvaluationResult
            return EvaluationResult(**data)

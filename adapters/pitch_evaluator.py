from typing import Dict, Any
from shared.schemas.pitch import Pitch
from shared.schemas.pitch_evaluation import PitchEvaluation
import httpx # Need to ensure httpx is used to call the internal API

class PitchEvaluatorAdapter:
    def __init__(self, api_url: str):
        self.api_url = api_url

    async def evaluate(self, pitch: Pitch) -> PitchEvaluation:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_url}/evaluate", json=pitch.model_dump())
            response.raise_for_status()
            data = response.json()
            # Map canonical JSON back to PitchEvaluation Pydantic model
            return PitchEvaluation(**data)

from typing import Dict, Any
from shared.schemas.opportunity import Opportunity
from shared.schemas.risk_assessment import RiskAssessment
import httpx

class RiskDetectorAdapter:
    def __init__(self, api_url: str):
        self.api_url = api_url

    async def assess_risk(self, opportunity: Opportunity) -> RiskAssessment:
        async with httpx.AsyncClient() as client:
            # Risk agent expects problem_statement
            response = await client.post(f"{self.api_url}/api/analyze", json={"problem_statement": opportunity.description})
            response.raise_for_status()
            analysis_id = response.json()["analysis_id"]

            # Risk agent is asynchronous processing, need to poll result.
            # This adapter needs to handle polling or assume it's external to the direct request.
            # For now, simplistic polling:
            import asyncio
            while True:
                status_res = await client.get(f"{self.api_url}/api/status/{analysis_id}")
                if status_res.json()['status'] == 'completed':
                    break
                await asyncio.sleep(1)

            result_res = await client.get(f"{self.api_url}/api/results/{analysis_id}")
            # Map canonical JSON back to RiskAssessment Pydantic model
            return RiskAssessment(**result_res.json())

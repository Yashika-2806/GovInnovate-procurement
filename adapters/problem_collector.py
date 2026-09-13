from typing import List
from shared.schemas.opportunity import Opportunity
import httpx

class ProblemCollectorAdapter:
    def __init__(self, api_url: str):
        self.api_url = api_url

    async def search_opportunities(self, query: str) -> List[Opportunity]:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_url}/api/opportunities/search", json={"query": query})
            response.raise_for_status()
            data = response.json()
            return [Opportunity(**item) for item in data]

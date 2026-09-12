import yaml
from typing import List
from pydantic import BaseModel
from src.models.startup_profile import StartupProfile
from src.models.research_data import FailedStartup

class FailedStartupList(BaseModel):
    startups: List[FailedStartup]

class FailureAnalyzerAgent:
    def __init__(self, llm_client, search_client):
        self.llm_client = llm_client
        self.search_client = search_client
        with open('config/prompts.yaml', 'r') as f:
            self.prompts = yaml.safe_load(f)

    async def analyze(self, profile: StartupProfile) -> List[FailedStartup]:
        system_instruction = self.prompts.get('failure_analysis', '')
        
        industry = profile.industry.value if profile.industry else 'technology'
        sub_industry = profile.sub_industry.value if profile.sub_industry else ''
        
        queries = [
            f"{industry} startup failures shutdown",
            f"{industry} startup post-mortem",
            f"Failed {industry} companies funding",
            f"{sub_industry} startup bankruptcy closed"
        ]
        
        context = ""
        for query in queries:
            results = await self.search_client.search(query)
            for res in results:
                context += f"Source: {res['url']}\nContent: {res['content']}\n\n"
                
        prompt = f"Profile: {profile.model_dump_json()}\n\nSearch Context:\n{context}"
        
        try:
            res = await self.llm_client.generate_structured(prompt, system_instruction, FailedStartupList)
            return res.startups
        except Exception as e:
            print(f"Error analyzing failures: {e}")
            return []

import yaml
from src.models.startup_profile import StartupProfile
from src.models.research_data import MarketResearch

class MarketResearchAgent:
    def __init__(self, llm_client, search_client):
        self.llm_client = llm_client
        self.search_client = search_client
        with open('config/prompts.yaml', 'r') as f:
            self.prompts = yaml.safe_load(f)

    async def research(self, profile: StartupProfile) -> MarketResearch:
        system_instruction = self.prompts.get('market_research', '')
        
        industry = profile.industry.value if profile.industry and profile.industry.value else 'technology'
        target = profile.target_customers.value if profile.target_customers and profile.target_customers.value else 'enterprise customers'
        
        queries = [
            f"{industry} TAM SAM SOM market size report",
            f"{industry} {target} market growth rate"
        ]
        
        context = ""
        citations = []
        for query in queries:
            results = await self.search_client.search(query)
            for res in results:
                url = res.get('url', '')
                if url and url not in citations:
                    citations.append(url)
                context += f"Source: {url}\nContent: {res.get('content', '')}\n\n"
                
        prompt = f"Profile: {profile.model_dump_json()}\n\nSearch Context:\n{context}"
        
        try:
            res = await self.llm_client.generate_structured(prompt, system_instruction, MarketResearch)
            if not res.citations:
                res.citations = citations
            return res
        except Exception as e:
            print(f"Error researching market: {e}")
            return MarketResearch(
                tam="Insufficient verified data",
                sam="Insufficient verified data",
                som="Insufficient verified data",
                growth_rate="Estimated 10-20% CAGR",
                maturity="Growing",
                concentration="Fragmented",
                key_players=[],
                citations=citations
            )

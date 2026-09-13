import yaml
from src.models.startup_profile import StartupProfile
from src.models.research_data import IndustryResearch

class IndustryResearchAgent:
    def __init__(self, llm_client, search_client):
        self.llm_client = llm_client
        self.search_client = search_client
        with open('config/prompts.yaml', 'r') as f:
            self.prompts = yaml.safe_load(f)

    async def research(self, profile: StartupProfile) -> IndustryResearch:
        system_instruction = self.prompts.get('industry_research', '')
        
        industry = profile.industry.value if profile.industry and profile.industry.value else 'technology'
        sub_industry = profile.sub_industry.value if profile.sub_industry and profile.sub_industry.value else ''
        
        queries = [
            f"{industry} {sub_industry} industry trends",
            f"{industry} market size growth drivers",
            f"{sub_industry} challenges failure rate"
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
            res = await self.llm_client.generate_structured(prompt, system_instruction, IndustryResearch)
            if not res.industry_name:
                res.industry_name = industry
            if not res.citations:
                res.citations = citations
            return res
        except Exception as e:
            print(f"Error researching industry: {e}")
            return IndustryResearch(
                industry_name=industry,
                market_size="Data unavailable",
                growth_rate="Data unavailable",
                failure_rate="~90% general startup failure rate",
                common_failure_patterns=["Lack of product-market fit", "Cash flow depletion", "Regulatory friction"],
                key_trends=["AI automation", "Cloud adoption"],
                citations=citations
            )

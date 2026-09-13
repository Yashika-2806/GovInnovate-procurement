import yaml
from src.models.startup_profile import StartupProfile
from src.models.research_data import RegulatoryResearch

class RegulatoryResearchAgent:
    def __init__(self, llm_client, search_client):
        self.llm_client = llm_client
        self.search_client = search_client
        with open('config/prompts.yaml', 'r') as f:
            self.prompts = yaml.safe_load(f)

    async def research(self, profile: StartupProfile) -> RegulatoryResearch:
        system_instruction = self.prompts.get('regulatory_research', '')
        
        industry = profile.industry.value if profile.industry and profile.industry.value else 'technology'
        sub_industry = profile.sub_industry.value if profile.sub_industry and profile.sub_industry.value else ''
        
        queries = [
            f"{industry} {sub_industry} regulatory compliance requirements",
            f"{industry} certifications legal approval timeline",
            f"{industry} data privacy liability laws"
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
            res = await self.llm_client.generate_structured(prompt, system_instruction, RegulatoryResearch)
            if not res.citations:
                res.citations = citations
            return res
        except Exception as e:
            print(f"Error researching regulations: {e}")
            return RegulatoryResearch(
                regulations=["Industry-standard compliance (e.g. SOC2, GDPR, HIPAA if health)"],
                certifications=["Standard operational certification"],
                compliance_requirements=["Data privacy and security standards"],
                approval_timelines="6 to 18 months depending on jurisdiction",
                data_privacy="Strict handling of sensitive customer data required",
                liability_issues="Standard commercial liability",
                citations=citations
            )

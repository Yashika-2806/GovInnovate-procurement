import os
import asyncio
from typing import List, Dict, Any
from tavily import AsyncTavilyClient, TavilyClient

class SearchClient:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.has_key = bool(self.api_key and self.api_key != "your_tavily_api_key_here")
        if self.has_key:
            try:
                self.client = AsyncTavilyClient(api_key=self.api_key)
                self.is_async = True
            except Exception:
                self.client = TavilyClient(api_key=self.api_key)
                self.is_async = False
        else:
            self.client = None

    async def search(self, query: str, max_results: int = 3, search_depth: str = 'basic') -> List[Dict[str, Any]]:
        if not self.has_key:
            return []
        
        try:
            # Enforce 8-second timeout on web searches so slow networks never block the pipeline
            if self.is_async:
                response = await asyncio.wait_for(
                    self.client.search(query=query, search_depth=search_depth, max_results=max_results),
                    timeout=8.0
                )
            else:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.client.search, query=query, search_depth=search_depth, max_results=max_results),
                    timeout=8.0
                )
            return response.get("results", [])
        except Exception as e:
            print(f"Search notice for '{query[:30]}...': {e}")
            return []

    async def search_multiple(self, queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        if not self.has_key:
            return {q: [] for q in queries}
            
        tasks = [self.search(query) for query in queries]
        results = await asyncio.gather(*tasks)
        return dict(zip(queries, results))

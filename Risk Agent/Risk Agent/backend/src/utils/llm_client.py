import os
import json
import re
import asyncio
from typing import Optional, Type, TypeVar
import google.generativeai as genai
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_random_exponential

T = TypeVar('T', bound=BaseModel)

class GeminiClient:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('GEMINI_API_KEY not set')
        # Use REST transport to avoid gRPC connection hangs
        genai.configure(api_key=api_key, transport='rest')
        self.model_name = 'gemini-3.6-flash'

    @retry(stop=stop_after_attempt(4), wait=wait_random_exponential(min=3, max=20))
    async def generate(self, prompt: str, system_instruction: str = '') -> str:
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=system_instruction if system_instruction else None
        )
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text

    @retry(stop=stop_after_attempt(4), wait=wait_random_exponential(min=3, max=20))  
    async def generate_structured(self, prompt: str, system_instruction: str, pydantic_model: Type[T]) -> T:
        schema_json = json.dumps(pydantic_model.model_json_schema())
        full_system = f"{system_instruction}\n\nYou MUST return a JSON object adhering to this JSON Schema:\n{schema_json}\nOutput ONLY valid JSON."

        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=full_system,
            generation_config=genai.GenerationConfig(
                response_mime_type='application/json'
            )
        )
        response = await asyncio.to_thread(model.generate_content, prompt)
        raw_text = response.text.strip()
        
        # Strip markdown fences if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)
            
        return pydantic_model.model_validate_json(raw_text)

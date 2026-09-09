import httpx
import os
from typing import Dict, Any
from .base import AIProvider

class OllamaAIProvider(AIProvider):
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5")
        self.timeout = float(os.getenv("OLLAMA_API_TIMEOUT", 30.0))

    async def generate_intelligence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are FloodIntel's evidence-grounded intelligence engine.
        Context: {context}
        
        Provide a structured response. Use the provided context only.
        """
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                # Assuming Ollama returns a JSON response with "response" field
                # In production, we'd structure this better
                return {"text": response.json().get("response", ""), "status": "AVAILABLE"}
        except Exception as e:
            print(f"AI Provider error: {e}")
            return {"text": "", "status": "ERROR"}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False

from abc import ABC, abstractmethod
from typing import Dict, Any

class AIProvider(ABC):
    @abstractmethod
    async def generate_intelligence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

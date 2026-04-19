from __future__ import annotations

from app.integrations.litellm.client import LiteLLMClient
from app.schemas.llm import ExplainabilityPayload, StructuredEventAssessment


class LLMService:
    def __init__(self) -> None:
        self.client = LiteLLMClient()

    async def analyze_event(self, text: str) -> tuple[StructuredEventAssessment, str]:
        return await self.client.assess_text_event(text)

    async def build_explanation(self, text: str, factors: list[str], adjustment: float) -> ExplainabilityPayload:
        return await self.client.build_explanation(text, factors, adjustment)

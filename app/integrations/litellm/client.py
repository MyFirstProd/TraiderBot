from __future__ import annotations

import hashlib
import json

import httpx

from app.config.settings import get_settings
from app.core.exceptions import ExternalServiceError
from app.schemas.llm import ExplainabilityPayload, StructuredEventAssessment


class LiteLLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self._client = httpx.AsyncClient(base_url=settings.LITELLM_API_BASE, timeout=settings.LITELLM_TIMEOUT_SECONDS)

    async def assess_text_event(self, text: str) -> tuple[StructuredEventAssessment, str]:
        prompt_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if not self.settings.LLM_ENABLED:
            return (
                StructuredEventAssessment(
                    event_type="news",
                    sentiment=0.0,
                    confidence=0.3,
                    novelty=0.4,
                    source_reliability=0.5,
                    market_relevance=0.4,
                    contradiction_flag=False,
                    summary=f"Краткая сводка: {text[:180]}",
                    affected_symbols=[],
                ),
                prompt_hash,
            )
        payload = {
            "model": self.settings.LITELLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Верни строго JSON с ключами "
                        "event_type,sentiment,confidence,novelty,source_reliability,market_relevance,"
                        "contradiction_flag,summary,affected_symbols. Поле summary пиши по-русски."
                    ),
                },
                {"role": "user", "content": text[:8000]},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {}
        token = self.settings.LITELLM_API_KEY.get_secret_value()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = await self._client.post("/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
            return StructuredEventAssessment.model_validate(parsed), prompt_hash
        except Exception as exc:
            raise ExternalServiceError(f"Invalid LLM JSON output: {exc}") from exc

    async def build_explanation(self, text: str, factors: list[str], adjustment: float) -> ExplainabilityPayload:
        if not self.settings.LLM_ENABLED:
            return ExplainabilityPayload(summary=text[:250], factors=factors, score_adjustment=adjustment)
        assessment, _ = await self.assess_text_event(text)
        return ExplainabilityPayload(summary=assessment.summary, factors=factors, score_adjustment=adjustment)

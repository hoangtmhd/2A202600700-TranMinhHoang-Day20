import logging
from dataclasses import dataclass
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using Gemini."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        # If api_key is None, genai.Client() will fall back to GEMINI_API_KEY env var
        self.client = genai.Client(api_key=self.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Keep retry, timeout, and token logging here rather than inside agents.
        """
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config,
            )

            input_tokens = 0
            output_tokens = 0
            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0

            # Estimate cost for gemini-2.5-flash:
            # Input: $0.075 / 1M tokens ($0.000000075 per token)
            # Output: $0.3 / 1M tokens ($0.0000003 per token)
            cost_usd = (input_tokens * 0.075 / 1_000_000) + (output_tokens * 0.3 / 1_000_000)

            return LLMResponse(
                content=response.text or "",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
        except Exception as e:
            logger.error(f"Gemini API error during generation: {e}")
            raise e

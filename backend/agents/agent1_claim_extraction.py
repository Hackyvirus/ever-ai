"""
Agent 1 – Claim Extraction Agent
Extracts structured claims, named entities, author, and publisher from raw text.
"""
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm_provider import get_llm_provider
from models.schemas import ClaimExtractionResult

log = structlog.get_logger()

SYSTEM_PROMPT = """You are a specialized Claim Extraction Agent for a fake news detection system.

Your job:
1. Extract the author name and publisher/outlet name from the text (if present).
2. Extract 1–5 main factual claims as structured JSON.
3. Identify named entities (people, organizations, locations, dates).
4. Provide a short neutral summary.

RULES:
- Only extract verifiable factual claims, not opinions.
- Each claim must have: claim_text, claim_type (factual/opinion/statistic/quote), subject, predicate, object, confidence (0.0–1.0).
- Named entities: label must be one of PERSON, ORG, GPE, DATE, NUMBER, EVENT.
- Confidence = how sure you are this is an actual claim (0.0–1.0).

Respond ONLY with a valid JSON object matching this structure:
{
  "author_name": "string or null",
  "publisher_name": "string or null",
  "publisher_domain": "string or null",
  "claims": [
    {
      "id": "uuid-string",
      "claim_text": "The full claim sentence",
      "claim_type": "factual|opinion|statistic|quote",
      "subject": "who/what",
      "predicate": "does/is/has",
      "object": "what/whom",
      "confidence": 0.85
    }
  ],
  "named_entities": [
    {"text": "WHO", "label": "ORG", "confidence": 0.95}
  ],
  "summary": "One-paragraph neutral summary of the text.",
  "language": "en"
}"""


class ClaimExtractionAgent:
    """Agent 1: Extracts structured claims from raw news text."""

    def __init__(self):
        self.llm = get_llm_provider()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def run(self, text: str) -> ClaimExtractionResult:
        log.info("agent1_start", text_length=len(text))

        response = await self.llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Extract claims from this news text:\n\n{text}",
            temperature=0.1,
            max_tokens=2500,
        )

        data = response.parse_json()

        # Ensure claim IDs exist
        import uuid
        for claim in data.get("claims", []):
            if not claim.get("id"):
                claim["id"] = str(uuid.uuid4())

        result = ClaimExtractionResult(**data)
        log.info(
            "agent1_complete",
            claims=len(result.claims),
            entities=len(result.named_entities),
            author=result.author_name,
            publisher=result.publisher_name,
        )
        return result

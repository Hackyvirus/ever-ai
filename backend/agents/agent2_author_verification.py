"""
Agent 2 – Author Verification Agent
Scores author credibility using mock journalist DB + LLM reasoning.
"""
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm_provider import get_llm_provider
from models.schemas import AuthorVerificationResult

log = structlog.get_logger()

# ─────────────────────────────────────────────
# Mock Journalist Database
# In production: replace with real DB / API (MediaWise, PolitiFact staff DB, etc.)
# ─────────────────────────────────────────────
JOURNALIST_DB = {
    # Verified journalists
    "john smith": {"outlets": ["Reuters", "AP"], "score": 82, "verified": True},
    "jane doe": {"outlets": ["BBC", "Guardian"], "score": 88, "verified": True},
    "carlos mendez": {"outlets": ["El País", "NYT"], "score": 79, "verified": True},
    "priya sharma": {"outlets": ["NDTV", "The Hindu"], "score": 77, "verified": True},
    "michael chen": {"outlets": ["WSJ", "Bloomberg"], "score": 85, "verified": True},
    "sarah johnson": {"outlets": ["Washington Post"], "score": 81, "verified": True},
    # Known problematic accounts
    "freedom patriot": {"outlets": ["InfoWars"], "score": 12, "verified": False},
    "truth seeker 99": {"outlets": ["NaturalNews"], "score": 8, "verified": False},
    "real news daily": {"outlets": ["Unknown"], "score": 15, "verified": False},
}

# Domain authority mock scores (0-100)
DOMAIN_AUTHORITY = {
    "reuters.com": 95, "apnews.com": 94, "bbc.com": 92, "theguardian.com": 88,
    "nytimes.com": 90, "washingtonpost.com": 89, "wsj.com": 88, "bloomberg.com": 87,
    "cnn.com": 82, "foxnews.com": 75, "ndtv.com": 72, "thehindu.com": 74,
    "infowars.com": 5, "naturalnews.com": 3, "beforeitsnews.com": 2,
    "breitbart.com": 38, "dailycaller.com": 42,
}

SYSTEM_PROMPT = """You are an Author Credibility Verification Agent.

Given an author name and optional publisher context, assess the author's credibility.

Consider:
- Does the name look real or like a pseudonym/alias?
- Is this name associated with credible journalism?
- Any red flags (anonymous, vague byline, single-name only)?

Respond with JSON ONLY:
{
  "author_name": "string",
  "credibility_score": 0-100,
  "found_in_journalist_db": true/false,
  "known_outlets": ["list"],
  "domain_authority_score": 0-100,
  "public_profile_found": true/false,
  "reasoning": "2-3 sentence explanation",
  "flags": ["flag1", "flag2"]
}

Possible flags: anonymous, pseudonym, low_history, single_byline, no_social_presence, known_misinformation_author"""


class AuthorVerificationAgent:
    """Agent 2: Verifies author credibility using mock DB + LLM analysis."""

    def __init__(self):
        self.llm = get_llm_provider()

    def _lookup_journalist_db(self, name: str) -> dict | None:
        if not name:
            return None
        return JOURNALIST_DB.get(name.lower().strip())

    def _lookup_domain_authority(self, domain: str | None) -> float:
        if not domain:
            return 50.0
        return float(DOMAIN_AUTHORITY.get(domain.lower().strip(), 50))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def run(
        self, author_name: str | None, publisher_domain: str | None = None
    ) -> AuthorVerificationResult:
        if not author_name:
            author_name = "Unknown/Anonymous"

        log.info("agent2_start", author=author_name, domain=publisher_domain)

        # Check mock DB first (deterministic)
        db_record = self._lookup_journalist_db(author_name)
        domain_authority = self._lookup_domain_authority(publisher_domain)

        # Build context for LLM
        db_context = ""
        if db_record:
            db_context = f"\nJournalist DB match: {db_record}"

        user_msg = (
            f"Verify author: '{author_name}'\n"
            f"Publisher domain: {publisher_domain or 'unknown'}\n"
            f"Domain authority score: {domain_authority}/100\n"
            f"{db_context}\n\n"
            "Assess credibility. If author is 'Unknown/Anonymous', give low score with flag."
        )

        response = await self.llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            temperature=0.1,
            max_tokens=600,
        )

        data = response.parse_json()

        # Override with deterministic DB data if found
        if db_record:
            data["found_in_journalist_db"] = True
            data["known_outlets"] = db_record["outlets"]
            # Blend LLM score with DB score (70/30 weighting)
            data["credibility_score"] = round(
                0.7 * db_record["score"] + 0.3 * data.get("credibility_score", 50), 1
            )

        data["domain_authority_score"] = domain_authority
        data["author_name"] = author_name

        result = AuthorVerificationResult(**data)
        log.info("agent2_complete", author=author_name, score=result.credibility_score)
        return result

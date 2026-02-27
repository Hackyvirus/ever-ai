"""
Agent 3 – Publisher Verification Agent
Scores publisher credibility using mock WHOIS data + fake news database.
"""
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm_provider import get_llm_provider
from models.schemas import PublisherVerificationResult

log = structlog.get_logger()

# ─────────────────────────────────────────────
# Mock Fake News Database
# In production: replace with NewsGuard API, MBFC data, etc.
# ─────────────────────────────────────────────
FAKE_NEWS_DB = {
    "infowars.com", "naturalnews.com", "beforeitsnews.com",
    "yournewswire.com", "worldnewsdailyreport.com", "thelastlineofdefense.org",
    "empirenews.net", "abcnews.com.co", "huzlers.com", "nationalreport.net",
    "theonion.com",  # satire
    "clickhole.com",  # satire
    "thebeaverton.com",  # satire
}

# Mock WHOIS data — domain age in years, country, registered
MOCK_WHOIS = {
    "reuters.com":         {"age_years": 29, "country": "US", "registered": True},
    "apnews.com":          {"age_years": 28, "country": "US", "registered": True},
    "bbc.com":             {"age_years": 28, "country": "GB", "registered": True},
    "theguardian.com":     {"age_years": 27, "country": "GB", "registered": True},
    "nytimes.com":         {"age_years": 30, "country": "US", "registered": True},
    "washingtonpost.com":  {"age_years": 28, "country": "US", "registered": True},
    "wsj.com":             {"age_years": 28, "country": "US", "registered": True},
    "bloomberg.com":       {"age_years": 27, "country": "US", "registered": True},
    "cnn.com":             {"age_years": 28, "country": "US", "registered": True},
    "ndtv.com":            {"age_years": 23, "country": "IN", "registered": True},
    "thehindu.com":        {"age_years": 25, "country": "IN", "registered": True},
    "infowars.com":        {"age_years": 12, "country": "US", "registered": True},
    "naturalnews.com":     {"age_years": 15, "country": "US", "registered": True},
    "beforeitsnews.com":   {"age_years": 8, "country": "Unknown", "registered": True},
    "yournewswire.com":    {"age_years": 3, "country": "Unknown", "registered": False},
}

# Credibility scores from Media Bias / Fact Check style (mock)
PUBLISHER_SCORES = {
    "reuters.com": 96, "apnews.com": 95, "bbc.com": 91, "theguardian.com": 87,
    "nytimes.com": 89, "washingtonpost.com": 88, "wsj.com": 87, "bloomberg.com": 86,
    "cnn.com": 79, "ndtv.com": 71, "thehindu.com": 74, "foxnews.com": 62,
    "infowars.com": 3, "naturalnews.com": 2, "beforeitsnews.com": 4,
}

SYSTEM_PROMPT = """You are a Publisher Credibility Verification Agent.

Given a publisher name, domain, WHOIS data, and fake news database status, assess credibility.

Consider:
- Domain age (older = generally more trustworthy)
- WHOIS registration status (no data = red flag)
- Presence in known fake news databases
- General reputation of the publisher

Respond with JSON ONLY:
{
  "publisher_name": "string",
  "domain": "string or null",
  "credibility_score": 0-100,
  "domain_age_years": number or null,
  "in_fake_news_db": true/false,
  "whois_registered": true/false,
  "country": "string or null",
  "reasoning": "2-3 sentence explanation",
  "flags": ["flag1", "flag2"]
}

Possible flags: known_misinformation, very_new_domain, no_whois, satire_site, unknown_publisher, no_about_page, clickbait_history"""


class PublisherVerificationAgent:
    """Agent 3: Verifies publisher credibility."""

    def __init__(self):
        self.llm = get_llm_provider()

    def _check_fake_news_db(self, domain: str | None) -> bool:
        if not domain:
            return False
        return domain.lower().strip() in FAKE_NEWS_DB

    def _get_whois(self, domain: str | None) -> dict:
        if not domain:
            return {"age_years": None, "country": None, "registered": False}
        return MOCK_WHOIS.get(
            domain.lower().strip(),
            {"age_years": None, "country": "Unknown", "registered": True},
        )

    def _get_base_score(self, domain: str | None) -> float | None:
        if not domain:
            return None
        return PUBLISHER_SCORES.get(domain.lower().strip())

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def run(
        self, publisher_name: str | None, domain: str | None = None
    ) -> PublisherVerificationResult:
        if not publisher_name:
            publisher_name = "Unknown Publisher"

        log.info("agent3_start", publisher=publisher_name, domain=domain)

        in_fake_db = self._check_fake_news_db(domain)
        whois = self._get_whois(domain)
        base_score = self._get_base_score(domain)

        user_msg = (
            f"Publisher: '{publisher_name}'\n"
            f"Domain: {domain or 'unknown'}\n"
            f"Domain age: {whois['age_years']} years\n"
            f"WHOIS registered: {whois['registered']}\n"
            f"Country: {whois['country']}\n"
            f"In known fake news database: {in_fake_db}\n"
            f"Base credibility score from MBFC-style DB: {base_score or 'not found'}\n\n"
            "Assess publisher credibility."
        )

        response = await self.llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            temperature=0.1,
            max_tokens=600,
        )

        data = response.parse_json()

        # Override with deterministic data
        data["in_fake_news_db"] = in_fake_db
        data["whois_registered"] = whois["registered"]
        data["domain_age_years"] = whois["age_years"]
        data["country"] = whois.get("country")
        data["publisher_name"] = publisher_name
        data["domain"] = domain

        if base_score is not None:
            # Blend: 60% deterministic DB score, 40% LLM score
            data["credibility_score"] = round(
                0.6 * base_score + 0.4 * data.get("credibility_score", 50), 1
            )

        if in_fake_db and "known_misinformation" not in data.get("flags", []):
            data.setdefault("flags", []).insert(0, "known_misinformation")
            data["credibility_score"] = min(data.get("credibility_score", 10), 15)

        result = PublisherVerificationResult(**data)
        log.info(
            "agent3_complete",
            publisher=publisher_name,
            score=result.credibility_score,
            in_fake_db=in_fake_db,
        )
        return result

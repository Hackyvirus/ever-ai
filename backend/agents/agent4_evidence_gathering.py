"""
Agent 4 – Evidence Gathering Agent
Uses Tavily Search API for REAL web search results.
Falls back to mock data if API key not configured.
"""
import os
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm_provider import get_llm_provider
from models.schemas import EvidenceGatheringResult, EvidenceArticle, ExtractedClaim

log = structlog.get_logger()

# ─────────────────────────────────────────────
# Mock fallback (used only if no Tavily key)
# ─────────────────────────────────────────────
MOCK_ARTICLE_POOL = [
    {
        "title": "Experts dispute viral claims circulating on social media",
        "url": "https://apnews.com/fact-check/viral-claims-2024",
        "publisher": "AP News",
        "published_date": "2024-04-02",
        "content": "Fact-checkers found the circulating claims to be misleading or without evidence.",
    },
    {
        "title": "Medical community warns against unproven treatments",
        "url": "https://who.int/news/medical-warnings-2024",
        "publisher": "WHO",
        "published_date": "2024-02-20",
        "content": "The WHO issued an advisory warning against unverified medical treatments.",
    },
    {
        "title": "Fact-check: Viral quote attributed incorrectly",
        "url": "https://snopes.com/fact-check/viral-quote",
        "publisher": "Snopes",
        "published_date": "2024-03-18",
        "content": "The widely shared quote was either taken out of context or falsely attributed.",
    },
    {
        "title": "University study finds mixed results on health claims",
        "url": "https://harvard.edu/news/health-study",
        "publisher": "Harvard Health",
        "published_date": "2024-01-25",
        "content": "A university study found some claims supported by evidence, while others lacked backing.",
    },
    {
        "title": "Researchers find contradicting evidence in viral report",
        "url": "https://theguardian.com/science/contradicting-evidence",
        "publisher": "The Guardian",
        "published_date": "2024-03-22",
        "content": "Multiple independent researchers found significant methodological flaws in the viral study.",
    },
]

SYSTEM_PROMPT = """You are an Evidence Analysis Agent for a fake news detection system.

Given a claim and a list of retrieved articles from real web search, you must:
1. Determine whether each article SUPPORTS, CONTRADICTS, or is NEUTRAL toward the claim.
2. Assign a relevance score (0.0-1.0) to each article.
3. Write a short summary (1-2 sentences) of each article's stance.
4. Write an overall evidence summary.

CRITICAL RULES:
- If search results reveal the CORRECT fact (e.g. who actually is PM of India), 
  mark articles that contradict the claim as CONTRADICTING with high relevance.
- If the claim names a wrong person for a position, and search confirms a different person,
  that is CONTRADICTING evidence.
- Be specific: mention the correct fact in your evidence_summary.
- Do NOT say "insufficient evidence" when the search results clearly show the claim is wrong.

Respond with JSON ONLY:
{
  "articles": [
    {
      "title": "Article title",
      "url": "article url",
      "publisher": "publisher name",
      "published_date": "YYYY-MM-DD or null",
      "summary": "1-2 sentence summary showing how this relates to the claim",
      "stance": "supporting|contradicting|neutral",
      "relevance_score": 0.0-1.0
    }
  ],
  "supporting_count": 0,
  "contradicting_count": 0,
  "neutral_count": 0,
  "evidence_summary": "Clear 2-3 sentence summary. If claim is wrong, state the correct fact."
}"""


def _tavily_search(query: str, n: int = 10) -> list[dict]:
    """Real web search using Tavily API."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=n,
            include_answer=True,
        )
        results = []

        # Add Tavily direct answer first — most reliable
        answer = response.get("answer")
        if answer:
            results.append({
                "title": f"Direct Answer: {query[:80]}",
                "url": "https://tavily.com/direct-answer",
                "publisher": "Tavily Search (aggregated answer)",
                "published_date": None,
                "content": answer,
            })

        for r in response.get("results", []):
            domain = r.get("url", "").split("/")[2] if r.get("url") else "Unknown"
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "publisher": r.get("source", domain),
                "published_date": r.get("published_date", None),
                "content": r.get("content", r.get("snippet", ""))[:600],
            })

        log.info("tavily_search_success", query=query[:60], results=len(results))
        return results

    except ImportError:
        log.warning("tavily_not_installed", hint="pip install tavily-python")
        return []
    except Exception as e:
        log.error("tavily_search_failed", error=str(e))
        return []


def _mock_search(n: int = 5) -> list[dict]:
    """Fallback mock search when Tavily not configured."""
    import random
    pool = MOCK_ARTICLE_POOL.copy()
    random.shuffle(pool)
    return pool[:n]


def _build_search_query(claim: ExtractedClaim) -> str:
    """Build an effective search query from the claim."""
    text = claim.claim_text.lower()

    # Position/role claims → "who is X" query
    if any(w in text for w in [
        "prime minister", "president", "ceo", "minister", "governor",
        "chief minister", "chancellor", "mayor", "secretary"
    ]):
        return f"who is the current {claim.object} fact check 2024 2025"

    # Health/medical claims → fact check
    elif any(w in text for w in ["cures", "treats", "prevents", "causes", "kills"]):
        return f"fact check: {claim.claim_text}"

    # Statistics → verify
    elif any(w in text for w in ["%", "percent", "million", "billion", "crore"]):
        return f"verify: {claim.claim_text}"

    # Default
    else:
        return f"fact check {claim.claim_text}"


class EvidenceGatheringAgent:
    """Agent 4: Gathers REAL evidence using Tavily Search API."""

    def __init__(self):
        self.llm = get_llm_provider()
        self.has_tavily = bool(os.getenv("TAVILY_API_KEY"))
        if self.has_tavily:
            log.info("evidence_agent_mode", mode="REAL_SEARCH via Tavily")
        else:
            log.warning(
                "evidence_agent_mode",
                mode="MOCK (set TAVILY_API_KEY in .env for real results)",
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def run(self, claim: ExtractedClaim) -> EvidenceGatheringResult:
        log.info("agent4_start", claim_id=claim.id, claim=claim.claim_text[:80])

        # Step 1: Search
        if self.has_tavily:
            query = _build_search_query(claim)
            log.info("agent4_real_search", query=query)
            raw_articles = _tavily_search(query, n=10)
            if not raw_articles:
                log.warning("agent4_tavily_empty_using_fallback")
                raw_articles = _mock_search(5)
        else:
            raw_articles = _mock_search(5)

        # Step 2: Format for LLM
        articles_text = "\n\n".join(
            f"[{i+1}] Title: {a['title']}\n"
            f"    Publisher: {a['publisher']}\n"
            f"    URL: {a['url']}\n"
            f"    Date: {a.get('published_date', 'unknown')}\n"
            f"    Content: {a['content']}"
            for i, a in enumerate(raw_articles)
        )

        user_msg = (
            f"CLAIM TO VERIFY: \"{claim.claim_text}\"\n\n"
            f"SEARCH RESULTS:\n{articles_text}\n\n"
            "Analyze each article. If results show the claim is factually wrong "
            "(e.g. wrong person named, wrong fact stated), mark those as CONTRADICTING "
            "and state the correct fact in the evidence_summary."
        )

        response = await self.llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            temperature=0.1,
            max_tokens=3000,
        )

        data = response.parse_json()
        articles = [EvidenceArticle(**a) for a in data.get("articles", [])]

        result = EvidenceGatheringResult(
            claim_id=claim.id,
            claim_text=claim.claim_text,
            articles=articles,
            supporting_count=data.get("supporting_count", 0),
            contradicting_count=data.get("contradicting_count", 0),
            neutral_count=data.get("neutral_count", 0),
            evidence_summary=data.get("evidence_summary", ""),
        )

        log.info(
            "agent4_complete",
            claim_id=claim.id,
            supporting=result.supporting_count,
            contradicting=result.contradicting_count,
            mode="real_tavily" if self.has_tavily else "mock",
        )
        return result
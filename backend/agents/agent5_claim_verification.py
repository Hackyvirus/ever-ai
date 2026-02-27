"""
Agent 5 – Claim Verification Agent
Verifies claims using ensemble of deterministic scoring + LLM reasoning.
Now handles well-known facts even when evidence is neutral/sparse.
"""
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm_provider import get_llm_provider
from models.schemas import (
    ClaimVerificationResult,
    EvidenceGatheringResult,
    ExtractedClaim,
    VerdictType,
)

log = structlog.get_logger()

SYSTEM_PROMPT = """You are a Claim Verification Agent for a fake news detection system.

Classify the claim as one of:
- "True" – Evidence supports it, OR it is a well-known verifiable fact confirmed by search results.
- "False" – Evidence contradicts it, OR search results show the correct fact is different.
- "Partially True" – Mixed evidence; some parts correct, some wrong.
- "Insufficient Evidence" – Genuinely cannot determine from available evidence.

IMPORTANT RULES:
1. If the evidence summary states the correct fact (e.g. "Narendra Modi IS the Prime Minister"),
   and the claim matches that fact → verdict is "True" with high confidence.
2. If search results confirm a person holds a position, and the claim states that → "True".
3. If search results show a DIFFERENT person holds the position → "False".
4. Do NOT say "Insufficient Evidence" when the evidence_summary actually confirms the claim.
5. Use your world knowledge combined with evidence to give accurate verdicts.

Respond with JSON ONLY:
{
  "claim_id": "string",
  "claim_text": "string",
  "verdict": "True|False|Partially True|Insufficient Evidence",
  "confidence": 0-100,
  "reasoning": "3-4 sentences explaining the verdict clearly, stating correct facts if known",
  "key_evidence": ["url1", "url2"]
}"""


def _deterministic_score(evidence: EvidenceGatheringResult) -> dict:
    """
    Deterministic scoring from evidence counts.
    Combined with LLM verdict for final ensemble decision.
    """
    total = evidence.supporting_count + evidence.contradicting_count + evidence.neutral_count
    if total == 0:
        return {"verdict": "Insufficient Evidence", "confidence": 20}

    support_ratio = evidence.supporting_count / max(total, 1)
    contradict_ratio = evidence.contradicting_count / max(total, 1)

    if evidence.supporting_count >= 3 and support_ratio >= 0.4:
        return {"verdict": "True", "confidence": min(85, int(support_ratio * 100) + 30)}
    elif evidence.contradicting_count >= 3 and contradict_ratio >= 0.4:
        return {"verdict": "False", "confidence": min(85, int(contradict_ratio * 100) + 30)}
    elif evidence.supporting_count >= 1 and evidence.contradicting_count == 0:
        return {"verdict": "True", "confidence": 60}
    elif evidence.contradicting_count >= 1 and evidence.supporting_count == 0:
        return {"verdict": "False", "confidence": 60}
    elif evidence.supporting_count > 0 and evidence.contradicting_count > 0:
        return {"verdict": "Partially True", "confidence": 50}
    else:
        return {"verdict": "Insufficient Evidence", "confidence": 25}


class ClaimVerificationAgent:
    """Agent 5: Verifies claims using ensemble scoring + LLM reasoning."""

    def __init__(self):
        self.llm = get_llm_provider()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def run(
        self,
        claim: ExtractedClaim,
        evidence: EvidenceGatheringResult,
    ) -> ClaimVerificationResult:
        log.info("agent5_start", claim_id=claim.id)

        # Step 1: Deterministic scoring
        det_result = _deterministic_score(evidence)

        # Step 2: Build context for LLM
        top_articles = sorted(
            evidence.articles, key=lambda a: a.relevance_score, reverse=True
        )[:8]

        articles_text = "\n".join(
            f"- [{a.stance.upper()}] {a.publisher}: {a.summary} ({a.url})"
            for a in top_articles
        ) or "No articles retrieved."

        user_msg = (
            f"CLAIM: \"{claim.claim_text}\"\n\n"
            f"EVIDENCE SUMMARY FROM SEARCH: {evidence.evidence_summary}\n\n"
            f"TOP ARTICLES:\n{articles_text}\n\n"
            f"Supporting: {evidence.supporting_count} | "
            f"Contradicting: {evidence.contradicting_count} | "
            f"Neutral: {evidence.neutral_count}\n\n"
            f"Deterministic scoring suggests: {det_result['verdict']} "
            f"(confidence: {det_result['confidence']}%)\n\n"
            "IMPORTANT: If the evidence summary confirms the claim is factually correct "
            "(e.g. confirms a person IS in a position), verdict should be True. "
            "Do not say Insufficient Evidence if the facts are confirmed.\n\n"
            f"Claim ID: {claim.id}"
        )

        response = await self.llm.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_msg,
            temperature=0.1,
            max_tokens=800,
        )

        data = response.parse_json()

        # ── Ensemble logic ──
        llm_verdict = data.get("verdict", "Insufficient Evidence")
        llm_confidence = data.get("confidence", 50)
        det_verdict = det_result["verdict"]
        det_confidence = det_result["confidence"]

        verdict_rank = {
            "True": 0,
            "False": 1,
            "Partially True": 2,
            "Insufficient Evidence": 3,
        }

        llm_rank = verdict_rank.get(llm_verdict, 3)
        det_rank = verdict_rank.get(det_verdict, 3)

        # If LLM says True/False with high confidence (>65%), trust it
        # Otherwise blend with deterministic
        if llm_confidence >= 65 and llm_verdict in ("True", "False"):
            final_verdict = llm_verdict
            final_confidence = round(0.7 * llm_confidence + 0.3 * det_confidence, 1)
        elif llm_verdict == det_verdict:
            # Both agree — higher confidence
            final_verdict = llm_verdict
            final_confidence = round(min(90, (llm_confidence + det_confidence) / 2 + 10), 1)
        else:
            # Disagree — take more conservative (higher rank = more cautious)
            if llm_rank <= det_rank:
                final_verdict = llm_verdict
            else:
                final_verdict = det_verdict
            final_confidence = round((llm_confidence + det_confidence) / 2, 1)

        data["verdict"] = final_verdict
        data["confidence"] = final_confidence
        data["claim_id"] = claim.id
        data["claim_text"] = claim.claim_text
        data.setdefault(
            "key_evidence",
            [a.url for a in top_articles[:3] if a.relevance_score > 0.1]
        )

        result = ClaimVerificationResult(**data)
        log.info(
            "agent5_complete",
            claim_id=claim.id,
            verdict=result.verdict,
            confidence=result.confidence,
            llm_said=llm_verdict,
            det_said=det_verdict,
        )
        return result
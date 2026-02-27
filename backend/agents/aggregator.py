"""
Aggregator Layer
Combines Author, Publisher, and Claim Verification scores into final verdict.
Uses weighted ensemble scoring — deterministic and explainable.

Key improvement: When claims are strongly True/False, that signal dominates.
Unknown author/publisher reduces score but does NOT override clear factual verdicts.
"""
from typing import List
import structlog

from models.schemas import (
    AuthorVerificationResult,
    PublisherVerificationResult,
    ClaimVerificationResult,
    AggregatedResult,
    VerdictType,
)

log = structlog.get_logger()

# Weights — claims evidence is the strongest signal
WEIGHT_AUTHOR    = 0.10   # Reduced: unknown author ≠ false claim
WEIGHT_PUBLISHER = 0.15   # Reduced: unknown publisher ≠ false claim
WEIGHT_CLAIMS    = 0.75   # Increased: actual evidence is most important


def _verdict_to_score(verdict: VerdictType, confidence: float) -> float:
    """Convert verdict + confidence to credibility score (0-100)."""
    base = {
        "True":                  88,
        "Partially True":        58,
        "Insufficient Evidence": 38,
        "False":                 8,
    }.get(verdict, 38)

    # Scale by confidence: high confidence → closer to base, low → toward 50
    weight = confidence / 100.0
    score = base * weight + 50 * (1 - weight)
    return max(0, min(100, score))


def _score_to_verdict(score: float, claim_verdicts: list) -> VerdictType:
    """
    Determine final verdict from score + individual claim verdicts.
    If majority of claims are True → lean True even if score is middling.
    """
    if not claim_verdicts:
        if score >= 70: return "True"
        if score >= 50: return "Partially True"
        if score >= 30: return "Insufficient Evidence"
        return "False"

    # Count claim verdicts
    counts = {"True": 0, "False": 0, "Partially True": 0, "Insufficient Evidence": 0}
    for v in claim_verdicts:
        counts[v] = counts.get(v, 0) + 1

    total = len(claim_verdicts)
    true_ratio  = counts["True"] / total
    false_ratio = counts["False"] / total

    # Strong majority of True claims → True (even with unknown author/publisher)
    if true_ratio >= 0.6 and score >= 55:
        return "True"
    if true_ratio >= 0.8:
        return "True"

    # Strong majority of False claims → False
    if false_ratio >= 0.6 and score < 40:
        return "False"
    if false_ratio >= 0.8:
        return "False"

    # Score-based for mixed cases
    if score >= 72: return "True"
    if score >= 52: return "Partially True"
    if score >= 32: return "Insufficient Evidence"
    return "False"


def _confidence_from_scores(scores: list[float]) -> float:
    """Higher variance in scores = lower confidence."""
    if not scores:
        return 50.0
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    confidence = max(35, min(95, 88 - (variance ** 0.5) * 0.4))
    return round(confidence, 1)


class AggregatorLayer:
    """Combines all agent outputs into a single credibility verdict."""

    def aggregate(
        self,
        author: AuthorVerificationResult,
        publisher: PublisherVerificationResult,
        claim_verifications: List[ClaimVerificationResult],
    ) -> AggregatedResult:
        log.info("aggregator_start", n_claims=len(claim_verifications))

        author_score    = author.credibility_score
        publisher_score = publisher.credibility_score

        # Claims score
        if claim_verifications:
            claim_scores = [
                _verdict_to_score(cv.verdict, cv.confidence)
                for cv in claim_verifications
            ]
            avg_claim_score = sum(claim_scores) / len(claim_scores)
        else:
            avg_claim_score = 38.0

        # Weighted final score
        final_score = round(
            WEIGHT_AUTHOR    * author_score
            + WEIGHT_PUBLISHER * publisher_score
            + WEIGHT_CLAIMS    * avg_claim_score,
            1,
        )

        # Confidence from score spread
        all_scores  = [author_score, publisher_score, avg_claim_score]
        confidence  = _confidence_from_scores(all_scores)

        # Verdict — uses claim verdicts to override pure score when evidence is clear
        claim_verdict_list = [cv.verdict for cv in claim_verifications]
        final_verdict = _score_to_verdict(final_score, claim_verdict_list)

        # Build explanation
        claim_summaries = "; ".join(
            f'"{cv.claim_text[:55]}…" → {cv.verdict} ({cv.confidence:.0f}%)'
            for cv in claim_verifications[:3]
        ) or "No specific claims analyzed."

        # Note about author/publisher if unknown
        source_note = ""
        if author.author_name in ("Unknown/Anonymous",) and publisher.publisher_name in ("Unknown Publisher",):
            source_note = " Note: Source is unverified (no author/publisher), but claim credibility is based primarily on evidence."

        explanation = (
            f"Final credibility score: {final_score}/100. "
            f"Author '{author.author_name}' scored {author_score}/100 "
            f"({'verified journalist' if author.found_in_journalist_db else 'not in journalist database'}). "
            f"Publisher '{publisher.publisher_name}' scored {publisher_score}/100"
            f"{' ⚠️ (known fake news source)' if publisher.in_fake_news_db else ''}. "
            f"Claim evidence: {claim_summaries}.{source_note}"
        )

        result = AggregatedResult(
            final_verdict=final_verdict,
            final_score=final_score,
            confidence=confidence,
            explanation=explanation,
            score_breakdown={
                "author_score":    author_score,
                "author_weight":   WEIGHT_AUTHOR,
                "publisher_score": publisher_score,
                "publisher_weight":WEIGHT_PUBLISHER,
                "claims_score":    round(avg_claim_score, 1),
                "claims_weight":   WEIGHT_CLAIMS,
                "individual_claim_scores": [
                    {
                        "claim":      cv.claim_text[:80],
                        "verdict":    cv.verdict,
                        "confidence": cv.confidence,
                        "score":      round(_verdict_to_score(cv.verdict, cv.confidence), 1),
                    }
                    for cv in claim_verifications
                ],
            },
        )

        log.info(
            "aggregator_complete",
            final_score=final_score,
            verdict=final_verdict,
            confidence=confidence,
            claim_verdicts=claim_verdict_list,
        )
        return result
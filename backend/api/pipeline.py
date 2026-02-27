"""
Pipeline Orchestrator
Coordinates all 5 agents + aggregator for a full analysis run.
"""
import asyncio
import uuid
from datetime import datetime
import structlog

from agents import (
    ClaimExtractionAgent,
    AuthorVerificationAgent,
    PublisherVerificationAgent,
    EvidenceGatheringAgent,
    ClaimVerificationAgent,
    AggregatorLayer,
)
from models.schemas import FullAnalysisResult
from core.llm_provider import get_llm_provider

log = structlog.get_logger()


class AnalysisPipeline:
    """Full analysis pipeline: text in → FullAnalysisResult out."""

    def __init__(self):
        self.agent1 = ClaimExtractionAgent()
        self.agent2 = AuthorVerificationAgent()
        self.agent3 = PublisherVerificationAgent()
        self.agent4 = EvidenceGatheringAgent()
        self.agent5 = ClaimVerificationAgent()
        self.aggregator = AggregatorLayer()

    async def run(self, text: str, query_id: str | None = None) -> FullAnalysisResult:
        if not query_id:
            query_id = str(uuid.uuid4())

        log.info("pipeline_start", query_id=query_id)
        started_at = datetime.utcnow()

        result = FullAnalysisResult(
            query_id=query_id,
            input_text=text,
            created_at=started_at,
            status="processing",
            llm_provider=get_llm_provider().provider_name,
        )

        try:
            # ── Step 1: Extract Claims (required for everything else)
            log.info("pipeline_step", step=1, name="claim_extraction")
            extraction = await self.agent1.run(text)
            result.claim_extraction = extraction

            # ── Step 2 + 3: Author & Publisher Verification (run in parallel)
            log.info("pipeline_step", step="2+3", name="author+publisher")
            author_task = self.agent2.run(
                extraction.author_name, extraction.publisher_domain
            )
            publisher_task = self.agent3.run(
                extraction.publisher_name, extraction.publisher_domain
            )
            author_result, publisher_result = await asyncio.gather(
                author_task, publisher_task
            )
            result.author_verification = author_result
            result.publisher_verification = publisher_result

            # ── Step 4: Evidence Gathering (one per claim, in parallel)
            log.info("pipeline_step", step=4, name="evidence_gathering")
            claims_to_process = extraction.claims[:5]  # Cap at 5 claims for MVP
            evidence_tasks = [self.agent4.run(claim) for claim in claims_to_process]
            evidence_results = await asyncio.gather(*evidence_tasks)
            result.evidence_gathering = list(evidence_results)

            # ── Step 5: Claim Verification (one per claim+evidence pair, in parallel)
            log.info("pipeline_step", step=5, name="claim_verification")
            verification_tasks = [
                self.agent5.run(claim, evidence)
                for claim, evidence in zip(claims_to_process, evidence_results)
            ]
            verification_results = await asyncio.gather(*verification_tasks)
            result.claim_verifications = list(verification_results)

            # ── Aggregation
            log.info("pipeline_step", step="agg", name="aggregation")
            aggregated = self.aggregator.aggregate(
                author_result, publisher_result, list(verification_results)
            )
            result.aggregated = aggregated

            result.status = "completed"
            log.info(
                "pipeline_complete",
                query_id=query_id,
                verdict=aggregated.final_verdict,
                score=aggregated.final_score,
                duration_s=(datetime.utcnow() - started_at).total_seconds(),
            )

        except Exception as e:
            log.error("pipeline_error", query_id=query_id, error=str(e))
            result.status = "failed"
            raise

        return result

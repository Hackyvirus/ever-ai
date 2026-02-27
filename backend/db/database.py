"""Database connection and helpers."""
import os
import json
from typing import AsyncGenerator
import asyncpg
import structlog

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://fakeshield:password@localhost:5432/fakeshield_db",
        ).replace("postgresql+asyncpg://", "postgresql://").replace("+asyncpg", "")
        _pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
        log.info("db_pool_created")
    return _pool


async def init_db():
    """Run init.sql to create tables."""
    pool = await get_pool()
    try:
        with open("db/init.sql") as f:
            sql = f.read()
        async with pool.acquire() as conn:
            await conn.execute(sql)
        log.info("db_initialized")
    except Exception as e:
        log.warning("db_init_skip", reason=str(e))


async def save_analysis(result) -> None:
    """Persist a FullAnalysisResult to the database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Insert query
        await conn.execute(
            """
            INSERT INTO user_queries
              (id, input_text, status, created_at, completed_at, final_verdict, final_score, final_explanation)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (id) DO UPDATE SET
              status=EXCLUDED.status,
              completed_at=EXCLUDED.completed_at,
              final_verdict=EXCLUDED.final_verdict,
              final_score=EXCLUDED.final_score,
              final_explanation=EXCLUDED.final_explanation
            """,
            result.query_id,
            result.input_text[:5000],
            result.status,
            result.created_at,
            None if result.status != "completed" else result.created_at,
            result.aggregated.final_verdict if result.aggregated else None,
            result.aggregated.final_score if result.aggregated else None,
            result.aggregated.explanation if result.aggregated else None,
        )

        # Insert claims
        if result.claim_extraction:
            for claim in result.claim_extraction.claims:
                await conn.execute(
                    """
                    INSERT INTO extracted_claims
                      (id, query_id, claim_text, claim_type, subject, predicate, object, confidence)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                    ON CONFLICT DO NOTHING
                    """,
                    claim.id,
                    result.query_id,
                    claim.claim_text,
                    claim.claim_type,
                    claim.subject,
                    claim.predicate,
                    claim.object,
                    claim.confidence,
                )

        # Insert credibility scores
        scores_to_insert = []
        if result.author_verification:
            scores_to_insert.append((
                result.query_id, "author",
                result.author_verification.author_name,
                result.author_verification.credibility_score,
                result.author_verification.reasoning,
            ))
        if result.publisher_verification:
            scores_to_insert.append((
                result.query_id, "publisher",
                result.publisher_verification.publisher_name,
                result.publisher_verification.credibility_score,
                result.publisher_verification.reasoning,
            ))
        if result.aggregated:
            scores_to_insert.append((
                result.query_id, "aggregate",
                "overall",
                result.aggregated.final_score,
                result.aggregated.explanation,
            ))

        for qid, stype, name, score, reasoning in scores_to_insert:
            await conn.execute(
                """
                INSERT INTO credibility_scores (query_id, score_type, entity_name, score, reasoning)
                VALUES ($1,$2,$3,$4,$5)
                """,
                qid, stype, name, score, reasoning,
            )

        # Insert evidence
        for ev in result.evidence_gathering:
            for article in ev.articles:
                await conn.execute(
                    """
                    INSERT INTO evidence_sources
                      (query_id, claim_id, url, title, publisher, summary, stance, relevance_score)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                    ON CONFLICT DO NOTHING
                    """,
                    result.query_id,
                    ev.claim_id,
                    article.url,
                    article.title,
                    article.publisher,
                    article.summary,
                    article.stance,
                    article.relevance_score,
                )

    log.info("db_saved", query_id=result.query_id)

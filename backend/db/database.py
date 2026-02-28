"""
EverAI — Database Layer
Stores EVERYTHING: requests, responses, claims, evidence,
verifications, entities, errors, feedback, WhatsApp sessions.
Survives server restarts — loads history back from DB on startup.
"""
from dotenv import load_dotenv
load_dotenv(override=True)

import os
import json
import time
import traceback
from datetime import datetime
from typing import Optional
import asyncpg
import structlog

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


# ─────────────────────────────────────────────────────────────
# Connection pool
# ─────────────────────────────────────────────────────────────

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        db_url = (
            os.getenv("DATABASE_URL", "postgresql://postgres:591081@localhost:5432/everai")
            .replace("postgresql+asyncpg://", "postgresql://")
            .replace("+asyncpg", "")
        )
        _pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10, command_timeout=30)
        log.info("db_pool_created")
    return _pool


# ─────────────────────────────────────────────────────────────
# Init — create all tables
# ─────────────────────────────────────────────────────────────

async def init_db():
    """Create all tables from init.sql."""
    try:
        pool = await get_pool()
        # Try multiple paths for init.sql
        for path in ["db/init.sql", "backend/db/init.sql", "/app/db/init.sql"]:
            if os.path.exists(path):
                with open(path) as f:
                    sql = f.read()
                async with pool.acquire() as conn:
                    await conn.execute(sql)
                log.info("db_initialized", path=path)
                return
        log.warning("db_init_sql_not_found")
    except Exception as e:
        log.warning("db_init_failed", error=str(e))
        raise


# ─────────────────────────────────────────────────────────────
# Save complete analysis — every field, every table
# ─────────────────────────────────────────────────────────────

async def save_analysis(result, source_type: str = "web",
                         whatsapp_from: str = None, language: str = "en",
                         duration_ms: int = None) -> bool:
    """
    Save EVERYTHING from a FullAnalysisResult to the database.
    Returns True on success, False on failure.
    Each table insert is wrapped separately so partial saves still work.
    """
    try:
        pool = await get_pool()
    except Exception as e:
        log.error("db_pool_failed", error=str(e))
        return False

    query_id = result.query_id
    saved_tables = []
    failed_tables = []

    async with pool.acquire() as conn:

        # ── 1. user_queries (main record) ──────────────────
        try:
            # Build full_response JSON — the COMPLETE raw result
            try:
                full_response = json.loads(result.model_dump_json())
            except Exception:
                full_response = {"error": "could not serialize full response"}

            completed_at = datetime.utcnow() if result.status == "completed" else None

            await conn.execute("""
                INSERT INTO user_queries (
                    id, input_text, source_type, language, whatsapp_from,
                    status, created_at, completed_at, duration_ms,
                    final_verdict, final_score, final_confidence,
                    final_explanation, llm_provider, full_response
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                ON CONFLICT (id) DO UPDATE SET
                    status            = EXCLUDED.status,
                    completed_at      = EXCLUDED.completed_at,
                    duration_ms       = EXCLUDED.duration_ms,
                    final_verdict     = EXCLUDED.final_verdict,
                    final_score       = EXCLUDED.final_score,
                    final_confidence  = EXCLUDED.final_confidence,
                    final_explanation = EXCLUDED.final_explanation,
                    full_response     = EXCLUDED.full_response
            """,
                query_id,
                result.input_text[:5000],
                source_type,
                language,
                whatsapp_from,
                result.status,
                result.created_at,
                completed_at,
                duration_ms,
                result.aggregated.final_verdict    if result.aggregated else None,
                result.aggregated.final_score      if result.aggregated else None,
                result.aggregated.confidence       if result.aggregated else None,
                result.aggregated.explanation      if result.aggregated else None,
                getattr(result, 'llm_provider', 'openai'),
                json.dumps(full_response),
            )
            saved_tables.append("user_queries")
        except Exception as e:
            failed_tables.append(f"user_queries: {e}")
            await _log_error(conn, query_id, "db_save", "user_queries_insert", str(e), traceback.format_exc())

        # ── 2. extracted_claims ────────────────────────────
        if result.claim_extraction:
            try:
                for claim in result.claim_extraction.claims:
                    await conn.execute("""
                        INSERT INTO extracted_claims
                            (id, query_id, claim_text, claim_type, subject, predicate, object, confidence)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                        ON CONFLICT (id) DO NOTHING
                    """,
                        claim.id, query_id,
                        claim.claim_text, claim.claim_type,
                        claim.subject, claim.predicate, claim.object,
                        claim.confidence,
                    )
                saved_tables.append("extracted_claims")
            except Exception as e:
                failed_tables.append(f"extracted_claims: {e}")
                await _log_error(conn, query_id, "db_save", "claims_insert", str(e), traceback.format_exc())

        # ── 3. named_entities ──────────────────────────────
        if result.claim_extraction and result.claim_extraction.named_entities:
            try:
                for ent in result.claim_extraction.named_entities:
                    await conn.execute("""
                        INSERT INTO named_entities (query_id, text, label, confidence)
                        VALUES ($1,$2,$3,$4)
                    """,
                        query_id, ent.text, ent.label, ent.confidence,
                    )
                saved_tables.append("named_entities")
            except Exception as e:
                failed_tables.append(f"named_entities: {e}")
                await _log_error(conn, query_id, "db_save", "entities_insert", str(e), traceback.format_exc())

        # ── 4. credibility_scores (author + publisher + aggregate) ──
        try:
            if result.author_verification:
                av = result.author_verification
                await conn.execute("""
                    INSERT INTO credibility_scores
                        (query_id, score_type, entity_name, score, reasoning, flags, raw_data)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                    query_id, "author", av.author_name,
                    av.credibility_score, av.reasoning,
                    av.flags or [],
                    json.dumps(av.model_dump()),
                )

            if result.publisher_verification:
                pv = result.publisher_verification
                await conn.execute("""
                    INSERT INTO credibility_scores
                        (query_id, score_type, entity_name, score, reasoning, flags, raw_data)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                    query_id, "publisher", pv.publisher_name,
                    pv.credibility_score, pv.reasoning,
                    pv.flags or [],
                    json.dumps(pv.model_dump()),
                )

            if result.aggregated:
                agg = result.aggregated
                await conn.execute("""
                    INSERT INTO credibility_scores
                        (query_id, score_type, entity_name, score, reasoning, flags, raw_data)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                    query_id, "aggregate", "overall",
                    agg.final_score, agg.explanation,
                    [],
                    json.dumps(agg.score_breakdown or {}),
                )
            saved_tables.append("credibility_scores")
        except Exception as e:
            failed_tables.append(f"credibility_scores: {e}")
            await _log_error(conn, query_id, "db_save", "scores_insert", str(e), traceback.format_exc())

        # ── 5. evidence_sources ────────────────────────────
        if result.evidence_gathering:
            try:
                for ev in result.evidence_gathering:
                    for article in ev.articles:
                        await conn.execute("""
                            INSERT INTO evidence_sources
                                (query_id, claim_id, url, title, publisher,
                                 published_date, summary, stance, relevance_score)
                            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                            ON CONFLICT DO NOTHING
                        """,
                            query_id, ev.claim_id,
                            article.url, article.title, article.publisher,
                            getattr(article, 'published_date', None),
                            article.summary, article.stance, article.relevance_score,
                        )
                saved_tables.append("evidence_sources")
            except Exception as e:
                failed_tables.append(f"evidence_sources: {e}")
                await _log_error(conn, query_id, "db_save", "evidence_insert", str(e), traceback.format_exc())

        # ── 6. claim_verifications ─────────────────────────
        if result.claim_verifications:
            try:
                for cv in result.claim_verifications:
                    await conn.execute("""
                        INSERT INTO claim_verifications
                            (query_id, claim_id, claim_text, verdict,
                             confidence, reasoning, key_evidence)
                        VALUES ($1,$2,$3,$4,$5,$6,$7)
                        ON CONFLICT DO NOTHING
                    """,
                        query_id, cv.claim_id, cv.claim_text,
                        cv.verdict, cv.confidence, cv.reasoning,
                        cv.key_evidence or [],
                    )
                saved_tables.append("claim_verifications")
            except Exception as e:
                failed_tables.append(f"claim_verifications: {e}")
                await _log_error(conn, query_id, "db_save", "verifications_insert", str(e), traceback.format_exc())

    # Log summary
    if failed_tables:
        log.error("db_save_partial",
                  query_id=query_id,
                  saved=saved_tables,
                  failed=failed_tables)
        return False
    else:
        log.info("db_save_complete",
                 query_id=query_id,
                 tables=saved_tables)
        return True


# ─────────────────────────────────────────────────────────────
# Save feedback
# ─────────────────────────────────────────────────────────────

async def save_feedback(data: dict) -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO feedback
                    (name, email, rating, helpful, what_liked, improve, use_case, language)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
                data.get("name"), data.get("email"),
                data.get("rating"), data.get("helpful"),
                data.get("what_liked"), data.get("improve"),
                data.get("use_case"), data.get("language", "en"),
            )
        log.info("feedback_saved", rating=data.get("rating"))
        return True
    except Exception as e:
        log.error("feedback_save_failed", error=str(e))
        return False


# ─────────────────────────────────────────────────────────────
# Save WhatsApp session
# ─────────────────────────────────────────────────────────────

async def save_whatsapp_session(phone: str, query_id: str,
                                 msg_in: str, msg_out: str,
                                 language: str = "en") -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO whatsapp_sessions
                    (phone_number, query_id, message_in, message_out, language)
                VALUES ($1,$2,$3,$4,$5)
            """,
                phone, query_id, msg_in[:3000], msg_out[:3000], language,
            )
        log.info("wa_session_saved", phone=phone[:10])
        return True
    except Exception as e:
        log.error("wa_session_save_failed", error=str(e))
        return False


# ─────────────────────────────────────────────────────────────
# Load history from DB (survives server restarts)
# ─────────────────────────────────────────────────────────────

async def load_recent_from_db(limit: int = 200) -> list[dict]:
    """
    Load recent analysis results from DB into memory cache on startup.
    This means history survives server restarts.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, input_text, status, created_at, completed_at,
                       final_verdict, final_score, final_confidence,
                       final_explanation, source_type, language,
                       whatsapp_from, full_response
                FROM user_queries
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

        log.info("db_history_loaded", count=len(rows))
        return [dict(r) for r in rows]
    except Exception as e:
        log.warning("db_history_load_failed", error=str(e))
        return []


# ─────────────────────────────────────────────────────────────
# Log errors to DB
# ─────────────────────────────────────────────────────────────

async def log_error_to_db(query_id: str, agent: str,
                           error_type: str, error_msg: str,
                           stack_trace: str = None) -> None:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await _log_error(conn, query_id, agent, error_type, error_msg, stack_trace)
    except Exception:
        pass  # Don't let error logging crash anything


async def _log_error(conn, query_id: str, agent: str,
                     error_type: str, error_msg: str,
                     stack_trace: str = None) -> None:
    """Internal helper — uses existing connection."""
    try:
        await conn.execute("""
            INSERT INTO error_logs (query_id, agent, error_type, error_msg, stack_trace)
            VALUES ($1,$2,$3,$4,$5)
        """,
            query_id, agent, error_type, str(error_msg)[:1000],
            (stack_trace or "")[:5000],
        )
    except Exception:
        pass  # Never crash on error logging


# ─────────────────────────────────────────────────────────────
# Admin queries (for debugging)
# ─────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    """Overall system statistics."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            total     = await conn.fetchval("SELECT COUNT(*) FROM user_queries")
            completed = await conn.fetchval("SELECT COUNT(*) FROM user_queries WHERE status='completed'")
            failed    = await conn.fetchval("SELECT COUNT(*) FROM user_queries WHERE status='failed'")
            verdicts  = await conn.fetch("""
                SELECT final_verdict, COUNT(*) as count
                FROM user_queries WHERE final_verdict IS NOT NULL
                GROUP BY final_verdict ORDER BY count DESC
            """)
            avg_score = await conn.fetchval("SELECT AVG(final_score) FROM user_queries WHERE final_score IS NOT NULL")
            wa_count  = await conn.fetchval("SELECT COUNT(*) FROM user_queries WHERE source_type='whatsapp'")
            errors    = await conn.fetchval("SELECT COUNT(*) FROM error_logs WHERE created_at > NOW() - INTERVAL '24 hours'")
            feedback  = await conn.fetchval("SELECT COUNT(*) FROM feedback")
            avg_rating= await conn.fetchval("SELECT AVG(rating) FROM feedback")

        return {
            "total_queries":     total,
            "completed":         completed,
            "failed":            failed,
            "whatsapp_queries":  wa_count,
            "avg_credibility_score": round(float(avg_score), 1) if avg_score else None,
            "verdict_breakdown": {r["final_verdict"]: r["count"] for r in verdicts},
            "errors_last_24h":   errors,
            "total_feedback":    feedback,
            "avg_feedback_rating": round(float(avg_rating), 1) if avg_rating else None,
        }
    except Exception as e:
        log.error("stats_failed", error=str(e))
        return {"error": str(e)}


async def get_recent_errors(limit: int = 50) -> list[dict]:
    """Get recent errors for debugging."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT query_id, agent, error_type, error_msg, created_at
                FROM error_logs
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]

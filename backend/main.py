"""EverAI – FastAPI Backend (Production Ready)"""
from dotenv import load_dotenv
load_dotenv(override=True)

import os
import uuid
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import get_settings
from models.schemas import AnalyzeRequest, AnalyzeResponse, FullAnalysisResult
from api.pipeline import AnalysisPipeline
from api.feedback import router as feedback_router
from db.database import (
    init_db, save_analysis, load_recent_from_db,
    get_stats, get_recent_errors, log_error_to_db
)
from whatsapp.webhook import router as whatsapp_router

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(__import__("logging"), os.getenv("LOG_LEVEL", "INFO"))
    )
)
log = structlog.get_logger()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
_result_cache: dict[str, FullAnalysisResult] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", provider=settings.llm_provider, env=settings.environment)
    try:
        await init_db()
        # ── Load recent history from DB into memory cache ──
        rows = await load_recent_from_db(limit=200)
        loaded = 0
        for row in rows:
            if row.get("full_response") and row["full_response"] not in ({}, "{}"):
                try:
                    import json
                    raw = row["full_response"]
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    obj = FullAnalysisResult(**data)
                    _result_cache[obj.query_id] = obj
                    loaded += 1
                except Exception:
                    pass  # skip malformed rows
        log.info("startup_cache_loaded", loaded=loaded, total_in_db=len(rows))
    except Exception as e:
        log.warning("startup_db_failed", error=str(e))
    yield
    log.info("shutdown")


app = FastAPI(
    title="EverAI API",
    description="Multi-agent fake news detection — stores everything in PostgreSQL",
    version="2.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp_router, prefix="/webhook", tags=["WhatsApp"])
app.include_router(feedback_router, prefix="/api", tags=["Feedback"])

pipeline = AnalysisPipeline()


# ─────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "app": "EverAI",
        "version": "2.0.0",
        "llm_provider": settings.llm_provider,
        "environment": settings.environment,
        "cache_size": len(_result_cache),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# Admin endpoints (for debugging)
# ─────────────────────────────────────────────────────────────

@app.get("/admin/stats", tags=["Admin"])
async def admin_stats():
    """Live statistics from DB — total queries, verdicts, errors."""
    return await get_stats()


@app.get("/admin/errors", tags=["Admin"])
async def admin_errors(limit: int = 50):
    """Recent errors from DB — useful for debugging."""
    return await get_recent_errors(limit)


@app.get("/admin/cache", tags=["Admin"])
async def admin_cache():
    """What's currently in memory cache."""
    return {
        "cache_size": len(_result_cache),
        "query_ids": list(_result_cache.keys())[-20:],
    }


# ─────────────────────────────────────────────────────────────
# Analysis pipeline
# ─────────────────────────────────────────────────────────────

async def _run_and_save(query_id: str, text: str,
                         source_type: str = "web",
                         whatsapp_from: str = None,
                         language: str = "en"):
    start = time.time()
    try:
        result = await pipeline.run(text, query_id=query_id)
        _result_cache[query_id] = result
        duration_ms = int((time.time() - start) * 1000)
        saved = await save_analysis(
            result,
            source_type=source_type,
            whatsapp_from=whatsapp_from,
            language=language,
            duration_ms=duration_ms,
        )
        if not saved:
            log.error("db_save_failed_for_query", query_id=query_id)
    except Exception as e:
        tb = traceback.format_exc()
        log.error("pipeline_failed", query_id=query_id, error=str(e))
        await log_error_to_db(query_id, "pipeline", type(e).__name__, str(e), tb)
        _result_cache[query_id] = FullAnalysisResult(
            query_id=query_id,
            input_text=text,
            created_at=datetime.utcnow(),
            status="failed",
            error_message=str(e),
        )


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def analyze_async(request: Request, body: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Async analysis — returns immediately, poll for results."""
    query_id = str(uuid.uuid4())
    _result_cache[query_id] = FullAnalysisResult(
        query_id=query_id, input_text=body.text,
        created_at=datetime.utcnow(), status="processing",
    )
    background_tasks.add_task(
        _run_and_save, query_id, body.text,
        getattr(body, 'source_type', 'web'),
        None,
        getattr(body, 'language', 'en'),
    )
    return AnalyzeResponse(query_id=query_id, status="processing",
                           message=f"Poll /api/report/{query_id}")


@app.post("/api/analyze/sync", response_model=FullAnalysisResult, tags=["Analysis"])
@limiter.limit("5/minute")
async def analyze_sync(request: Request, body: AnalyzeRequest):
    """Synchronous analysis — waits for full result."""
    query_id = str(uuid.uuid4())
    start = time.time()
    try:
        result = await pipeline.run(body.text, query_id=query_id)
        _result_cache[query_id] = result
        duration_ms = int((time.time() - start) * 1000)
        saved = await save_analysis(
            result,
            source_type=getattr(body, 'source_type', 'web'),
            language=getattr(body, 'language', 'en'),
            duration_ms=duration_ms,
        )
        if not saved:
            log.error("db_save_failed_sync", query_id=query_id)
        return result
    except Exception as e:
        tb = traceback.format_exc()
        log.error("sync_pipeline_failed", query_id=query_id, error=str(e))
        await log_error_to_db(query_id, "pipeline_sync", type(e).__name__, str(e), tb)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/report/{query_id}", response_model=FullAnalysisResult, tags=["Analysis"])
async def get_report(query_id: str):
    """Get report — checks memory first, then DB."""
    # Check memory cache first (fast)
    result = _result_cache.get(query_id)
    if result:
        return result

    # Fallback: check DB (handles server restarts)
    try:
        from db.database import get_pool
        import json
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT full_response FROM user_queries WHERE id=$1", query_id
            )
        if row and row["full_response"] not in ({}, "{}"):
            raw = row["full_response"]
            data = json.loads(raw) if isinstance(raw, str) else raw
            obj = FullAnalysisResult(**data)
            _result_cache[query_id] = obj  # cache it
            return obj
    except Exception as e:
        log.warning("report_db_lookup_failed", query_id=query_id, error=str(e))

    raise HTTPException(status_code=404, detail="Report not found")


@app.get("/api/history", tags=["Analysis"])
async def get_history(limit: int = 20, source: str = None):
    """History — from memory + DB, deduplicated."""
    # From memory
    mem_results = sorted(
        _result_cache.values(), key=lambda r: r.created_at, reverse=True
    )[:limit]

    return [
        {
            "query_id":      r.query_id,
            "status":        r.status,
            "created_at":    r.created_at.isoformat(),
            "final_verdict": r.aggregated.final_verdict if r.aggregated else None,
            "final_score":   r.aggregated.final_score   if r.aggregated else None,
            "confidence":    r.aggregated.confidence    if r.aggregated else None,
            "source_type":   getattr(r, 'source_type', 'web'),
            "preview":       r.input_text[:120] + ("..." if len(r.input_text) > 120 else ""),
        }
        for r in mem_results
    ]

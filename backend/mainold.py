"""
EverAI – FastAPI Backend
Multi-agent fake news detection system.
"""
from dotenv import load_dotenv
load_dotenv(override=True)
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import get_settings
from models.schemas import AnalyzeRequest, AnalyzeResponse, FullAnalysisResult
from api.pipeline import AnalysisPipeline
from db.database import init_db, save_analysis, get_pool
from whatsapp.webhook import router as whatsapp_router

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(__import__("logging"), os.getenv("LOG_LEVEL", "INFO"))
    )
)
log = structlog.get_logger()

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

# In-memory cache for results (replace with Redis in production)
_result_cache: dict[str, FullAnalysisResult] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", provider=settings.llm_provider, env=settings.environment)
    try:
        await init_db()
    except Exception as e:
        log.warning("db_init_failed", error=str(e))
    yield
    log.info("shutdown")


app = FastAPI(
    title="EverAI API",
    description="Multi-agent fake news detection system",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp_router, prefix="/webhook", tags=["WhatsApp"])


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────
# Analysis Endpoints
# ─────────────────────────────────────────────
pipeline = AnalysisPipeline()


async def _run_analysis(query_id: str, text: str, source_type: str = "web"):
    """Background task: run pipeline and save results."""
    try:
        result = await pipeline.run(text, query_id=query_id)
        _result_cache[query_id] = result
        await save_analysis(result)
    except Exception as e:
        log.error("analysis_failed", query_id=query_id, error=str(e))
        _result_cache[query_id] = FullAnalysisResult(
            query_id=query_id,
            input_text=text,
            created_at=datetime.utcnow(),
            status="failed",
        )


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def analyze(
    request: Request,
    body: AnalyzeRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit news text for analysis.
    Returns query_id immediately; poll /api/report/{id} for results.
    """
    query_id = str(uuid.uuid4())
    log.info("analyze_request", query_id=query_id, text_len=len(body.text))

    # Store pending status immediately
    _result_cache[query_id] = FullAnalysisResult(
        query_id=query_id,
        input_text=body.text,
        created_at=datetime.utcnow(),
        status="processing",
    )

    background_tasks.add_task(_run_analysis, query_id, body.text, body.source_type)

    return AnalyzeResponse(
        query_id=query_id,
        status="processing",
        message=f"Analysis started. Poll /api/report/{query_id} for results.",
    )


@app.post("/api/analyze/sync", response_model=FullAnalysisResult, tags=["Analysis"])
@limiter.limit("5/minute")
async def analyze_sync(request: Request, body: AnalyzeRequest):
    """
    Submit news text for synchronous analysis (waits for result).
    Slower but returns full result in one call.
    """
    query_id = str(uuid.uuid4())
    log.info("analyze_sync_request", query_id=query_id)

    result = await pipeline.run(body.text, query_id=query_id)
    _result_cache[query_id] = result

    try:
        await save_analysis(result)
    except Exception as e:
        log.warning("db_save_failed", error=str(e))

    return result


@app.get("/api/report/{query_id}", response_model=FullAnalysisResult, tags=["Analysis"])
async def get_report(query_id: str):
    """Fetch analysis report by ID."""
    result = _result_cache.get(query_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@app.get("/api/history", tags=["Analysis"])
async def get_history(limit: int = 20):
    """Return recent analyses (from in-memory cache)."""
    recent = sorted(
        _result_cache.values(),
        key=lambda r: r.created_at,
        reverse=True,
    )[:limit]
    return [
        {
            "query_id": r.query_id,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "final_verdict": r.aggregated.final_verdict if r.aggregated else None,
            "final_score": r.aggregated.final_score if r.aggregated else None,
            "preview": r.input_text[:120] + "..." if len(r.input_text) > 120 else r.input_text,
        }
        for r in recent
    ]

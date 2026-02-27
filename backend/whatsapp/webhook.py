"""
WhatsApp Bot – Twilio Integration
Receives WhatsApp messages, runs analysis pipeline, responds with verdict.
"""
import os
import asyncio
import structlog
from fastapi import APIRouter, Form, BackgroundTasks, Request, Response
from twilio.rest import Client
from twilio.request_validator import RequestValidator

from api.pipeline import AnalysisPipeline
from core.config import get_settings

log = structlog.get_logger()
router = APIRouter()
settings = get_settings()
pipeline = AnalysisPipeline()

# In-memory queue to track pending WA analyses
_wa_pending: dict[str, str] = {}  # {from_number: query_id}


def _get_twilio_client() -> Client | None:
    sid = settings.twilio_account_sid
    token = settings.twilio_auth_token
    if not sid or not token or sid.startswith("AC"):
        if sid == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
            return None
    try:
        return Client(sid, token)
    except Exception:
        return None


def _send_whatsapp(to: str, body: str):
    """Send a WhatsApp message via Twilio."""
    client = _get_twilio_client()
    if not client:
        log.warning("twilio_not_configured")
        return
    try:
        client.messages.create(
            from_=settings.twilio_whatsapp_from,
            to=to,
            body=body,
        )
        log.info("whatsapp_sent", to=to)
    except Exception as e:
        log.error("whatsapp_send_error", error=str(e))


async def _analyze_and_respond(from_number: str, text: str):
    """Run full pipeline and send WhatsApp response."""
    try:
        result = await pipeline.run(text)

        if result.aggregated:
            agg = result.aggregated
            verdict = agg.final_verdict
            score = agg.final_score
            confidence = agg.confidence

            # Verdict emoji
            emoji = {"True": "✅", "False": "❌", "Partially True": "⚠️"}.get(
                verdict, "❓"
            )

            # Short reasoning (first 200 chars)
            reasoning = agg.explanation[:200] + "..." if len(agg.explanation) > 200 else agg.explanation

            report_url = f"{settings.frontend_url}/report/{result.query_id}"

            msg = (
                f"🔍 *FakeShield Analysis Complete*\n\n"
                f"{emoji} *Verdict:* {verdict}\n"
                f"📊 *Credibility Score:* {score}/100\n"
                f"🎯 *Confidence:* {confidence:.0f}%\n\n"
                f"📝 *Summary:* {reasoning}\n\n"
                f"🔗 *Full Report:* {report_url}"
            )
        else:
            msg = "❌ Analysis failed. Please try again with a different text."

        _send_whatsapp(from_number, msg)

    except Exception as e:
        log.error("wa_analysis_error", error=str(e))
        _send_whatsapp(
            from_number,
            "❌ An error occurred during analysis. Please try again later.",
        )


@router.post("/whatsapp", tags=["WhatsApp"])
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0"),
):
    """
    Twilio WhatsApp webhook endpoint.
    
    Setup:
    1. Go to Twilio Console → Messaging → WhatsApp Sandbox
    2. Set webhook URL to: https://your-domain.com/webhook/whatsapp
    3. Method: POST
    """
    text = Body.strip()
    log.info("whatsapp_received", from_=From, text_preview=text[:80])

    # Handle commands
    if text.lower() in ["help", "hi", "hello", "start"]:
        response_msg = (
            "👋 Welcome to *FakeShield*!\n\n"
            "Send me any news article text or WhatsApp forward and I'll analyze it for credibility.\n\n"
            "I'll check:\n"
            "• 🖊️ Author credibility\n"
            "• 📰 Publisher credibility\n"
            "• 🔍 Evidence from multiple sources\n"
            "• ✅ Claim verification\n\n"
            "Just paste the news text and send!"
        )
        _send_whatsapp(From, response_msg)
        return Response(content="", media_type="text/xml")

    if len(text) < 20:
        _send_whatsapp(
            From,
            "⚠️ Please send a longer news text (at least 20 characters) for analysis.",
        )
        return Response(content="", media_type="text/xml")

    # Rate limiting per number (simple in-memory)
    if From in _wa_pending:
        _send_whatsapp(
            From,
            "⏳ I'm still analyzing your previous message. Please wait a moment.",
        )
        return Response(content="", media_type="text/xml")

    # Acknowledge immediately
    _send_whatsapp(From, "🔄 *Analyzing your message...*\n\nThis may take 30–60 seconds.")
    _wa_pending[From] = "pending"

    # Run analysis in background
    async def run_and_cleanup():
        try:
            await _analyze_and_respond(From, text)
        finally:
            _wa_pending.pop(From, None)

    background_tasks.add_task(run_and_cleanup)

    return Response(content="", media_type="text/xml")

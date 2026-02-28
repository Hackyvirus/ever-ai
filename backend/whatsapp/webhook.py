"""
WhatsApp Bot – Twilio Integration
Supports any number (not just sandbox owner) with detailed reports.
Language auto-detected from message or set by user.
"""
from dotenv import load_dotenv
load_dotenv(override=True)

import os
import asyncio
import structlog
from fastapi import APIRouter, Form, BackgroundTasks, Request, Response
from twilio.rest import Client

from api.pipeline import AnalysisPipeline
from core.config import get_settings
from db.database import save_analysis, save_whatsapp_session, log_error_to_db

log = structlog.get_logger()
router = APIRouter()
settings = get_settings()
pipeline = AnalysisPipeline()

_pending: dict[str, str] = {}
_user_lang: dict[str, str] = {}  # remember each user's language preference


def _get_twilio_client():
    sid = settings.twilio_account_sid
    token = settings.twilio_auth_token
    if not sid or not token or sid == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        return None
    try:
        return Client(sid, token)
    except Exception as e:
        log.error("twilio_client_error", error=str(e))
        return None


def _send_whatsapp(to: str, body: str):
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
        log.info("whatsapp_sent", to=to[:15])
    except Exception as e:
        log.error("whatsapp_send_error", error=str(e))


def _detect_language(text: str) -> str:
    """Simple language detection from script."""
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    if devanagari > 3:
        # Marathi vs Hindi heuristic — common Marathi words
        marathi_words = ['आहे', 'आहेत', 'आणि', 'करा', 'नाही', 'हे', 'ते', 'काय', 'पण']
        hindi_words = ['है', 'हैं', 'और', 'करें', 'नहीं', 'यह', 'वह', 'क्या', 'लेकिन']
        mr_count = sum(1 for w in marathi_words if w in text)
        hi_count = sum(1 for w in hindi_words if w in text)
        return 'mr' if mr_count >= hi_count else 'hi'
    return 'en'


def _build_whatsapp_response(result, lang: str, report_url: str) -> str:
    """Build detailed WhatsApp response in user's language."""
    if not result.aggregated:
        msgs = {'en':'❌ Analysis failed. Please try again.',
                'hi':'❌ विश्लेषण विफल। कृपया पुनः प्रयास करें।',
                'mr':'❌ विश्लेषण अयशस्वी. कृपया पुन्हा प्रयत्न करा.'}
        return msgs.get(lang, msgs['en'])

    agg = result.aggregated
    verdict = agg.final_verdict
    score = round(agg.final_score, 1)
    confidence = round(agg.confidence, 0)

    emoji = {'True':'✅','False':'❌','Partially True':'⚠️','Insufficient Evidence':'❓'}.get(verdict,'❓')

    # Verdict in user language
    verdict_local = {
        'en': verdict,
        'hi': {'True':'सच ✅','False':'झूठ ❌','Partially True':'आंशिक सच ⚠️','Insufficient Evidence':'अपर्याप्त साक्ष्य ❓'}.get(verdict,verdict),
        'mr': {'True':'खरे ✅','False':'खोटे ❌','Partially True':'अंशतः खरे ⚠️','Insufficient Evidence':'अपुरा पुरावा ❓'}.get(verdict,verdict),
    }.get(lang, verdict)

    # Claim summaries
    claim_lines = []
    for cv in (result.claim_verifications or [])[:3]:
        cv_emoji = {'True':'✅','False':'❌','Partially True':'⚠️','Insufficient Evidence':'❓'}.get(cv.verdict,'❓')
        short_claim = cv.claim_text[:70] + ('…' if len(cv.claim_text)>70 else '')
        short_reason = cv.reasoning[:120] + ('…' if len(cv.reasoning)>120 else '')
        claim_lines.append(f"{cv_emoji} *{short_claim}*\n   {short_reason}")

    # Evidence counts
    ev_lines = []
    for ev in (result.evidence_gathering or [])[:2]:
        ev_lines.append(
            f"• Supporting: {ev.supporting_count} | Contradicting: {ev.contradicting_count}\n"
            f"  {ev.evidence_summary[:100]}…"
        )

    if lang == 'hi':
        msg = (
            f"🔍 *EverAI विश्लेषण पूर्ण*\n\n"
            f"{emoji} *निर्णय:* {verdict_local}\n"
            f"📊 *विश्वसनीयता स्कोर:* {score}/100\n"
            f"🎯 *विश्वास:* {confidence:.0f}%\n\n"
        )
        if claim_lines:
            msg += "*दावे:*\n" + "\n\n".join(claim_lines) + "\n\n"
        if ev_lines:
            msg += "*साक्ष्य:*\n" + "\n".join(ev_lines) + "\n\n"
        msg += f"🔗 *पूरी रिपोर्ट:* {report_url}"

    elif lang == 'mr':
        msg = (
            f"🔍 *EverAI विश्लेषण पूर्ण*\n\n"
            f"{emoji} *निर्णय:* {verdict_local}\n"
            f"📊 *विश्वासार्हता गुण:* {score}/100\n"
            f"🎯 *आत्मविश्वास:* {confidence:.0f}%\n\n"
        )
        if claim_lines:
            msg += "*दावे:*\n" + "\n\n".join(claim_lines) + "\n\n"
        if ev_lines:
            msg += "*पुरावा:*\n" + "\n".join(ev_lines) + "\n\n"
        msg += f"🔗 *संपूर्ण अहवाल:* {report_url}"

    else:  # English
        msg = (
            f"🔍 *EverAI Fact Check Complete*\n\n"
            f"{emoji} *Verdict:* {verdict}\n"
            f"📊 *Credibility Score:* {score}/100\n"
            f"🎯 *Confidence:* {confidence:.0f}%\n\n"
        )
        if claim_lines:
            msg += "*Claims Analyzed:*\n" + "\n\n".join(claim_lines) + "\n\n"
        if ev_lines:
            msg += "*Evidence:*\n" + "\n".join(ev_lines) + "\n\n"
        msg += (
            f"📝 *Summary:* {agg.explanation[:200]}…\n\n"
            f"🔗 *Full Report:* {report_url}"
        )

    return msg


async def _analyze_and_respond(from_number: str, text: str, lang: str):
    result = None
    msg = None
    try:
        result = await pipeline.run(text)
        report_url = f"{settings.frontend_url}/wa-report/{result.query_id}"
        msg = _build_whatsapp_response(result, lang, report_url)
        _send_whatsapp(from_number, msg)
        # Save to DB — pass WhatsApp metadata
        await save_analysis(
            result,
            source_type="whatsapp",
            whatsapp_from=from_number,
            language=lang,
        )
        # Save WhatsApp session log
        await save_whatsapp_session(
            phone=from_number,
            query_id=result.query_id,
            msg_in=text,
            msg_out=msg or "",
            language=lang,
        )
    except Exception as e:
        import traceback
        log.error("wa_analysis_error", error=str(e))
        if result:
            await log_error_to_db(result.query_id, "whatsapp_agent", type(e).__name__, str(e), traceback.format_exc())
        err_msgs = {
            "en": "❌ Error during analysis. Please try again.",
            "hi": "❌ विश्लेषण में त्रुटि। कृपया पुनः प्रयास करें।",
            "mr": "❌ विश्लेषणात त्रुटी. कृपया पुन्हा प्रयत्न करा.",
        }
        _send_whatsapp(from_number, err_msgs.get(lang, err_msgs["en"]))
    finally:
        _pending.pop(from_number, None)


@router.post("/whatsapp", tags=["WhatsApp"])
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0"),
):
    text = Body.strip()
    log.info("whatsapp_received", from_=From[:15], text_preview=text[:60])

    # Detect or recall language
    lang_cmd = text.lower().strip()
    if lang_cmd in ['english', 'en', '/english']:
        _user_lang[From] = 'en'
        _send_whatsapp(From, "✅ Language set to English. Send any news to fact-check!")
        return Response(content="", media_type="text/xml")
    elif lang_cmd in ['hindi', 'हिंदी', 'hi', '/hindi']:
        _user_lang[From] = 'hi'
        _send_whatsapp(From, "✅ भाषा हिंदी में सेट की गई। कोई भी समाचार भेजें!")
        return Response(content="", media_type="text/xml")
    elif lang_cmd in ['marathi', 'मराठी', 'mr', '/marathi']:
        _user_lang[From] = 'mr'
        _send_whatsapp(From, "✅ भाषा मराठीमध्ये सेट केली. कोणतीही बातमी पाठवा!")
        return Response(content="", media_type="text/xml")

    # Auto-detect if no preference stored
    lang = _user_lang.get(From) or _detect_language(text)

    # Help message
    if text.lower() in ['help', 'hi', 'hello', 'start', 'हेलो', 'नमस्ते', 'नमस्कार']:
        help_msg = (
            "👋 *Welcome to EverAI Fact Checker!*\n\n"
            "Send me any:\n"
            "• News article text\n"
            "• WhatsApp forward\n"
            "• Social media post\n\n"
            "I'll check if it's *True, False, or Partially True* using AI.\n\n"
            "🌐 *Language options:*\n"
            "Type *English*, *Hindi* (हिंदी), or *Marathi* (मराठी) to switch language.\n\n"
            "🔍 Just paste news and send!"
        )
        _send_whatsapp(From, help_msg)
        return Response(content="", media_type="text/xml")

    if len(text) < 15:
        msgs = {
            'en':'⚠️ Please send a longer news text (min 15 characters).',
            'hi':'⚠️ कृपया लंबा समाचार टेक्स्ट भेजें (न्यूनतम 15 अक्षर)।',
            'mr':'⚠️ कृपया जास्त बातमी मजकूर पाठवा (किमान 15 अक्षरे).',
        }
        _send_whatsapp(From, msgs.get(lang, msgs['en']))
        return Response(content="", media_type="text/xml")

    if From in _pending:
        msgs = {
            'en':'⏳ Still analyzing your previous message. Please wait.',
            'hi':'⏳ अभी भी आपका पिछला संदेश विश्लेषण हो रहा है।',
            'mr':'⏳ अजूनही तुमचा मागील संदेश विश्लेषण होत आहे.',
        }
        _send_whatsapp(From, msgs.get(lang, msgs['en']))
        return Response(content="", media_type="text/xml")

    # Acknowledge
    ack_msgs = {
        'en':'🔄 *Analyzing your message...*\n\nChecking author, publisher, evidence and claims. This takes 30-60 seconds.',
        'hi':'🔄 *आपका संदेश विश्लेषण हो रहा है...*\n\nलेखक, प्रकाशक, साक्ष्य जाँच रहे हैं। 30-60 सेकंड लगेंगे।',
        'mr':'🔄 *तुमचा संदेश विश्लेषण होत आहे...*\n\nलेखक, प्रकाशक, पुरावा तपासत आहे. 30-60 सेकंद लागतील.',
    }
    _pending[From] = lang
    _send_whatsapp(From, ack_msgs.get(lang, ack_msgs['en']))

    background_tasks.add_task(_analyze_and_respond, From, text, lang)
    return Response(content="", media_type="text/xml")

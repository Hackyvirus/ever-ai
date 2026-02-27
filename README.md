# 🔍 FakeShield – Multi-Agent Fake News Detection System

A production-ready MVP using 5 specialized AI agents to detect fake news, with OpenAI GPT-4o as the default LLM provider — with a provider abstraction layer ready for Gemini and Claude.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Input Layer                         │
│           Web UI  /  WhatsApp Bot  /  REST API              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  FastAPI Orchestrator                         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Agent 1   │  │   Agent 2   │  │   Agent 3   │         │
│  │   Claim     │  │   Author    │  │  Publisher  │         │
│  │ Extraction  │  │Verification │  │Verification │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Agent 4   │  │   Agent 5   │  │  Aggregator │         │
│  │  Evidence   │  │   Claim     │  │    Layer    │         │
│  │  Gathering  │  │Verification │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              PostgreSQL Database                              │
│   user_queries | extracted_claims | credibility_scores       │
│   evidence_sources | claim_verifications                     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone & configure
cp .env.example .env
# Edit .env with your OpenAI API key

# 2. Docker (recommended)
docker-compose up --build

# Frontend → http://localhost:5173
# Backend  → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

## Manual Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## LLM Provider Switching

In `.env`, set `LLM_PROVIDER` to switch providers:

| Provider | Value | Required Key |
|----------|-------|-------------|
| OpenAI (default) | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| Anthropic Claude | `claude` | `ANTHROPIC_API_KEY` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Submit text for analysis |
| `GET`  | `/api/report/{id}` | Fetch full report |
| `GET`  | `/api/history` | Recent analyses |
| `POST` | `/webhook/whatsapp` | Twilio WhatsApp webhook |
| `GET`  | `/health` | Health check |

## WhatsApp Setup

1. Create Twilio account → get WhatsApp sandbox number
2. Set webhook URL to `https://your-domain.com/webhook/whatsapp`
3. Add `TWILIO_*` vars to `.env`
4. Send message to sandbox number to test

## Deployment

```bash
# Production with Docker
docker-compose -f docker-compose.prod.yml up -d

# Or Railway/Render: push repo, set env vars, deploy
```

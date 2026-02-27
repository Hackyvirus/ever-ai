# EverAI Deployment Guide

## Option 1: Docker Compose (Self-hosted / VPS)

```bash
# 1. Clone repo and configure
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY, set DATABASE_URL, TWILIO_* etc.

# 2. Build and start
docker-compose up --build -d

# 3. Check logs
docker-compose logs -f backend

# 4. Access
# Frontend: http://your-server:5173
# Backend API: http://your-server:8000
# API Docs: http://your-server:8000/docs
```

---

## Option 2: Railway (Recommended — Free tier available)

### Backend
1. Go to railway.app → New Project → Deploy from GitHub
2. Select the `backend/` directory
3. Add env vars (OPENAI_API_KEY, DATABASE_URL, etc.)
4. Railway auto-detects Python + uvicorn

### Frontend
1. New Service → GitHub → `frontend/` directory
2. Set build command: `npm run build`
3. Set start command: `npx serve dist`
4. Set `VITE_API_URL` to your backend Railway URL

### Database
1. Add PostgreSQL service in Railway
2. Copy the connection string to `DATABASE_URL`

---

## Option 3: Render

### Backend (Web Service)
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Root dir: `backend`

### Frontend (Static Site)
- Build: `npm install && npm run build`  
- Publish dir: `frontend/dist`
- Set VITE_API_URL env var

### Database
- Use Render PostgreSQL (free tier available)

---

## Option 4: AWS ECS

```bash
# Build images
docker build -t EverAI-backend ./backend
docker build -t EverAI-frontend ./frontend

# Push to ECR
aws ecr create-repository --repository-name EverAI-backend
docker tag EverAI-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/EverAI-backend
docker push <account>.dkr.ecr.<region>.amazonaws.com/EverAI-backend

# Deploy via ECS Task Definition (or use Copilot CLI)
```

---

## WhatsApp Bot Setup

1. Sign up at [twilio.com](https://twilio.com)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Note your sandbox number (e.g., `+14155238886`)
4. Set webhook URL in Twilio:
   - `https://your-backend-domain.com/webhook/whatsapp`
   - Method: `POST`
5. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxx
   TWILIO_AUTH_TOKEN=xxx
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```
6. Test: Send any message to the sandbox number

---

## Switching LLM Providers

```bash
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...

# Gemini (install: pip install google-generativeai)
LLM_PROVIDER=gemini
GEMINI_API_KEY=...

# Claude (install: pip install anthropic)
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a long random string
- [ ] Set `ENVIRONMENT=production`
- [ ] Restrict CORS origins in `main.py`
- [ ] Use strong PostgreSQL password
- [ ] Enable HTTPS (use Let's Encrypt / Cloudflare)
- [ ] Set up backup for PostgreSQL
- [ ] Monitor with Sentry or similar
- [ ] Set `RATE_LIMIT_PER_MINUTE` appropriately

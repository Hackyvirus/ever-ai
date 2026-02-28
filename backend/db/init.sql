-- EverAI PostgreSQL Schema v2
-- Stores everything needed for full audit trail and debugging

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Main query log ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_queries (
    id               VARCHAR(36) PRIMARY KEY,
    input_text       TEXT NOT NULL,
    source_type      VARCHAR(20) DEFAULT 'web',   -- web | whatsapp | api
    language         VARCHAR(5)  DEFAULT 'en',    -- en | hi | mr
    whatsapp_from    VARCHAR(50),                  -- phone number if from WA
    status           VARCHAR(20) DEFAULT 'pending',
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    duration_ms      INTEGER,                      -- how long analysis took
    final_verdict    VARCHAR(30),
    final_score      NUMERIC(5,2),
    final_confidence NUMERIC(5,2),
    final_explanation TEXT,
    llm_provider     VARCHAR(30) DEFAULT 'openai',
    error_message    TEXT,                         -- store error if failed
    full_response    JSONB DEFAULT '{}'            -- complete raw JSON response
);

-- ── Extracted claims ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS extracted_claims (
    id           VARCHAR(36) PRIMARY KEY,
    query_id     VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    claim_text   TEXT NOT NULL,
    claim_type   VARCHAR(50),
    subject      VARCHAR(500),
    predicate    TEXT,
    object       TEXT,
    confidence   NUMERIC(5,2),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Named entities ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS named_entities (
    id           SERIAL PRIMARY KEY,
    query_id     VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    text         VARCHAR(255),
    label        VARCHAR(50),   -- PERSON, ORG, GPE, DATE, etc.
    confidence   NUMERIC(5,2),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Credibility scores ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS credibility_scores (
    id           SERIAL PRIMARY KEY,
    query_id     VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    score_type   VARCHAR(30) NOT NULL,   -- author | publisher | aggregate
    entity_name  VARCHAR(255),
    score        NUMERIC(5,2),
    reasoning    TEXT,
    flags        TEXT[],                  -- array of flag strings
    raw_data     JSONB DEFAULT '{}',      -- full agent output
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Evidence sources ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_sources (
    id              SERIAL PRIMARY KEY,
    query_id        VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    claim_id        VARCHAR(36),
    url             TEXT,
    title           TEXT,
    publisher       VARCHAR(255),
    published_date  VARCHAR(30),
    summary         TEXT,
    stance          VARCHAR(20),   -- supporting | contradicting | neutral
    relevance_score NUMERIC(5,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Claim verifications ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS claim_verifications (
    id           SERIAL PRIMARY KEY,
    query_id     VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    claim_id     VARCHAR(36),
    claim_text   TEXT,
    verdict      VARCHAR(30),
    confidence   NUMERIC(5,2),
    reasoning    TEXT,
    key_evidence TEXT[],           -- array of URLs
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Feedback ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255),
    email        VARCHAR(255),
    rating       INTEGER CHECK (rating BETWEEN 1 AND 5),
    helpful      VARCHAR(20),
    what_liked   TEXT,
    improve      TEXT,
    use_case     TEXT,
    language     VARCHAR(5) DEFAULT 'en',
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── WhatsApp sessions ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id              SERIAL PRIMARY KEY,
    phone_number    VARCHAR(50) NOT NULL,
    query_id        VARCHAR(36) REFERENCES user_queries(id) ON DELETE SET NULL,
    message_in      TEXT,
    message_out     TEXT,
    language        VARCHAR(5) DEFAULT 'en',
    status          VARCHAR(20) DEFAULT 'sent',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Error logs ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS error_logs (
    id           SERIAL PRIMARY KEY,
    query_id     VARCHAR(36),
    agent        VARCHAR(50),    -- which agent failed
    error_type   VARCHAR(100),
    error_msg    TEXT,
    stack_trace  TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_queries_status    ON user_queries(status);
CREATE INDEX IF NOT EXISTS idx_queries_created   ON user_queries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_queries_verdict   ON user_queries(final_verdict);
CREATE INDEX IF NOT EXISTS idx_queries_source    ON user_queries(source_type);
CREATE INDEX IF NOT EXISTS idx_queries_wa        ON user_queries(whatsapp_from) WHERE whatsapp_from IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_claims_query      ON extracted_claims(query_id);
CREATE INDEX IF NOT EXISTS idx_entities_query    ON named_entities(query_id);
CREATE INDEX IF NOT EXISTS idx_scores_query      ON credibility_scores(query_id);
CREATE INDEX IF NOT EXISTS idx_evidence_query    ON evidence_sources(query_id);
CREATE INDEX IF NOT EXISTS idx_evidence_stance   ON evidence_sources(stance);
CREATE INDEX IF NOT EXISTS idx_verif_query       ON claim_verifications(query_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating   ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_wa_phone          ON whatsapp_sessions(phone_number);
CREATE INDEX IF NOT EXISTS idx_errors_query      ON error_logs(query_id);
CREATE INDEX IF NOT EXISTS idx_errors_agent      ON error_logs(agent);

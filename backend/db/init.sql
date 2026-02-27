-- FakeShield PostgreSQL Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS user_queries (
    id VARCHAR(36) PRIMARY KEY,
    input_text TEXT NOT NULL,
    source_type VARCHAR(20) DEFAULT 'web',
    whatsapp_from VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    final_verdict VARCHAR(30),
    final_score NUMERIC(5,2),
    final_explanation TEXT
);

CREATE TABLE IF NOT EXISTS extracted_claims (
    id VARCHAR(36) PRIMARY KEY,
    query_id VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(50),
    subject VARCHAR(255),
    predicate TEXT,
    object TEXT,
    confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS credibility_scores (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    score_type VARCHAR(30) NOT NULL,
    entity_name VARCHAR(255),
    score NUMERIC(5,2),
    reasoning TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence_sources (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    claim_id VARCHAR(36),
    url TEXT,
    title TEXT,
    publisher VARCHAR(255),
    summary TEXT,
    stance VARCHAR(20),
    relevance_score NUMERIC(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS claim_verifications (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(36) REFERENCES user_queries(id) ON DELETE CASCADE,
    claim_id VARCHAR(36),
    verdict VARCHAR(30),
    confidence NUMERIC(5,2),
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_queries_status ON user_queries(status);
CREATE INDEX IF NOT EXISTS idx_queries_created ON user_queries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_claims_query ON extracted_claims(query_id);
CREATE INDEX IF NOT EXISTS idx_scores_query ON credibility_scores(query_id);
CREATE INDEX IF NOT EXISTS idx_evidence_query ON evidence_sources(query_id);

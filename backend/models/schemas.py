"""Shared Pydantic models for all agents and API responses."""
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ─────────────────────────────────────────────
# Agent 1 – Claim Extraction
# ─────────────────────────────────────────────
class NamedEntity(BaseModel):
    text: str
    label: str  # PERSON, ORG, GPE, DATE, etc.
    confidence: float = Field(ge=0, le=1)


class ExtractedClaim(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_text: str
    claim_type: Literal["factual", "opinion", "statistic", "quote"]
    subject: str
    predicate: str
    object: str
    confidence: float = Field(ge=0, le=1)


class ClaimExtractionResult(BaseModel):
    author_name: Optional[str] = None
    publisher_name: Optional[str] = None
    publisher_domain: Optional[str] = None
    claims: List[ExtractedClaim]
    named_entities: List[NamedEntity]
    summary: str
    language: str = "en"


# ─────────────────────────────────────────────
# Agent 2 – Author Verification
# ─────────────────────────────────────────────
class AuthorVerificationResult(BaseModel):
    author_name: str
    credibility_score: float = Field(ge=0, le=100)
    found_in_journalist_db: bool
    known_outlets: List[str] = []
    domain_authority_score: float = Field(ge=0, le=100, default=0)
    public_profile_found: bool = False
    reasoning: str
    flags: List[str] = []  # e.g. ["anonymous", "pseudonym", "low_history"]


# ─────────────────────────────────────────────
# Agent 3 – Publisher Verification
# ─────────────────────────────────────────────
class PublisherVerificationResult(BaseModel):
    publisher_name: str
    domain: Optional[str] = None
    credibility_score: float = Field(ge=0, le=100)
    domain_age_years: Optional[float] = None
    in_fake_news_db: bool = False
    whois_registered: bool = True
    country: Optional[str] = None
    reasoning: str
    flags: List[str] = []  # e.g. ["known_misinformation", "new_domain", "no_whois"]


# ─────────────────────────────────────────────
# Agent 4 – Evidence Gathering
# ─────────────────────────────────────────────
class EvidenceArticle(BaseModel):
    title: str
    url: str
    publisher: str
    published_date: Optional[str] = None
    summary: str
    stance: Literal["supporting", "contradicting", "neutral"]
    relevance_score: float = Field(ge=0, le=1)


class EvidenceGatheringResult(BaseModel):
    claim_id: str
    claim_text: str
    articles: List[EvidenceArticle]
    supporting_count: int
    contradicting_count: int
    neutral_count: int
    evidence_summary: str


# ─────────────────────────────────────────────
# Agent 5 – Claim Verification
# ─────────────────────────────────────────────
VerdictType = Literal["True", "False", "Partially True", "Insufficient Evidence"]


class ClaimVerificationResult(BaseModel):
    claim_id: str
    claim_text: str
    verdict: VerdictType
    confidence: float = Field(ge=0, le=100)
    reasoning: str
    key_evidence: List[str] = []  # URLs of most relevant evidence


# ─────────────────────────────────────────────
# Aggregator
# ─────────────────────────────────────────────
class AggregatedResult(BaseModel):
    final_verdict: VerdictType
    final_score: float = Field(ge=0, le=100, description="Overall credibility 0-100")
    confidence: float = Field(ge=0, le=100)
    explanation: str
    score_breakdown: dict = Field(
        default_factory=dict,
        description="author_weight, publisher_weight, evidence_weight, etc."
    )


# ─────────────────────────────────────────────
# Full Pipeline Result
# ─────────────────────────────────────────────
class FullAnalysisResult(BaseModel):
    query_id: str
    input_text: str
    created_at: datetime
    status: str
    claim_extraction: Optional[ClaimExtractionResult] = None
    author_verification: Optional[AuthorVerificationResult] = None
    publisher_verification: Optional[PublisherVerificationResult] = None
    evidence_gathering: List[EvidenceGatheringResult] = []
    claim_verifications: List[ClaimVerificationResult] = []
    aggregated: Optional[AggregatedResult] = None
    llm_provider: str = "openai"


# ─────────────────────────────────────────────
# API Schemas
# ─────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    source_type: str = "web"


class AnalyzeResponse(BaseModel):
    query_id: str
    status: str
    message: str

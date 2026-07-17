"""
Blue Horseshoe — Core Pydantic Models
All data contracts for the Blue Horseshoe system.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class LifecycleStage(str, Enum):
    T_MINUS_7 = "T-7"
    T_MINUS_2 = "T-2"
    T_MINUS_1 = "T-1"
    T_PLUS_0 = "T+0"
    T_PLUS_1 = "T+1"
    MANUAL = "Manual"


class RunStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETE = "Complete"
    PARTIAL = "Partial"
    FAILED = "Failed"
    STALE = "Stale"


class SignalDirection(str, Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class PacketStatus(str, Enum):
    COMPLETE = "Complete"
    PARTIAL = "Partial"
    FAILED = "Failed"
    STALE = "Stale"


# ─── Market Asset ──────────────────────────────────────────────────────────────

class MarketAsset(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    exchange: Optional[str] = None


class MarketAssetCreate(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    exchange: Optional[str] = None


class MarketAssetResponse(MarketAsset):
    airtable_record_id: str


# ─── Earnings Event ────────────────────────────────────────────────────────────

class EarningsEventCreate(BaseModel):
    ticker: str
    event_date: str   # ISO date string YYYY-MM-DD
    expected_eps: Optional[float] = None
    status: str = "Scheduled"


class EarningsEventResponse(EarningsEventCreate):
    event_id: str
    airtable_record_id: str
    asset_record_id: Optional[str] = None


# ─── Lifecycle Run ─────────────────────────────────────────────────────────────

class LifecycleRunCreate(BaseModel):
    ticker: str
    lifecycle_stage: LifecycleStage
    earnings_event_record_id: Optional[str] = None


class LifecycleRunResponse(BaseModel):
    run_id: str
    ticker: str
    lifecycle_stage: LifecycleStage
    status: RunStatus
    start_time: str
    airtable_record_id: str


# ─── Market Snapshot ──────────────────────────────────────────────────────────

class MarketSnapshot(BaseModel):
    snapshot_id: str
    ticker: str
    price_close: Optional[float] = None
    price_open: Optional[float] = None
    price_high: Optional[float] = None
    price_low: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    data_as_of: str
    provider: str


# ─── Technical Observation ────────────────────────────────────────────────────

class TechnicalObservation(BaseModel):
    observation_id: str
    indicator: str
    value: float
    normalized_text: str


# ─── Signal ───────────────────────────────────────────────────────────────────

class Signal(BaseModel):
    signal_id: str
    signal_type: str
    direction: SignalDirection
    summary: str
    overall_confidence: float = Field(ge=0, le=100)
    source_quality_score: float = Field(ge=0, le=100, default=0)
    evidence_convergence: float = Field(ge=0, le=100, default=0)
    freshness_score: float = Field(ge=0, le=100, default=0)
    extraction_certainty: float = Field(ge=0, le=100, default=0)
    technical_confirmation: float = Field(ge=0, le=100, default=0)
    contradiction_penalty: float = Field(ge=0, le=100, default=0)
    missing_data_penalty: float = Field(ge=0, le=100, default=0)


# ─── Intelligence Packet ──────────────────────────────────────────────────────

class MarketIntelligencePacket(BaseModel):
    """The canonical JSON contract delivered to ARIA StreetSmart."""
    packet_id: str
    ticker: str
    lifecycle_stage: LifecycleStage
    status: PacketStatus
    completeness_score: float = Field(ge=0, le=100)
    packet_digest: str
    generation_time: str
    version: int = 1
    snapshot: Optional[MarketSnapshot] = None
    technical_observations: list[TechnicalObservation] = []
    signals: list[Signal] = []
    artifact_url: Optional[str] = None   # Full packet JSON in Artifact Store
    # Metadata
    run_id: str
    total_cost_usd: float = 0.0
    total_tokens: int = 0


# ─── API Request/Response ─────────────────────────────────────────────────────

class RunPipelineRequest(BaseModel):
    ticker: str
    lifecycle_stage: LifecycleStage = LifecycleStage.MANUAL
    earnings_event_record_id: Optional[str] = None


class RunPipelineResponse(BaseModel):
    run_id: str
    status: RunStatus
    packet_id: Optional[str] = None
    message: str

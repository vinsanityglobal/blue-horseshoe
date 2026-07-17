"""Blue Horseshoe — Earnings Events API Router"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from core.airtable.earnings_events import EarningsEventsService
from core.models import EarningsEventCreate, EarningsEventResponse

router = APIRouter(prefix="/earnings", tags=["Earnings Events"])


@router.post("", response_model=EarningsEventResponse, status_code=201)
def create_earnings_event(event: EarningsEventCreate):
    """Register a new earnings event."""
    svc = EarningsEventsService()
    return svc.create(event)


@router.get("/upcoming", response_model=list[EarningsEventResponse])
def get_upcoming_earnings(days_ahead: int = Query(default=14, ge=1, le=90)):
    """Get all scheduled earnings events in the next N days."""
    svc = EarningsEventsService()
    return svc.get_upcoming(days_ahead=days_ahead)


@router.get("/{ticker}", response_model=list[EarningsEventResponse])
def get_earnings_by_ticker(ticker: str, status: Optional[str] = None):
    """Get earnings events for a specific ticker."""
    svc = EarningsEventsService()
    return svc.get_by_ticker(ticker.upper(), status=status)

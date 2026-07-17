"""Blue Horseshoe — Lifecycle Runs API Router"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from core.airtable.lifecycle_runs import LifecycleRunsService
from core.models import LifecycleRunCreate, LifecycleRunResponse

router = APIRouter(prefix="/runs", tags=["Lifecycle Runs"])


@router.post("", response_model=LifecycleRunResponse, status_code=201)
def create_run(run: LifecycleRunCreate):
    """Create a new lifecycle run record."""
    svc = LifecycleRunsService()
    return svc.create(run)


@router.get("", response_model=list[dict])
def list_recent_runs(
    ticker: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List recent lifecycle runs."""
    svc = LifecycleRunsService()
    return svc.get_recent(ticker=ticker, limit=limit)


@router.get("/{run_id}", response_model=LifecycleRunResponse)
def get_run(run_id: str):
    """Get a lifecycle run by its run ID."""
    svc = LifecycleRunsService()
    run = svc.get_by_run_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run

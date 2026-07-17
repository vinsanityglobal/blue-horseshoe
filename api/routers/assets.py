"""Blue Horseshoe — Market Assets API Router"""
from fastapi import APIRouter, HTTPException
from core.airtable.market_assets import MarketAssetsService
from core.models import MarketAssetCreate, MarketAssetResponse

router = APIRouter(prefix="/assets", tags=["Market Assets"])


@router.post("", response_model=MarketAssetResponse, status_code=201)
def create_asset(asset: MarketAssetCreate):
    """Register a new market asset for tracking."""
    svc = MarketAssetsService()
    return svc.create(asset)


@router.get("", response_model=list[MarketAssetResponse])
def list_assets():
    """List all tracked market assets."""
    svc = MarketAssetsService()
    return svc.list_all()


@router.get("/{ticker}", response_model=MarketAssetResponse)
def get_asset(ticker: str):
    """Get a market asset by ticker symbol."""
    svc = MarketAssetsService()
    asset = svc.get_by_ticker(ticker.upper())
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker.upper()} not found")
    return asset

"""
Blue Horseshoe — Market Assets CRUD
Manages the registry of tracked market assets.
"""
import logging
from typing import Optional
from core.airtable.client import AirtableClient
from core.models import MarketAssetCreate, MarketAssetResponse
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MarketAssetsService:
    def __init__(self):
        self.client = AirtableClient()
        self.table_id = get_settings().table_market_assets

    def create(self, asset: MarketAssetCreate) -> MarketAssetResponse:
        """Create a new market asset. Idempotent — skips if ticker already exists."""
        existing = self.get_by_ticker(asset.ticker)
        if existing:
            logger.info(f"Asset {asset.ticker} already exists: {existing.airtable_record_id}")
            return existing

        fields = {
            "Ticker": asset.ticker.upper(),
            "Company Name": asset.company_name,
        }
        if asset.sector:
            fields["Sector"] = asset.sector
        if asset.exchange:
            fields["Exchange"] = asset.exchange

        record = self.client.create_record(self.table_id, fields)
        return MarketAssetResponse(
            ticker=asset.ticker.upper(),
            company_name=asset.company_name,
            sector=asset.sector,
            exchange=asset.exchange,
            airtable_record_id=record["id"],
        )

    def get_by_ticker(self, ticker: str) -> Optional[MarketAssetResponse]:
        """Fetch a market asset by ticker symbol."""
        formula = f"{{Ticker}} = '{ticker.upper()}'"
        records = self.client.list_records(self.table_id, filter_formula=formula, max_records=1)
        if not records:
            return None
        r = records[0]
        f = r["fields"]
        return MarketAssetResponse(
            ticker=f.get("Ticker", ticker.upper()),
            company_name=f.get("Company Name", ""),
            sector=f.get("Sector"),
            exchange=f.get("Exchange"),
            airtable_record_id=r["id"],
        )

    def list_all(self) -> list[MarketAssetResponse]:
        """List all tracked market assets."""
        records = self.client.list_records(
            self.table_id,
            sort=[{"field": "Ticker", "direction": "asc"}],
            max_records=500,
        )
        results = []
        for r in records:
            f = r["fields"]
            results.append(MarketAssetResponse(
                ticker=f.get("Ticker", ""),
                company_name=f.get("Company Name", ""),
                sector=f.get("Sector"),
                exchange=f.get("Exchange"),
                airtable_record_id=r["id"],
            ))
        return results

    def upsert(self, asset: MarketAssetCreate) -> MarketAssetResponse:
        """Upsert a market asset by ticker."""
        fields = {
            "Ticker": asset.ticker.upper(),
            "Company Name": asset.company_name,
        }
        if asset.sector:
            fields["Sector"] = asset.sector
        if asset.exchange:
            fields["Exchange"] = asset.exchange

        formula = f"{{Ticker}} = '{asset.ticker.upper()}'"
        existing = self.client.list_records(self.table_id, filter_formula=formula, max_records=1)
        if existing:
            record = self.client.update_record(self.table_id, existing[0]["id"], fields)
        else:
            record = self.client.create_record(self.table_id, fields)

        return MarketAssetResponse(
            ticker=asset.ticker.upper(),
            company_name=asset.company_name,
            sector=asset.sector,
            exchange=asset.exchange,
            airtable_record_id=record["id"],
        )

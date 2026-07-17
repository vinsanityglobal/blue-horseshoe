"""
Blue Horseshoe — Earnings Events CRUD
Manages the earnings event calendar for tracked assets.
"""
import logging
import ulid
from typing import Optional
from core.airtable.client import AirtableClient
from core.models import EarningsEventCreate, EarningsEventResponse
from config.settings import get_settings

logger = logging.getLogger(__name__)


class EarningsEventsService:
    def __init__(self):
        self.client = AirtableClient()
        self.table_id = get_settings().table_earnings_events

    def create(self, event: EarningsEventCreate) -> EarningsEventResponse:
        """Create a new earnings event."""
        event_id = str(ulid.new())
        fields = {
            "Event ID": event_id,
            "Ticker": event.ticker.upper(),
            "Event Date": event.event_date + "T00:00:00.000Z",
            "Status": event.status,
        }
        if event.expected_eps is not None:
            fields["Expected EPS"] = event.expected_eps

        record = self.client.create_record(self.table_id, fields)
        return EarningsEventResponse(
            event_id=event_id,
            ticker=event.ticker.upper(),
            event_date=event.event_date,
            expected_eps=event.expected_eps,
            status=event.status,
            airtable_record_id=record["id"],
        )

    def get_by_ticker(self, ticker: str, status: Optional[str] = None) -> list[EarningsEventResponse]:
        """Get all earnings events for a ticker, optionally filtered by status."""
        formula = f"{{Ticker}} = '{ticker.upper()}'"
        if status:
            formula = f"AND({formula}, {{Status}} = '{status}')"
        records = self.client.list_records(
            self.table_id,
            filter_formula=formula,
            sort=[{"field": "Event Date", "direction": "asc"}],
            max_records=50,
        )
        results = []
        for r in records:
            f = r["fields"]
            # Parse date — Airtable returns ISO datetime
            event_date = f.get("Event Date", "")[:10] if f.get("Event Date") else ""
            results.append(EarningsEventResponse(
                event_id=f.get("Event ID", r["id"]),
                ticker=f.get("Ticker", ticker.upper()),
                event_date=event_date,
                expected_eps=f.get("Expected EPS"),
                status=f.get("Status", "Scheduled"),
                airtable_record_id=r["id"],
            ))
        return results

    def get_upcoming(self, days_ahead: int = 14) -> list[EarningsEventResponse]:
        """Get all scheduled earnings events in the next N days."""
        from datetime import datetime, timedelta
        today = datetime.utcnow().strftime("%Y-%m-%d")
        future = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        formula = (
            f"AND({{Status}} = 'Scheduled', "
            f"IS_AFTER({{Event Date}}, '{today}T00:00:00.000Z'), "
            f"IS_BEFORE({{Event Date}}, '{future}T00:00:00.000Z'))"
        )
        records = self.client.list_records(
            self.table_id,
            filter_formula=formula,
            sort=[{"field": "Event Date", "direction": "asc"}],
            max_records=100,
        )
        results = []
        for r in records:
            f = r["fields"]
            event_date = f.get("Event Date", "")[:10] if f.get("Event Date") else ""
            results.append(EarningsEventResponse(
                event_id=f.get("Event ID", r["id"]),
                ticker=f.get("Ticker", ""),
                event_date=event_date,
                expected_eps=f.get("Expected EPS"),
                status=f.get("Status", "Scheduled"),
                airtable_record_id=r["id"],
            ))
        return results

    def update_status(self, record_id: str, status: str) -> dict:
        """Update the status of an earnings event."""
        return self.client.update_record(self.table_id, record_id, {"Status": status})

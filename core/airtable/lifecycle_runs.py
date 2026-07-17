"""
Blue Horseshoe — Lifecycle Runs CRUD
Manages pipeline execution records per asset per lifecycle stage.
Each run is immutable once created — status updates are the only allowed mutation.
"""
import logging
import ulid
from datetime import datetime
from typing import Optional
from core.airtable.client import AirtableClient
from core.models import LifecycleRunCreate, LifecycleRunResponse, RunStatus
from config.settings import get_settings

logger = logging.getLogger(__name__)


class LifecycleRunsService:
    def __init__(self):
        self.client = AirtableClient()
        self.table_id = get_settings().table_lifecycle_runs

    def create(self, run: LifecycleRunCreate) -> LifecycleRunResponse:
        """Create a new lifecycle run record."""
        run_id = str(ulid.new())
        start_time = datetime.utcnow().isoformat() + "Z"
        fields = {
            "Run ID": run_id,
            "Ticker": run.ticker.upper(),
            "Lifecycle Stage": run.lifecycle_stage.value,
            "Status": RunStatus.RUNNING.value,
            "Start Time": start_time,
            "Version": 1,
        }
        if run.earnings_event_record_id:
            fields["Earnings Event Record ID"] = run.earnings_event_record_id

        record = self.client.create_record(self.table_id, fields)
        return LifecycleRunResponse(
            run_id=run_id,
            ticker=run.ticker.upper(),
            lifecycle_stage=run.lifecycle_stage,
            status=RunStatus.RUNNING,
            start_time=start_time,
            airtable_record_id=record["id"],
        )

    def update_status(
        self,
        record_id: str,
        status: RunStatus,
        end_time: Optional[str] = None,
    ) -> dict:
        """Update the status of a lifecycle run."""
        fields = {"Status": status.value}
        if end_time:
            fields["End Time"] = end_time
        elif status in (RunStatus.COMPLETE, RunStatus.FAILED, RunStatus.PARTIAL):
            fields["End Time"] = datetime.utcnow().isoformat() + "Z"
        return self.client.update_record(self.table_id, record_id, fields)

    def get_by_run_id(self, run_id: str) -> Optional[LifecycleRunResponse]:
        """Fetch a lifecycle run by its ULID run_id."""
        formula = f"{{Run ID}} = '{run_id}'"
        records = self.client.list_records(self.table_id, filter_formula=formula, max_records=1)
        if not records:
            return None
        r = records[0]
        f = r["fields"]
        return LifecycleRunResponse(
            run_id=f.get("Run ID", run_id),
            ticker=f.get("Ticker", ""),
            lifecycle_stage=f.get("Lifecycle Stage", "Manual"),
            status=f.get("Status", "Running"),
            start_time=f.get("Start Time", ""),
            airtable_record_id=r["id"],
        )

    def get_recent(self, ticker: Optional[str] = None, limit: int = 20) -> list[dict]:
        """Get recent lifecycle runs, optionally filtered by ticker."""
        formula = f"{{Ticker}} = '{ticker.upper()}'" if ticker else None
        records = self.client.list_records(
            self.table_id,
            filter_formula=formula,
            sort=[{"field": "Start Time", "direction": "desc"}],
            max_records=limit,
        )
        return [{"id": r["id"], **r["fields"]} for r in records]

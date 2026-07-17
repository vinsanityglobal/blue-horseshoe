"""
Blue Horseshoe — Airtable Client
Handles all reads/writes to the Blue Horseshoe Airtable base.
Implements batching (10 records/request), rate-limit retry with exponential backoff,
and idempotency via ULID primary keys.
"""
import time
import httpx
import logging
from typing import Any, Optional
from config.settings import get_settings

logger = logging.getLogger(__name__)

AIRTABLE_API_BASE = "https://api.airtable.com/v0"
MAX_BATCH_SIZE = 10
MAX_RETRIES = 5
BASE_BACKOFF = 1.0  # seconds


class AirtableClient:
    def __init__(self):
        s = get_settings()
        self.pat = s.airtable_pat
        self.base_id = s.airtable_base_id
        self.rate_limit_delay = s.airtable_rate_limit_delay
        self.headers = {
            "Authorization": f"Bearer {self.pat}",
            "Content-Type": "application/json",
        }

    def _url(self, table_id: str) -> str:
        return f"{AIRTABLE_API_BASE}/{self.base_id}/{table_id}"

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Execute an HTTP request with exponential backoff on 429."""
        for attempt in range(MAX_RETRIES):
            try:
                resp = httpx.request(
                    method, url, headers=self.headers, timeout=30, **kwargs
                )
                if resp.status_code == 429:
                    wait = BASE_BACKOFF * (2 ** attempt) + (attempt * 0.1)
                    logger.warning(f"Airtable rate limit hit. Waiting {wait:.1f}s (attempt {attempt+1}/{MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                time.sleep(self.rate_limit_delay)
                return resp.json()
            except httpx.HTTPStatusError as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Airtable request failed after {MAX_RETRIES} attempts: {e}")
                    raise
                time.sleep(BASE_BACKOFF * (2 ** attempt))
        raise RuntimeError(f"Airtable request failed after {MAX_RETRIES} retries")

    def get_record(self, table_id: str, record_id: str) -> dict:
        """Fetch a single record by ID."""
        url = f"{self._url(table_id)}/{record_id}"
        return self._request("GET", url)

    def list_records(
        self,
        table_id: str,
        filter_formula: Optional[str] = None,
        fields: Optional[list[str]] = None,
        max_records: int = 100,
        sort: Optional[list[dict]] = None,
    ) -> list[dict]:
        """List records with optional filtering and sorting. Handles pagination."""
        url = self._url(table_id)
        params: dict[str, Any] = {"maxRecords": max_records}
        if filter_formula:
            params["filterByFormula"] = filter_formula
        if fields:
            params["fields[]"] = fields
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")

        all_records = []
        offset = None
        while True:
            if offset:
                params["offset"] = offset
            data = self._request("GET", url, params=params)
            all_records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset or len(all_records) >= max_records:
                break
        return all_records[:max_records]

    def create_record(self, table_id: str, fields: dict) -> dict:
        """Create a single record."""
        url = self._url(table_id)
        return self._request("POST", url, json={"fields": fields})

    def create_records_batch(self, table_id: str, records: list[dict]) -> list[dict]:
        """Create up to 10 records per batch. Returns all created records."""
        created = []
        for i in range(0, len(records), MAX_BATCH_SIZE):
            batch = records[i:i + MAX_BATCH_SIZE]
            payload = {"records": [{"fields": r} for r in batch]}
            url = self._url(table_id)
            result = self._request("POST", url, json=payload)
            created.extend(result.get("records", []))
        return created

    def update_record(self, table_id: str, record_id: str, fields: dict) -> dict:
        """Patch a single record (partial update)."""
        url = f"{self._url(table_id)}/{record_id}"
        return self._request("PATCH", url, json={"fields": fields})

    def upsert_by_field(self, table_id: str, fields: dict, key_field: str) -> dict:
        """
        Upsert: if a record with fields[key_field] exists, update it.
        Otherwise create it. Uses idempotency via the key_field value.
        """
        key_value = fields.get(key_field)
        if not key_value:
            raise ValueError(f"key_field '{key_field}' not found in fields")

        formula = f"{{{{{{key_field}}}}}} = '{key_value}'"
        existing = self.list_records(table_id, filter_formula=formula, max_records=1)
        if existing:
            record_id = existing[0]["id"]
            return self.update_record(table_id, record_id, fields)
        return self.create_record(table_id, fields)

    def delete_record(self, table_id: str, record_id: str) -> dict:
        """Delete a single record."""
        url = f"{self._url(table_id)}/{record_id}"
        return self._request("DELETE", url)

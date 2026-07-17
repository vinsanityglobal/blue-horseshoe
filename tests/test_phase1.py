import pytest
import os
from fastapi.testclient import TestClient

# Mock environment variables for testing before importing app
os.environ["APP_NAME"] = "Blue Horseshoe Test"
os.environ["APP_VERSION"] = "0.1.0-test"
os.environ["ENVIRONMENT"] = "testing"
os.environ["AIRTABLE_PAT"] = "test_pat"
os.environ["AIRTABLE_BASE_ID"] = "test_base"

# Mock all table IDs
for tbl in [
    "MARKET_ASSETS", "EARNINGS_EVENTS", "LIFECYCLE_RUNS", "SCHEDULED_JOBS",
    "PROVIDER_CALLS", "MARKET_SNAPSHOTS", "TECHNICAL_OBSERVATIONS",
    "RESEARCH_RUNS", "RESEARCH_SOURCES", "SIGNALS", "INTELLIGENCE_PACKETS"
]:
    os.environ[f"TABLE_{tbl}"] = f"tbl_{tbl.lower()}"

from main import app
from config.settings import get_settings

client = TestClient(app)

def test_settings_load_correctly():
    """Test that settings are loaded correctly from environment"""
    s = get_settings()
    assert s.app_name == "Blue Horseshoe Test"
    assert s.environment == "testing"
    assert s.airtable_base_id == "test_base"
    assert s.table_market_assets == "tbl_market_assets"

def test_health_endpoint():
    """Test the health check endpoint returns correct structure"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Blue Horseshoe Test"
    assert data["version"] == "0.1.0-test"
    assert "airtable_base" in data
    assert "provider" in data

def test_api_routes_registered():
    """Test that all expected API routes are registered"""
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    
    # Health
    assert "/api/health" in routes
    
    # Assets
    assert "/api/assets" in routes
    assert "/api/assets/{ticker}" in routes
    
    # Earnings
    assert "/api/earnings" in routes
    assert "/api/earnings/upcoming" in routes
    assert "/api/earnings/{ticker}" in routes
    
    # Runs
    assert "/api/runs" in routes
    assert "/api/runs/{run_id}" in routes

# We won't test the actual Airtable client calls here since they require live network
# or complex mocking. The live smoke tests will verify Airtable connectivity.

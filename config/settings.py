"""
Blue Horseshoe — Configuration
Railway + Airtable operating stack.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- Identity ---
    app_name: str = "Blue Horseshoe"
    app_version: str = "0.1.0"
    environment: str = "production"

    # --- Auth ---
    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # --- Airtable ---
    airtable_pat: str = ""
    airtable_base_id: str = ""

    # --- Airtable Table IDs ---
    table_market_assets: str = ""
    table_earnings_events: str = ""
    table_lifecycle_runs: str = ""
    table_scheduled_jobs: str = ""
    table_provider_calls: str = ""
    table_market_snapshots: str = ""
    table_technical_observations: str = ""
    table_research_runs: str = ""
    table_research_sources: str = ""
    table_signals: str = ""
    table_intelligence_packets: str = ""

    # --- Artifact Storage ---
    artifact_store_type: str = "local"
    artifact_store_path: str = "/tmp/bh_artifacts"
    artifact_store_bucket: str = ""
    artifact_store_key: str = ""
    artifact_store_secret: str = ""
    artifact_store_endpoint: str = ""

    # --- Market Data Providers ---
    provider_primary: str = "yfinance"
    provider_primary_key: str = ""
    provider_fallback: str = "yfinance"
    provider_fallback_key: str = ""

    # --- OpenRouter ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_extraction: str = "google/gemma-3-27b-it"
    model_synthesis: str = "anthropic/claude-3.5-sonnet"
    model_writing: str = "openai/gpt-4o"

    # --- Pipeline ---
    airtable_batch_size: int = 10
    airtable_rate_limit_delay: float = 0.2
    shadow_timeout_seconds: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

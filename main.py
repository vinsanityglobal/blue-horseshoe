"""
Blue Horseshoe — FastAPI Application
Market Intelligence Engine for ARIA StreetSmart.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import get_settings
from api.routers import assets, earnings, runs, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

s = get_settings()

app = FastAPI(
    title=s.app_name,
    version=s.app_version,
    description="Market Intelligence Engine — Blue Horseshoe v0.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routers
app.include_router(health.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(earnings.router, prefix="/api")
app.include_router(runs.router, prefix="/api")


@app.on_event("startup")
async def startup():
    logger.info(f"{s.app_name} v{s.app_version} starting up...")
    logger.info(f"Airtable base: {s.airtable_base_id}")
    logger.info(f"Primary data provider: {s.provider_primary}")
    logger.info(f"Artifact store: {s.artifact_store_type}")

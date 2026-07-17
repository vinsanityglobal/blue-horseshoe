"""Blue Horseshoe — Health Check Router"""
from fastapi import APIRouter
from config.settings import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    s = get_settings()
    return {
        "status": "ok",
        "service": s.app_name,
        "version": s.app_version,
        "airtable_base": s.airtable_base_id,
        "provider": s.provider_primary,
    }

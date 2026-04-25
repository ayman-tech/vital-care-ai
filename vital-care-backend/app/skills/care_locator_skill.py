import logging
from app.services.location_service import LocationService
from app.schemas.chat import NearestCareSuggestion
from app.schemas.urgency import RecommendedProviderType

logger = logging.getLogger(__name__)


class CareLocatorSkill:
    """Finds nearby care options given a provider type and optional location."""

    def __init__(self, location_service: LocationService):
        self.location_service = location_service

    async def run(
        self,
        provider_type: RecommendedProviderType,
        location: dict | None = None,
    ) -> list[NearestCareSuggestion]:
        return await self.location_service.find_nearby_providers(
            provider_type=provider_type,
            location=location,
        )

import logging
from app.schemas.chat import NearestCareSuggestion
from app.schemas.urgency import RecommendedProviderType
from app.prompts.care_locator_prompt import CARE_LOCATOR_PROMPT

logger = logging.getLogger(__name__)


class LocationService:
    """
    LLM-based care locator service.
    Uses the provided location context and provider type to generate
    realistic nearby care suggestions via the LLM.

    TODO: Replace with Google Maps Places API or a real healthcare directory
    when an API key is available. The interface is drop-in compatible.
    """

    def __init__(self, llm=None):
        self._llm = llm

    def _get_llm(self):
        if self._llm is None:
            from app.services.llm_service import get_llm_service
            self._llm = get_llm_service()
        return self._llm

    async def find_nearby_providers(
        self,
        provider_type: RecommendedProviderType,
        location: dict | None = None,
    ) -> list[NearestCareSuggestion]:
        location_description = self._describe_location(location)
        user_message = (
            f"Provider type needed: {provider_type.specialty.replace('_', ' ')}\n"
            f"Reason: {provider_type.reason}\n"
            f"Location: {location_description}"
        )

        llm = self._get_llm()
        raw = await llm.chat_completion_json(
            system_prompt=CARE_LOCATOR_PROMPT,
            user_message=user_message,
            temperature=0.4,
        )

        suggestions = []
        for item in raw.get("suggestions", []):
            if not isinstance(item, dict):
                continue
            try:
                note = item.get("note", "")
                suggestions.append(
                    NearestCareSuggestion(
                        name=item.get("name", ""),
                        type=item.get("type", provider_type.specialty),
                        address=item.get("address", ""),
                        distance=item.get("distance"),
                        phone=item.get("phone"),
                        source=f"ai_suggested — {note}" if note else "ai_suggested",
                    )
                )
            except Exception as e:
                logger.warning("Skipping malformed care suggestion: %s", e)

        return suggestions

    def _describe_location(self, location: dict | None) -> str:
        if not location:
            return "Location not provided"

        parts = []
        city = location.get("city")
        state = location.get("state")
        country = location.get("country")
        lat = location.get("latitude")
        lng = location.get("longitude")

        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if country:
            parts.append(country)

        description = ", ".join(parts) if parts else ""

        if lat and lng:
            coords = f"coordinates: {lat:.4f}, {lng:.4f}"
            description = f"{description} ({coords})" if description else coords

        return description or "Location not provided"


def get_location_service() -> LocationService:
    return LocationService()

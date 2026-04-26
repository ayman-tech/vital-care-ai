import json
import re
import logging
from datetime import datetime, timezone

from app.services.llm_service import LLMService, get_llm_service
from app.services.location_service import LocationService, get_location_service
from app.schemas.wellbeing import (
    WellbeingChatRequest, WellbeingChatResponse,
    AgentData, EscalationSummary, MoodPoint, StressPoint, TagEntry, SeverityLevel,
)
from app.models.wellbeing import WellbeingSession, WellbeingMessage
from app.prompts.wellbeing_system_prompt import WELLBEING_SYSTEM_PROMPT
from app.schemas.urgency import RecommendedProviderType

logger = logging.getLogger(__name__)

_AGENT_DATA_RE = re.compile(r"<!--AGENT_DATA\s*([\s\S]*?)\s*AGENT_DATA-->")

# Crisis tags that immediately raise severity to CRITICAL regardless of LLM output
_CRISIS_TAGS = {"#self-harm-risk", "#crisis", "#suicidal-ideation", "#hopelessness"}

_TAG_SEVERITY_MAP = {
    "crisis": {"#self-harm-risk", "#crisis", "#suicidal-ideation", "#hopelessness"},
    "moderate": {"#depression-signs", "#burnout", "#emotional-numbness", "#anxiety",
                 "#financial-stress", "#food-insecurity", "#housing-stress",
                 "#sleep-deprivation", "#social-isolation", "#loneliness"},
}


def _classify_tag(tag: str) -> str:
    tag = tag.lower()
    if tag in _TAG_SEVERITY_MAP["crisis"]:
        return "critical"
    if tag in _TAG_SEVERITY_MAP["moderate"]:
        return "moderate"
    return "low"


def _parse_agent_data(raw_response: str) -> tuple[str, AgentData | None]:
    """Split visible text from embedded AGENT_DATA block."""
    match = _AGENT_DATA_RE.search(raw_response)
    if not match:
        visible = raw_response.strip()
        return visible, None

    visible = _AGENT_DATA_RE.sub("", raw_response).strip()
    try:
        data = json.loads(match.group(1))
        return visible, AgentData(
            tags=data.get("tags", []),
            severity=data.get("severity", "LOW"),
            mood_score=int(data.get("mood_score", 5)),
            stress_score=int(data.get("stress_score", 5)),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
    except Exception as e:
        logger.warning("Failed to parse AGENT_DATA: %s", e)
        return visible, None


def _get_top_tags(tags_dict: dict, n: int = 5) -> list[TagEntry]:
    """Sort tags by weighted score (crisis=3x, moderate=2x, low=1x)."""
    weight = {"critical": 3, "moderate": 2, "low": 1}
    scored = []
    for tag, info in tags_dict.items():
        sev = info.get("severity", "low")
        scored.append((tag, info.get("count", 1), sev, info.get("count", 1) * weight.get(sev, 1)))
    scored.sort(key=lambda x: x[3], reverse=True)
    return [TagEntry(tag=t, count=c, severity=s) for t, c, s, _ in scored[:n]]


def _extract_key_moments(messages: list[WellbeingMessage], n: int = 3) -> list[str]:
    """Return the n most significant user messages (longest, as proxy for key moments)."""
    user_msgs = [m.content for m in messages if m.role == "user" and len(m.content) > 30]
    user_msgs.sort(key=len, reverse=True)
    return user_msgs[:n]


class WellbeingAgent:
    """
    Student-focused mental health companion agent.

    Implements the full wellbeing skill: consent protocol, mood/stress/tag tracking,
    severity assessment, escalation pipeline, and Diagnosis Agent handoff.
    """

    def __init__(self, llm: LLMService, location_service: LocationService):
        self.llm = llm
        self.location_service = location_service

    # ------------------------------------------------------------------ #
    #  Main chat entry point                                               #
    # ------------------------------------------------------------------ #

    async def run(
        self,
        request: WellbeingChatRequest,
        session: WellbeingSession,
        messages: list[WellbeingMessage],
    ) -> WellbeingChatResponse:

        # Build conversation history for the LLM
        # messages already includes the current user message (added by the route before calling agent)
        history = [{"role": m.role, "content": m.content} for m in messages]

        raw_response = await self.llm.chat_with_history(
            system_prompt=WELLBEING_SYSTEM_PROMPT,
            messages=history,
            json_mode=False,
            temperature=0.7,
            max_tokens=1000,
        )

        visible_text, agent_data = _parse_agent_data(raw_response)

        # Update session state from agent_data
        severity = self._update_session_state(session, agent_data, request.message)

        # Check for crisis tags even if LLM didn't flag CRITICAL
        if agent_data and any(t in _CRISIS_TAGS for t in agent_data.tags):
            severity = "CRITICAL"
            session.severity = "CRITICAL"

        # Escalate if CRITICAL
        if severity == "CRITICAL" and not session.escalated:
            escalation = await self._run_escalation(session, messages, location=None)
            return WellbeingChatResponse(
                response=visible_text,
                session_id=session.id,
                severity=severity,
                agent_data=agent_data,
                escalated=True,
                escalation_payload=escalation.model_dump() if escalation else None,
                status="escalated",
            )

        return WellbeingChatResponse(
            response=visible_text,
            session_id=session.id,
            severity=severity,
            agent_data=agent_data,
            status="active",
        )

    # ------------------------------------------------------------------ #
    #  Panic button — immediate escalation                                 #
    # ------------------------------------------------------------------ #

    async def handle_panic(
        self,
        session: WellbeingSession,
        messages: list[WellbeingMessage],
        location: dict | None = None,
    ) -> EscalationSummary:
        session.severity = "CRITICAL"
        session.escalated = True
        session.escalation_timestamp = datetime.now(timezone.utc)
        return await self._run_escalation(session, messages, location, trigger="PANIC_BUTTON")

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _update_session_state(
        self, session: WellbeingSession, agent_data: AgentData | None, user_message: str
    ) -> SeverityLevel:
        if not agent_data:
            return session.severity  # type: ignore

        now = datetime.now(timezone.utc).isoformat()

        # Update mood / stress history
        mood_hist = session.mood_history
        mood_hist.append(MoodPoint(timestamp=now, score=agent_data.mood_score).model_dump())
        session.mood_history = mood_hist

        stress_hist = session.stress_history
        stress_hist.append(StressPoint(timestamp=now, score=agent_data.stress_score).model_dump())
        session.stress_history = stress_hist

        # Update tags
        tags = session.tags
        for tag in agent_data.tags:
            tag = tag.lower()
            if tag not in tags:
                tags[tag] = {"count": 0, "lastSeen": now, "severity": _classify_tag(tag)}
            tags[tag]["count"] += 1
            tags[tag]["lastSeen"] = now
        session.tags = tags

        # Update severity (never downgrade within a session)
        severity_rank = {"LOW": 1, "MODERATE": 2, "CRITICAL": 3}
        new_severity = agent_data.severity
        if severity_rank.get(new_severity, 1) > severity_rank.get(session.severity, 1):
            session.severity = new_severity
            sev_log = session.severity_log
            sev_log.append(new_severity)
            session.severity_log = sev_log

        return session.severity  # type: ignore

    async def _run_escalation(
        self,
        session: WellbeingSession,
        messages: list[WellbeingMessage],
        location: dict | None,
        trigger: str = "CRITICAL_SEVERITY",
    ) -> EscalationSummary:
        session.escalated = True
        session.escalation_timestamp = datetime.now(timezone.utc)

        mood_timeline = [MoodPoint(**p) for p in session.mood_history]
        stress_timeline = [StressPoint(**p) for p in session.stress_history]
        severity_prog = session.severity_log or ["CRITICAL"]
        top_tags = _get_top_tags(session.tags)
        key_moments = _extract_key_moments(messages)

        # Compute session duration
        if messages:
            start = messages[0].created_at
            now = datetime.now(timezone.utc)
            duration = int((now - start.replace(tzinfo=timezone.utc)).total_seconds() / 60)
        else:
            duration = 0

        # Hand off to Diagnosis Agent for nearby mental health providers
        nearby_providers = await self._find_mental_health_providers(session, location)

        return EscalationSummary(
            session_id=session.id,
            duration_minutes=duration,
            mood_timeline=mood_timeline,
            stress_timeline=stress_timeline,
            severity_progression=severity_prog,
            top_tags=top_tags,
            key_moments=key_moments,
            nearby_providers=nearby_providers,
        )

    async def _find_mental_health_providers(
        self, session: WellbeingSession, location: dict | None
    ) -> list[dict]:
        """Call CareLocatorSkill via location service for mental health providers."""
        try:
            provider_type = RecommendedProviderType(
                specialty="psychiatrist",
                reason="Mental health crisis — student needs immediate support.",
            )
            suggestions = await self.location_service.find_nearby_providers(
                provider_type=provider_type,
                location=location,
            )
            return [s.model_dump() for s in suggestions]
        except Exception as e:
            logger.error("Error finding mental health providers: %s", e)
            return []


def get_wellbeing_agent() -> WellbeingAgent:
    return WellbeingAgent(
        llm=get_llm_service(),
        location_service=get_location_service(),
    )

import json
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.models.database import Base


class WellbeingSession(Base):
    __tablename__ = "wellbeing_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    consent_given = Column(Boolean, default=False)
    severity = Column(String, default="LOW")   # LOW | MODERATE | CRITICAL
    escalated = Column(Boolean, default=False)
    escalation_timestamp = Column(DateTime, nullable=True)
    university = Column(String, default="UMD")
    insurance_plan = Column(String, nullable=True)

    # JSON-serialized lists/dicts stored as Text
    _mood_history = Column("mood_history", Text, default="[]")
    _stress_history = Column("stress_history", Text, default="[]")
    _tags = Column("tags", Text, default="{}")
    _severity_log = Column("severity_log", Text, default="[]")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("WellbeingMessage", back_populates="session",
                            order_by="WellbeingMessage.created_at")

    # JSON property helpers
    @property
    def mood_history(self) -> list:
        return json.loads(self._mood_history or "[]")

    @mood_history.setter
    def mood_history(self, value: list):
        self._mood_history = json.dumps(value)

    @property
    def stress_history(self) -> list:
        return json.loads(self._stress_history or "[]")

    @stress_history.setter
    def stress_history(self, value: list):
        self._stress_history = json.dumps(value)

    @property
    def tags(self) -> dict:
        return json.loads(self._tags or "{}")

    @tags.setter
    def tags(self, value: dict):
        self._tags = json.dumps(value)

    @property
    def severity_log(self) -> list:
        return json.loads(self._severity_log or "[]")

    @severity_log.setter
    def severity_log(self, value: list):
        self._severity_log = json.dumps(value)


class WellbeingMessage(Base):
    __tablename__ = "wellbeing_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("wellbeing_sessions.id"), nullable=False)
    role = Column(String, nullable=False)      # user | assistant
    content = Column(Text, nullable=False)     # visible text only (AGENT_DATA stripped)
    severity_at_time = Column(String, nullable=True)
    mood_score = Column(String, nullable=True)
    stress_score = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("WellbeingSession", back_populates="messages")

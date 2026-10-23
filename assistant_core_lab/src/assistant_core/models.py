"""Shared request and response contracts for the assistant service."""

from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """Supported routing results and the service's unknown-answer result."""

    GREETING = "greeting"
    FEE = "fee"
    OFFICE = "office"
    RULE = "rule"
    UNKNOWN = "unknown"


class Message(BaseModel):
    """Validated input to AssistantService.handle."""

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = "local"


class Source(BaseModel):
    """Reference to a handbook rule used in an answer."""

    id: str
    title: str


class Response(BaseModel):
    """Service answer with routing, provenance and fallback status."""

    answer: str
    intent: Intent
    sources: list[Source] = Field(default_factory=list)
    degraded: bool = False

"""Single service entry point shared by the CLI and future HTTP/UI adapters."""

import logging
from time import perf_counter

from assistant_core.config import Settings
from assistant_core.errors import ConfigError, InvalidRequest, ProviderError
from assistant_core.knowledge import KnowledgeBase, load_knowledge
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import Responder, StubLLMResponder, TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits, tuition

log = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, settings: Settings, knowledge: KnowledgeBase, responder: Responder):
        self.settings = settings
        self.knowledge = knowledge
        self.responder = responder
        self.fallback = TemplateResponder()

    def handle(self, msg: Message) -> Response:
        """Handle a validated message without exposing provider failures."""
        start = perf_counter()
        intent = route(msg.text, {office.name.casefold() for office in self.knowledge.offices})
        response = self._dispatch(intent, msg.text)
        log.info(
            "handled",
            extra={
                "intent": response.intent.value,
                "latency_ms": round((perf_counter() - start) * 1000, 3),
                "session": msg.session_id,
                "degraded": response.degraded,
            },
        )
        return response

    def _dispatch(self, intent: Intent, text: str) -> Response:
        if intent is Intent.GREETING:
            return Response(answer="Hello! I can help with offices, fees and rules.", intent=intent)
        if intent is Intent.FEE:
            return self._fee(text)
        if intent is Intent.OFFICE:
            office = self.knowledge.find_office(text)
            if office is not None:
                return Response(answer=f"{office.name}: room {office.room}, open {office.hours}.", intent=intent)
            return self._unknown()
        return self._rule(text)

    def _fee(self, text: str) -> Response:
        try:
            credits, retake = parse_credits(text)
            amount = tuition(
                credits,
                retake,
                self.settings.credit_rate_vnd,
                self.settings.retake_multiplier,
                self.settings.max_credits,
            )
        except InvalidRequest as error:
            return Response(answer=str(error), intent=Intent.FEE)
        return Response(answer=f"Your tuition is {amount:,} VND.", intent=Intent.FEE)

    def _rule(self, text: str) -> Response:
        rule = self.knowledge.find_rule(text)
        if rule is None:
            return self._unknown()
        sources = [Source(id=rule.id, title=rule.title)]
        try:
            answer = self.responder.explain(text, rule)
        except ProviderError:
            # Provider error messages can contain credentials or request text.
            log.warning("provider failed; using template fallback")
            return Response(
                answer=self.fallback.explain(text, rule), intent=Intent.RULE, sources=sources, degraded=True
            )
        return Response(answer=answer, intent=Intent.RULE, sources=sources)

    @staticmethod
    def _unknown() -> Response:
        return Response(answer="Sorry, I don't know that yet.", intent=Intent.UNKNOWN)


def create_service(settings: Settings) -> AssistantService:
    """Load knowledge and compose the offline Lab 3 provider once at startup."""
    if settings.llm_provider != "stub":
        raise ConfigError("Unsupported LLM_PROVIDER. Lab 3 supports only 'stub'.")
    knowledge = load_knowledge(settings.data_dir)
    return AssistantService(settings, knowledge, StubLLMResponder())

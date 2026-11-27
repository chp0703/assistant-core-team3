"""Single service entry point shared by the CLI and HTTP/UI adapters."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

from assistant_core.config import Settings
from assistant_core.errors import ConfigError, DataError, InvalidRequest, ProviderError
from assistant_core.guard import INJECTION_REPLY, PRIVATE_REPLY, is_private_request, looks_like_injection
from assistant_core.knowledge import KnowledgeBase, load_knowledge
from assistant_core.llm import LLM, make_llm
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import make_index
from assistant_core.rag.types import RagResult
from assistant_core.responder import Responder, StubLLMResponder, TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits, tuition

log = logging.getLogger(__name__)
_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_KB_DIR = Path("data/kb")
_SUPPORTED_RAG_PROVIDERS = frozenset({"stub", "template", "ollama", "openai"})


def _to_public_response(result: RagResult) -> Response:
    """Map an internal RagResult to the preserved Lab 03-05 public Response."""
    return Response(
        answer=result.answer,
        intent=result.intent,
        sources=list(result.sources),
        degraded=result.degraded,
    )


def _resolve_kb_dir(settings: Settings) -> Path:
    """Resolve the Markdown KB directory, keeping kb_dir aligned with overridden data_dir."""
    kb_dir = settings.kb_dir
    if kb_dir == _DEFAULT_KB_DIR and settings.data_dir != _DEFAULT_DATA_DIR:
        kb_dir = settings.data_dir / "kb"
    if not kb_dir.is_dir():
        raise DataError(f"Knowledge base directory not found: {kb_dir}")
    return kb_dir


def _build_rag_llm(settings: Settings) -> LLM | None:
    """Build the configured LLM adapter or return None for retrieval-only mode."""
    if settings.llm_provider == "template":
        return None
    if settings.llm_provider not in _SUPPORTED_RAG_PROVIDERS:
        raise ConfigError(f"Unsupported LLM_PROVIDER: {settings.llm_provider!r}.")
    try:
        return make_llm(
            settings.llm_provider,
            settings.llm_model,
            settings.llm_base_url,
            settings.llm_api_key,
            settings.llm_timeout_s,
        )
    except ProviderError as error:
        raise ConfigError(str(error)) from error


class AssistantService:
    def __init__(
        self,
        settings: Settings,
        knowledge: KnowledgeBase,
        responder: Responder,
        rag: RagAnswerer | None = None,
    ):
        self.settings = settings
        self.knowledge = knowledge
        self.responder = responder
        self.fallback = TemplateResponder()
        self.rag = rag

    def handle(self, msg: Message) -> Response:
        """Handle a validated message without exposing provider failures."""
        response, _ = self.handle_with_rag_result(msg)
        return response

    def handle_with_rag_result(self, msg: Message) -> tuple[Response, RagResult | None]:
        """Handle a message and return both the public Response and optional RagResult metadata."""
        start = perf_counter()
        response, rag_result = self._execute(msg.text)
        log.info(
            "handled",
            extra={
                "intent": response.intent.value,
                "latency_ms": round((perf_counter() - start) * 1000, 3),
                "degraded": response.degraded,
            },
        )
        return response, rag_result

    def _execute(self, text: str) -> tuple[Response, RagResult | None]:
        refusal = None
        if looks_like_injection(text):
            refusal = INJECTION_REPLY
        elif self.rag is not None and is_private_request(text):
            refusal = PRIVATE_REPLY

        if refusal is not None:
            rag_result = RagResult(
                answer=refusal,
                intent=Intent.UNKNOWN,
                path="abstain",
                confidence=0.0,
            )
            return _to_public_response(rag_result), rag_result

        intent = route(text, {office.name.casefold() for office in self.knowledge.offices})
        return self._dispatch(intent, text)

    def _dispatch(self, intent: Intent, text: str) -> tuple[Response, RagResult | None]:
        if intent is Intent.GREETING:
            return Response(answer="Hello! I can help with offices, fees and rules.", intent=intent), None
        if intent is Intent.FEE:
            return self._fee(text), None
        if intent is Intent.OFFICE:
            office = self.knowledge.find_office(text)
            if office is not None:
                return Response(answer=f"{office.name}: room {office.room}, open {office.hours}.", intent=intent), None
            return self._unknown(), None
        if self.rag is not None:
            rag_result = self.rag.answer(text)
            return _to_public_response(rag_result), rag_result
        return self._rule(text), None

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
    """Load knowledge and compose the assistant service once at startup."""
    if not settings.rag_enabled:
        if settings.llm_provider != "stub":
            raise ConfigError("Unsupported LLM_PROVIDER. Lab 3 supports only 'stub'.")
        knowledge = load_knowledge(settings.data_dir)
        return AssistantService(settings, knowledge, StubLLMResponder())

    llm = _build_rag_llm(settings)
    knowledge = load_knowledge(settings.data_dir)
    kb_dir = _resolve_kb_dir(settings)
    chunks = load_folder(kb_dir)
    if not chunks:
        raise DataError(f"No knowledge base documents found in {kb_dir}.")
    try:
        index = make_index(settings.retrieval_kind, chunks)
    except KeyError as error:
        raise ConfigError(f"Unsupported RETRIEVAL_KIND: {settings.retrieval_kind!r}.") from error
    rag = RagAnswerer(
        index=index,
        llm=llm,
        min_score=settings.retrieval_min_score,
        prompt_version=settings.prompt_version,
    )
    return AssistantService(settings, knowledge, StubLLMResponder(), rag=rag)

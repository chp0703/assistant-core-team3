"""Answer from retrieved evidence, abstaining before any unsupported generation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.guard import PRIVATE_REPLY, is_private_request
from assistant_core.models import Intent, Source
from assistant_core.rag.types import RagResult

if TYPE_CHECKING:
    from assistant_core.llm import LLM
    from assistant_core.rag.index import Index

log = logging.getLogger("assistant_core.rag")
ESCALATE_MSG = (
    "I'm not confident I can answer that from the official documents. "
    "Please contact the Training Office (room I.101) or ask your academic advisor."
)


class RagAnswerer:
    """Return internal metadata; tool_runner must validate arguments before execution."""

    def __init__(
        self,
        index: Index,
        llm: LLM | None = None,
        min_score: float = 2.0,
        k: int = 3,
        prompt_version: str = "answer_v1",
        retries: int = 1,
        tool_runner: Callable[[str], str | None] | None = None,
    ):
        self.index, self.llm, self.min_score, self.k = index, llm, min_score, k
        self.prompt_version, self.retries, self.tool_runner = prompt_version, retries, tool_runner

    def answer(self, question: str) -> RagResult:
        if is_private_request(question):
            return RagResult(answer=PRIVATE_REPLY, intent=Intent.UNKNOWN, path="abstain", confidence=0.0)
        hits = self.index.search(question, self.k)
        if not hits or hits[0].score < self.min_score:
            return RagResult(
                answer=ESCALATE_MSG, intent=Intent.UNKNOWN, path="abstain", escalate=True, confidence=0.0,
            )
        top = hits[0].chunk
        fallback = RagResult(
            answer=f"{top.title}: {top.text}", intent=Intent.RULE,
            sources=(Source(id=top.id, title=top.title),), path="retrieval",
        )
        if self.llm is None:
            return fallback

        # Keep privacy, abstain and retrieval usable before the Part D dependency merges.
        from assistant_core.llm import build_prompt, parse_draft

        sources = {hit.chunk.id: Source(id=hit.chunk.id, title=hit.chunk.title) for hit in hits}
        try:
            prompt = build_prompt(question, hits, self.prompt_version)
        except ProviderError:
            log.warning("prompt unavailable; using retrieval fallback")
            return replace(fallback, degraded=True)

        for attempt in range(self.retries + 1):
            try:
                raw = self.llm.complete(prompt)
                if self.tool_runner is not None:
                    try:
                        result = self.tool_runner(raw)
                    except InvalidRequest as exc:
                        return RagResult(answer=str(exc), intent=Intent.FEE, path="tool", degraded=True)
                    if result is not None:
                        return RagResult(answer=result, intent=Intent.FEE, path="tool")
                draft = parse_draft(raw, set(sources))
                if draft.abstain:
                    return RagResult(
                        answer=ESCALATE_MSG, intent=Intent.UNKNOWN, path="abstain",
                        escalate=True, confidence=draft.confidence,
                    )
                return RagResult(
                    answer=draft.answer, intent=Intent.RULE,
                    sources=tuple(sources[source_id] for source_id in draft.source_ids),
                    path="llm", confidence=draft.confidence,
                )
            except ProviderError:
                log.warning("llm attempt %d failed", attempt + 1)
        return replace(fallback, degraded=True)

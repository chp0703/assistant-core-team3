"""LLM adapters and structured output validation for Lab 06 Part D.

The default stub is offline. Retry and retrieval fallback belong to RagAnswerer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from assistant_core.errors import ProviderError

if TYPE_CHECKING:
    from assistant_core.rag.index import Hit

PROMPTS = Path(__file__).parent / "prompts"


class LLM(Protocol):
    name: str

    def complete(self, prompt: str) -> str: ...


class AnswerDraft(BaseModel):
    """Validated model output; confidence is not a probability of correctness."""

    answer: str = Field(max_length=800)
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    abstain: bool = False


def build_prompt(question: str, hits: list[Hit], version: str = "answer_v1") -> str:
    """Render a packaged prompt without interpreting placeholders in input data."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", version):
        raise ProviderError("invalid prompt version")
    try:
        template = (PROMPTS / f"{version}.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProviderError("prompt template unavailable") from exc

    sources = "\n".join(f"[{h.chunk.id}] {h.chunk.title}: {h.chunk.text}" for h in hits)
    values = {"{sources}": sources, "{question}": question}
    return re.sub(r"\{sources\}|\{question\}", lambda match: values[match.group()], template)


def parse_draft(raw: str, allowed_ids: set[str]) -> AnswerDraft:
    """Validate a JSON object, its schema and the retrieved-source citation set."""
    try:
        draft = AnswerDraft.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as exc:
        # Do not expose model output, prompts or credentials in error messages.
        raise ProviderError(f"invalid structured output: {type(exc).__name__}") from exc

    if not draft.abstain and (not draft.source_ids or not set(draft.source_ids) <= allowed_ids):
        raise ProviderError("answer cites sources that were not retrieved")
    return draft


class StubLLM:
    """Deterministically quote the first source, for offline tests and evaluation."""

    name = "stub"

    def __init__(self, fail: bool = False, garbage: bool = False):
        self.fail, self.garbage = fail, garbage

    def complete(self, prompt: str) -> str:
        if self.fail:
            raise ProviderError("stub provider unavailable")
        if self.garbage:
            return "Sure! Here is a great answer without any JSON."

        # Search only the source block: a question cannot introduce its own source.
        _, marker, remainder = prompt.partition("\nSOURCES:\n")
        sources = remainder.partition("\nQUESTION:")[0] if marker else ""
        match = re.match(r"\[([^\]\r\n]+)\] ([^\r\n]+?): ([^\r\n]+)", sources.strip())
        if not match:
            return AnswerDraft(answer="", confidence=0.0, abstain=True).model_dump_json()

        first_sentence = re.split(r"(?<=[.!?])\s+", match.group(3))[0]
        answer = f"According to {match.group(2)}: {first_sentence}"
        return AnswerDraft(
            answer=" ".join(answer.split()[:79])[:800],
            source_ids=[match.group(1)],
            confidence=0.7,
        ).model_dump_json()


class OllamaLLM:
    """Optional adapter for a local Ollama chat endpoint."""

    name = "ollama"

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434", timeout_s: float = 30):
        self.model, self.base_url = model, base_url.rstrip("/")
        self._http = httpx.Client(timeout=timeout_s)

    def complete(self, prompt: str) -> str:
        try:
            response = self._http.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0},
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
            raise ProviderError(f"ollama failed: {type(exc).__name__}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("ollama returned invalid message content")
        return content

    def close(self) -> None:
        self._http.close()


class OpenAICompatibleLLM:
    """Optional adapter matching the instructor's chat-completions interface."""

    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", timeout_s: float = 20):
        self.model, self.base_url = model, base_url.rstrip("/")
        self._http = httpx.Client(timeout=timeout_s, headers={"Authorization": f"Bearer {api_key}"})

    def complete(self, prompt: str) -> str:
        try:
            response = self._http.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
            raise ProviderError(f"provider failed: {type(exc).__name__}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("provider returned invalid message content")
        return content

    def close(self) -> None:
        self._http.close()


def make_llm(provider: str, model: str, base_url: str | None, api_key: str | None, timeout_s: float) -> LLM:
    """Construct a provider; stub never requires credentials or a network call."""
    if provider == "stub":
        return StubLLM()
    if provider == "ollama":
        return OllamaLLM(model, base_url or "http://localhost:11434", timeout_s)
    if provider == "openai":
        if not api_key or not api_key.strip():
            raise ProviderError("LLM_API_KEY required for provider 'openai'")
        return OpenAICompatibleLLM(api_key, model, base_url or "https://api.openai.com/v1", timeout_s)
    raise ProviderError(f"unknown LLM provider {provider!r}")

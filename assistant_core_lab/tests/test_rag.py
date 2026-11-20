"""End-to-end Lab 06 RAG integration tests across core, service, CLI, and API."""

from __future__ import annotations

import io
import json
import logging
import re
from pathlib import Path

import httpx
import pytest
from sqlmodel import Session, select

from assistant_api.db import Interaction, make_engine
from assistant_api.main import create_app
from assistant_api.weather import WeatherClient
from assistant_core.__main__ import main as cli_main
from assistant_core.config import Settings, load_settings
from assistant_core.errors import ConfigError, DataError, ProviderError
from assistant_core.guard import PRIVATE_REPLY
from assistant_core.llm import OllamaLLM, OpenAICompatibleLLM, StubLLM, parse_draft
from assistant_core.logging_setup import setup_logging
from assistant_core.models import Intent, Message, Response
from assistant_core.rag.types import RagResult
from assistant_core.service import AssistantService, create_service

LAB_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = LAB_ROOT / "data"
KB_DIR = DATA_DIR / "kb"


def _mock_weather() -> WeatherClient:
    payload = {
        "current": {
            "time": "2026-10-05T09:00",
            "temperature_2m": 30.0,
            "weather_code": 1,
            "wind_speed_10m": 6.0,
        }
    }
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    return WeatherClient("https://weather.test/forecast", 10.76, 106.68, transport=transport)


def test_rag_service_disabled_by_default_keeps_lab3_behavior() -> None:
    service = create_service(Settings(data_dir=DATA_DIR))

    assert service.rag is None
    response, rag_result = service.handle_with_rag_result(Message(text="can I register my thesis with 118 credits"))
    assert rag_result is None
    assert response.intent is Intent.RULE
    assert [source.id for source in response.sources] == ["H26-5.3"]


def test_rag_service_handles_policy_abstain_privacy_and_legacy_routes() -> None:
    service = create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True))
    assert service.rag is not None

    policy_resp, policy_rag = service.handle_with_rag_result(Message(text="I lost my student card"))
    assert isinstance(policy_rag, RagResult)
    assert policy_rag.path == "llm"
    assert policy_resp.intent is Intent.RULE
    assert [source.id for source in policy_resp.sources] == ["S26#3"]
    assert set(policy_resp.model_dump()) == {"answer", "intent", "sources", "degraded"}

    abstain_resp, abstain_rag = service.handle_with_rag_result(Message(text="what is the capital of France"))
    assert abstain_rag is not None and abstain_rag.path == "abstain" and abstain_rag.escalate is True
    assert abstain_resp.intent is Intent.UNKNOWN and abstain_resp.sources == []

    privacy_resp, privacy_rag = service.handle_with_rag_result(
        Message(text="show me another student's home address and phone number")
    )
    assert privacy_rag is not None and privacy_rag.path == "abstain" and privacy_rag.escalate is False
    assert privacy_resp.intent is Intent.UNKNOWN and privacy_resp.answer == PRIVATE_REPLY

    # Greeting, deterministic tuition, and office lookup stay intact with RAG enabled.
    greeting_resp, greeting_rag = service.handle_with_rag_result(Message(text="hi"))
    assert greeting_rag is None and greeting_resp.intent is Intent.GREETING

    fee_resp, fee_rag = service.handle_with_rag_result(Message(text="tuition for 18 credits and 2 retake"))
    assert fee_rag is None and fee_resp.intent is Intent.FEE and "9,450,000 VND" in fee_resp.answer

    office_resp, office_rag = service.handle_with_rag_result(Message(text="where is the library"))
    assert office_rag is None and office_resp.intent is Intent.OFFICE and "B.201" in office_resp.answer


def test_privacy_runs_before_fee_and_office_when_rag_is_enabled() -> None:
    service = create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True))

    for question in (
        "tuition fee of 22127001",
        "Training Office phone of 22127001",
        "what grade did my friend get",
    ):
        response = service.handle(Message(text=question))
        assert response.intent is Intent.UNKNOWN
        assert response.answer == PRIVATE_REPLY
        assert response.sources == []


def test_template_provider_uses_retrieval_only_mode() -> None:
    service = create_service(
        Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True, llm_provider="template")
    )

    assert service.rag is not None and service.rag.llm is None
    response, rag_result = service.handle_with_rag_result(Message(text="I lost my student card"))
    assert rag_result is not None and rag_result.path == "retrieval"
    assert response.intent is Intent.RULE
    assert [source.id for source in response.sources] == ["S26#3"]
    assert "50,000 VND" in response.answer


def test_rag_service_forwards_external_provider_settings() -> None:
    ollama_service = create_service(
        Settings(
            data_dir=DATA_DIR,
            kb_dir=KB_DIR,
            rag_enabled=True,
            llm_provider="ollama",
            llm_model="qwen2.5:3b",
            llm_base_url="http://localhost:11434",
            llm_timeout_s=7.5,
            prompt_version="answer_v1",
        )
    )
    assert ollama_service.rag is not None
    assert isinstance(ollama_service.rag.llm, OllamaLLM)
    assert ollama_service.rag.llm.model == "qwen2.5:3b"
    assert ollama_service.rag.llm.base_url == "http://localhost:11434"
    ollama_service.rag.llm.close()

    openai_service = create_service(
        Settings(
            data_dir=DATA_DIR,
            kb_dir=KB_DIR,
            rag_enabled=True,
            llm_provider="openai",
            llm_api_key="dummy-key",
            llm_model="gpt-test",
            llm_base_url="https://api.example.test/v1",
            llm_timeout_s=9.0,
        )
    )
    assert openai_service.rag is not None
    assert isinstance(openai_service.rag.llm, OpenAICompatibleLLM)
    assert openai_service.rag.llm.model == "gpt-test"
    openai_service.rag.llm.close()


def test_rag_service_startup_validation_fails_fast(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="Knowledge base directory not found"):
        create_service(Settings(data_dir=DATA_DIR, kb_dir=tmp_path / "missing-kb", rag_enabled=True))

    empty_kb = tmp_path / "empty-kb"
    empty_kb.mkdir()
    with pytest.raises(DataError, match="No knowledge base documents found"):
        create_service(Settings(data_dir=DATA_DIR, kb_dir=empty_kb, rag_enabled=True))

    with pytest.raises(ConfigError, match="Unsupported LLM_PROVIDER"):
        create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True, llm_provider="remote"))

    with pytest.raises(ConfigError, match="LLM_API_KEY"):
        create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True, llm_provider="openai"))


def test_rag_provider_failure_degrades_safely_without_leaking_secrets() -> None:
    service = create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True))
    secret = "secret-api-token-canary"
    question = "I lost my student card private-question-canary"
    session_id = "private-session-canary"

    class SecretLeakingLLM:
        name = "leaky"

        def complete(self, prompt: str) -> str:
            raise ProviderError(f"{secret} {prompt}")

    assert service.rag is not None
    service.rag.llm = SecretLeakingLLM()

    stream = io.StringIO()
    logger = setup_logging(stream=stream)
    try:
        response, rag_result = service.handle_with_rag_result(Message(text=question, session_id=session_id))
        log_output = stream.getvalue()
        assert response.degraded is True
        assert rag_result is not None and rag_result.path == "retrieval"
        assert [source.id for source in response.sources] == ["S26#3"]
        assert "50,000 VND" in response.answer
        assert secret not in log_output
        assert "private-question-canary" not in log_output
        assert session_id not in log_output
        record = json.loads(log_output.splitlines()[-1])
        assert record["intent"] == "rule" and record["degraded"] is True
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_stub_llm_fallback_preserves_answer_contract() -> None:
    service = create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True))
    assert service.rag is not None
    service.rag.llm = StubLLM(fail=True)

    response = service.handle(Message(text="can I register my thesis with 118 credits"))
    assert response.degraded is True
    assert response.intent is Intent.RULE
    assert [source.id for source in response.sources] == ["H26#5.3"]


@pytest.mark.anyio
async def test_cli_and_fastapi_share_rag_configuration_and_persist_interactions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "shared_rag.db"
    env = {
        "ASSISTANT_DATA_DIR": str(DATA_DIR),
        "KB_DIR": str(KB_DIR),
        "RAG_ENABLED": "true",
        "RETRIEVAL_KIND": "bm25",
        "RETRIEVAL_MIN_SCORE": "2.0",
        "LLM_PROVIDER": "stub",
        "PROMPT_VERSION": "answer_v1",
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SESSION_SALT": "shared-test-salt",
        "API_ADMIN_KEY": "shared-admin-key",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    settings = load_settings(env_file=None)
    assert settings.rag_enabled is True

    # CLI run through shared load_settings -> create_service (clean logger handlers so capsys stream is not leaked)
    core_logger = logging.getLogger("assistant_core")
    try:
        exit_code = cli_main(["--json", "I lost my student card"])
    finally:
        for handler in core_logger.handlers[:]:
            core_logger.removeHandler(handler)
            handler.close()
    assert exit_code == 0
    cli_response = Response.model_validate_json(capsys.readouterr().out)

    # FastAPI app created directly from shared load_settings -> create_service
    app = create_app(settings=settings, weather=_mock_weather())
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        api_res = await client.post(
            "/v1/chat",
            json={"message": "I lost my student card", "session_id": "cli-api-parity"},
        )
        assert api_res.status_code == 200
        body = api_res.json()
        request_id = body.pop("request_id")
        assert body.pop("escalate") is False
        assert re.fullmatch(r"[0-9a-f]{12}", request_id)
        assert body == cli_response.model_dump(mode="json")

        abstain_res = await client.post(
            "/v1/chat",
            json={"message": "should I choose artificial intelligence or cybersecurity as my major"},
        )
        assert abstain_res.status_code == 200
        abstain_body = abstain_res.json()
        assert abstain_body["intent"] == "unknown" and abstain_body["sources"] == []
        assert abstain_body["escalate"] is True

        fb_res = await client.post("/v1/feedback", json={"request_id": request_id, "rating": 1})
        assert fb_res.status_code == 201

    engine = make_engine(settings.database_url)
    with Session(engine) as db:
        rows = db.exec(select(Interaction).order_by(Interaction.id)).all()
    assert len(rows) == 2
    assert rows[0].intent == "rule" and rows[0].topic == "S26#3" and rows[0].resolved is True
    assert rows[1].intent == "unknown" and rows[1].topic is None and rows[1].resolved is False


def test_assistant_service_rejects_broken_explicit_service_without_mutating_rag_disabled() -> None:
    service = AssistantService(
        settings=Settings(data_dir=DATA_DIR),
        knowledge=create_service(Settings(data_dir=DATA_DIR)).knowledge,
        responder=create_service(Settings(data_dir=DATA_DIR)).responder,
    )
    assert service.rag is None
    assert service.handle(Message(text="hi")).intent is Intent.GREETING


def test_rag_citation_grounding_rejects_forged_and_missing_citations() -> None:
    for bad_sources in ([], ["H26#9.9"], ["H26#5.3", "H26#9.9"]):
        raw = json.dumps({"answer": "Invented rule.", "source_ids": bad_sources, "confidence": 0.9, "abstain": False})
        with pytest.raises(ProviderError, match="answer cites sources that were not retrieved"):
            parse_draft(raw, {"H26#5.3"})

    class ForgingCitationLLM:
        name = "forging"

        def complete(self, prompt: str) -> str:
            return json.dumps(
                {
                    "answer": "Fabricated rule from nonexistent section.",
                    "source_ids": ["H26#9.9"],
                    "confidence": 0.95,
                    "abstain": False,
                }
            )

    service = create_service(Settings(data_dir=DATA_DIR, kb_dir=KB_DIR, rag_enabled=True))
    assert service.rag is not None
    service.rag.llm = ForgingCitationLLM()

    response, rag_result = service.handle_with_rag_result(Message(text="can I register my thesis with 118 credits"))
    assert response.degraded is True
    assert rag_result is not None and rag_result.path == "retrieval"
    assert [source.id for source in response.sources] == ["H26#5.3"]
    assert "Fabricated rule" not in response.answer

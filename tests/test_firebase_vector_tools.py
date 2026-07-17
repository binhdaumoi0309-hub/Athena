import asyncio
from types import SimpleNamespace

import pytest

from hanoi_heart_assistant.agents.price_agent import service_price_agent
from hanoi_heart_assistant.tools import firebase_vector_tools as vector_tools


def test_build_vector_chunks_includes_records_and_web_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSPITAL_VECTOR_CHUNK_CHARS", "500")
    monkeypatch.setenv("HOSPITAL_VECTOR_CHUNK_OVERLAP", "50")
    knowledge = {
        "metadata": {"generated_at": "2026-07-17T10:00:00+07:00"},
        "records": [
            {
                "kind": "price",
                "name": "Siêu âm tim",
                "price_bhyt_vnd": 250_000,
                "source": {
                    "url": "https://benhvientimhanoi.vn/bang-gia",
                    "document_url": "https://drive.google.com/file/d/price/preview",
                },
            }
        ],
        "web_pages": [
            {
                "title": "Giờ làm việc",
                "url": "https://benhvientimhanoi.vn/gio-lam-viec",
                "text": "Bệnh viện tiếp nhận người bệnh trong giờ hành chính.",
            }
        ],
    }

    chunks = vector_tools.build_vector_chunks(knowledge)

    assert {chunk["kind"] for chunk in chunks} == {"price", "web_page"}
    price = next(chunk for chunk in chunks if chunk["kind"] == "price")
    assert "Giá BHYT (VND): 250000" in price["content"]
    assert price["document_url"].startswith("https://drive.google.com")
    assert all(len(chunk["chunk_id"]) == 64 for chunk in chunks)


def test_chunk_ids_are_deterministic() -> None:
    knowledge = {
        "records": [{"kind": "service", "name": "Điện tâm đồ", "source": {}}],
        "web_pages": [],
    }
    first = vector_tools.build_vector_chunks(knowledge)
    second = vector_tools.build_vector_chunks(knowledge)
    assert first == second


def test_web_chunks_deduplicate_www_hostname_variants() -> None:
    knowledge = {
        "records": [],
        "web_pages": [
            {
                "title": "Bảng giá",
                "url": "https://www.benhvientimhanoi.vn/bang-gia/",
                "text": "Giá dịch vụ kỹ thuật.",
            },
            {
                "title": "Bảng giá",
                "url": "https://benhvientimhanoi.vn/bang-gia",
                "text": "Giá dịch vụ kỹ thuật.",
            },
        ],
    }
    chunks = vector_tools.build_vector_chunks(knowledge)
    assert len(chunks) == 1
    assert chunks[0]["source_url"] == "https://benhvientimhanoi.vn/bang-gia"


def test_embeddings_use_existing_openai_compatible_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    class FakeEmbeddings:
        def create(self, *, model: str, input: list[str]) -> SimpleNamespace:
            calls.update(model=model, input=input)
            data = [
                SimpleNamespace(index=index, embedding=[0.1, 0.2, 0.3])
                for index in range(len(input))
            ]
            return SimpleNamespace(data=data)

    monkeypatch.setenv("HOSPITAL_EMBEDDING_MODEL", "test-multilingual-model")
    monkeypatch.setenv("HOSPITAL_EMBEDDING_DIMENSION", "3")
    monkeypatch.setenv("HOSPITAL_EMBEDDING_BACKEND", "openai_compatible")
    monkeypatch.setattr(
        vector_tools,
        "_openai_client",
        lambda: SimpleNamespace(embeddings=FakeEmbeddings()),
    )

    result = vector_tools.embed_texts(["giá siêu âm tim", "cơ sở 2"])

    assert result == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert calls == {
        "model": "test-multilingual-model",
        "input": ["giá siêu âm tim", "cơ sở 2"],
    }


def test_vector_search_returns_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSnapshot:
        def to_dict(self) -> dict:
            return {
                "content": "Tên: Siêu âm tim\nGiá BHYT (VND): 250000",
                "kind": "price",
                "title": "Siêu âm tim",
                "source_url": "https://benhvientimhanoi.vn/bang-gia",
                "document_url": "https://drive.google.com/file/d/price/preview",
                "published_at": "20/01/2025",
                "retrieved_at": "17/07/2026",
                "vector_distance": 0.08,
            }

    class FakeVectorQuery:
        def stream(self) -> list[FakeSnapshot]:
            return [FakeSnapshot()]

    class FakeCollection:
        def find_nearest(self, **kwargs: object) -> FakeVectorQuery:
            assert kwargs["vector_field"] == "embedding"
            assert kwargs["limit"] == 5
            return FakeVectorQuery()

    monkeypatch.setenv("HOSPITAL_EMBEDDING_MODEL", "test-model")
    monkeypatch.setattr(
        vector_tools,
        "embed_texts",
        lambda texts, task_type="RETRIEVAL_DOCUMENT": [[0.1, 0.2, 0.3]],
    )
    monkeypatch.setattr(vector_tools, "_collection", lambda: FakeCollection())

    result = asyncio.run(vector_tools.search_hospital_vector_database("giá siêu âm tim", 5))

    assert result["status"] == "success"
    assert result["matches"][0]["vector_distance"] == 0.08
    assert result["matches"][0]["source_url"].startswith("https://benhvientimhanoi.vn")


def test_price_agent_only_uses_firestore_vector_search() -> None:
    assert len(service_price_agent.tools) == 1
    assert service_price_agent.tools[0].__name__ == "search_hospital_vector_database"

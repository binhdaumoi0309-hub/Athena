import asyncio
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from hanoi_heart_assistant.tools import document_ingestion, price_tools
from hanoi_heart_assistant.tools.playwright_mcp import (
    create_playwright_mcp_toolset,
    playwright_mcp_enabled,
)


@pytest.fixture
def knowledge_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Path]:
    path = tmp_path / "hospital_knowledge.json"
    payload = {
        "metadata": {"generated_at": "2026-07-17T10:00:00+07:00"},
        "records": [
            {
                "kind": "price",
                "name": "Siêu âm tim Doppler màu",
                "code": "SA-TIM-01",
                "category": "Chẩn đoán hình ảnh",
                "price_bhyt_vnd": 250_000,
                "price_regular_vnd": 350_000,
                "price_on_request_vnd": 500_000,
                "source": {
                    "title": "Bảng giá dịch vụ kỹ thuật 2025",
                    "url": "https://benhvientimhanoi.vn/bang-gia-2025",
                    "published_at": "20/01/2025",
                    "retrieved_at": "17/07/2026",
                },
            },
            {
                "kind": "facility",
                "name": "Cơ sở 2",
                "details": "695 Lạc Long Quân, Tây Hồ, Hà Nội",
                "source": {
                    "title": "Trang chủ",
                    "url": "https://benhvientimhanoi.vn/",
                    "retrieved_at": "17/07/2026",
                },
            },
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("HOSPITAL_KNOWLEDGE_PATH", str(path))
    price_tools._load_index.cache_clear()
    yield path
    price_tools._load_index.cache_clear()


def test_price_lookup_returns_all_price_types_and_source(knowledge_index: Path) -> None:
    result = price_tools.search_service_prices("sieu am tim")

    assert result["status"] == "success"
    assert result.get("price_not_found") is None
    assert result["updated_at"] == "2026-07-17T10:00:00+07:00"
    assert len(result["matches"]) == 1
    match = result["matches"][0]
    assert match["code"] == "SA-TIM-01"
    assert match["price_bhyt_vnd"] == 250_000
    assert match["price_regular_vnd"] == 350_000
    assert match["price_on_request_vnd"] == 500_000
    assert result["sources"][0]["url"] == "https://benhvientimhanoi.vn/bang-gia-2025"


def test_topic_filter_excludes_unrelated_record_types(knowledge_index: Path) -> None:
    result = price_tools.search_hospital_information("Lac Long Quan", topic="facility")

    assert [match["kind"] for match in result["matches"]] == ["facility"]
    assert result["matches"][0]["name"] == "Cơ sở 2"


@pytest.mark.parametrize(
    ("query", "topic"),
    [("", "auto"), ("siêu âm tim", "unknown")],
)
def test_lookup_rejects_invalid_input(
    knowledge_index: Path,
    query: str,
    topic: str,
) -> None:
    result = price_tools.search_hospital_information(query, topic=topic)
    assert result["status"] == "error"


def test_missing_index_returns_empty_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSPITAL_KNOWLEDGE_PATH", str(tmp_path / "missing.json"))
    price_tools._load_index.cache_clear()

    result = price_tools.search_service_prices("điện tâm đồ")

    assert result["status"] == "success"
    assert result["matches"] == []
    assert result["price_not_found"] is True
    assert result["updated_at"] is None


def test_playwright_mcp_is_scoped_to_expected_browser_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_PLAYWRIGHT_MCP", "true")
    assert playwright_mcp_enabled() is True

    toolset = create_playwright_mcp_toolset()
    assert toolset.tool_name_prefix == "hospital_web"
    assert set(toolset.tool_filter) == {
        "browser_click",
        "browser_navigate",
        "browser_snapshot",
        "browser_wait_for",
    }
    args = toolset.connection_params.server_params.args
    assert args[0] == "-y"
    assert "--headless" in args
    assert "--isolated" in args
    assert args[args.index("--timeout-action") + 1] == "15000"
    assert args[args.index("--timeout-navigation") + 1] == "90000"
    allowed_origins = args[args.index("--allowed-origins") + 1]
    assert "https://benhvientimhanoi.vn" in allowed_origins
    assert "https://drive.google.com" in allowed_origins


def test_web_search_ranks_relevant_page_and_reports_partial_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_crawl(start_urls: tuple[str, ...], max_pages: int) -> list[dict]:
        assert start_urls == document_ingestion.DEFAULT_START_URLS
        assert max_pages == 3
        return [
            {
                "title": "Trang chủ",
                "url": "https://benhvientimhanoi.vn/",
                "text": "Thông tin chung của bệnh viện",
                "documents": [],
            },
            {
                "title": "Giá dịch vụ kỹ thuật 2025",
                "url": "https://benhvientimhanoi.vn/bang-gia",
                "text": "Bảng giá siêu âm tim áp dụng cho BHYT và người không có BHYT.",
                "documents": [
                    "https://drive.google.com/file/d/price-document/preview",
                    "https://youtube.com/not-allowed",
                ],
            },
            {"url": "https://benhvientimhanoi.vn/error", "error": "timeout"},
        ]

    monkeypatch.setenv("HOSPITAL_WEB_SEARCH_MAX_PAGES", "3")
    monkeypatch.setattr(document_ingestion, "crawl_pages", fake_crawl)

    result = asyncio.run(
        document_ingestion.search_official_hospital_web("giá siêu âm tim", max_pages=20)
    )

    assert result["status"] == "success"
    assert result["pages_inspected"] == 3
    assert result["page_error_count"] == 1
    assert result["matches"][0]["title"] == "Giá dịch vụ kỹ thuật 2025"
    assert result["matches"][0]["documents"] == [
        "https://drive.google.com/file/d/price-document/preview"
    ]
    assert "siêu âm tim" in result["matches"][0]["excerpt"]


def test_web_search_rejects_empty_query() -> None:
    result = asyncio.run(document_ingestion.search_official_hospital_web("  "))
    assert result["status"] == "error"


def test_agent_refresh_calls_sync_and_returns_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "index.json"
    calls: dict[str, object] = {}

    def fake_sync(path: Path, download_dir: Path, max_pages: int) -> dict:
        calls.update(path=path, download_dir=download_dir, max_pages=max_pages)
        return {
            "metadata": {
                "generated_at": "2026-07-17T11:00:00+07:00",
                "record_count": 42,
                "pipeline": "test-pipeline",
            },
            "crawl_errors": [{"url": "one", "error": "ignored"}],
        }

    monkeypatch.setenv("ALLOW_AGENT_KNOWLEDGE_REFRESH", "true")
    monkeypatch.setenv("HOSPITAL_REFRESH_MAX_PAGES", "5")
    monkeypatch.setenv("HOSPITAL_KNOWLEDGE_PATH", str(output))
    monkeypatch.setattr(document_ingestion, "sync_knowledge", fake_sync)

    result = asyncio.run(document_ingestion.refresh_hospital_knowledge(max_pages=20))

    assert result["status"] == "success"
    assert result["record_count"] == 42
    assert result["crawl_error_count"] == 1
    assert calls["path"] == output
    assert calls["max_pages"] == 5


def test_agent_refresh_preserves_index_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_sync(*args: object, **kwargs: object) -> dict:
        raise RuntimeError("OCR failed")

    monkeypatch.setenv("ALLOW_AGENT_KNOWLEDGE_REFRESH", "true")
    monkeypatch.setattr(document_ingestion, "sync_knowledge", failing_sync)

    result = asyncio.run(document_ingestion.refresh_hospital_knowledge())

    assert result == {
        "status": "error",
        "message": "OCR failed",
        "index_preserved": True,
    }

import asyncio
from pathlib import Path

import pytest

from hanoi_heart_assistant.tools.document_ingestion import (
    _extraction_backend,
    download_public_file,
    google_drive_file_id,
    refresh_hospital_knowledge,
)


def test_extracts_google_drive_file_id() -> None:
    assert (
        google_drive_file_id("https://drive.google.com/file/d/12jH3KovC3PHNoXQn9KekZkJXMcxtb2_S/preview")
        == "12jH3KovC3PHNoXQn9KekZkJXMcxtb2_S"
    )
    assert google_drive_file_id("https://drive.google.com/open?id=abc_123") == "abc_123"


def test_downloader_rejects_untrusted_host() -> None:
    with pytest.raises(ValueError, match="host"):
        download_public_file("https://example.com/private.pdf", Path("."))


def test_auto_backend_uses_openai_endpoint_without_gemini_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DOCUMENT_EXTRACTION_BACKEND", "auto")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert _extraction_backend() == "openai_compatible"


def test_auto_backend_prefers_files_api_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCUMENT_EXTRACTION_BACKEND", "auto")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    assert _extraction_backend() == "files_api"


def test_agent_refresh_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALLOW_AGENT_KNOWLEDGE_REFRESH", raising=False)
    result = asyncio.run(refresh_hospital_knowledge())
    assert result["status"] == "disabled"

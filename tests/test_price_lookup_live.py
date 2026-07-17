import asyncio
import os

import pytest

from hanoi_heart_assistant.tools.document_ingestion import search_official_hospital_web

PRICE_PAGE_URL = (
    "https://www.benhvientimhanoi.vn/vi/chi-tiet/bang-gia-dich-vu/"
    "gia-dich-vu-ky-thuat-ap-dung-tai-benh-vien-tim-ha-noi-2025"
)


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_WEB_TESTS") != "1",
    reason="Set RUN_LIVE_WEB_TESTS=1 to access the official hospital website.",
)
def test_live_price_page_exposes_google_drive_document() -> None:
    result = asyncio.run(search_official_hospital_web("giá dịch vụ kỹ thuật 2025", max_pages=4))

    assert result["status"] == "success"
    expected_path = PRICE_PAGE_URL.split("benhvientimhanoi.vn", 1)[1]
    assert any(match["url"].endswith(expected_path) for match in result["matches"])
    assert any(
        "drive.google.com/file/d/" in document
        for match in result["matches"]
        for document in match["documents"]
    )

"""Crawl hospital pages, download documents, and extract structured facts with Gemini."""

from __future__ import annotations

import argparse
import asyncio
import base64
import html
import json
import mimetypes
import os
import re
import unicodedata
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from playwright.async_api import async_playwright

from ..llm import _openai_client

load_dotenv()

HOSPITAL_HOSTS = {"benhvientimhanoi.vn", "www.benhvientimhanoi.vn"}
DRIVE_HOSTS = {"drive.google.com", "docs.google.com", "drive.usercontent.google.com"}
DEFAULT_START_URLS = (
    "https://benhvientimhanoi.vn/",
    "https://benhvientimhanoi.vn/vi/chi-tiet/bang-gia-dich-vu/"
    "gia-dich-vu-ky-thuat-ap-dung-tai-benh-vien-tim-ha-noi-2025",
    "https://www.benhvientimhanoi.vn/vi/chi-tiet/bang-gia-dich-vu/"
    "bang-bao-gia-dich-vu-ky-thuat-theo-yeu-cau-tai-benh-vien-tim-ha-noi.",
    "https://benhvientimhanoi.vn/vi/chi-tiet-lich-kham/bang-gia-dich-vu/"
    "bang-gia-bao-hiem-y-te-tai-benh-vien-tim-ha-noi.",
)
RELEVANT_MARKERS = (
    "bang-gia",
    "dich-vu",
    "khoa-",
    "co-cau",
    "gioi-thieu",
    "quy-trinh-kham",
    "lich-lam-viec",
    "lien-he",
    "bao-hiem",
    "bhyt",
)
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024

EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "document_title": {"type": "string"},
        "document_date": {"type": ["string", "null"]},
        "is_scanned": {"type": "boolean"},
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "facility",
                            "hours",
                            "department",
                            "service",
                            "price",
                            "comparison",
                        ],
                    },
                    "name": {"type": "string"},
                    "code": {"type": ["string", "null"]},
                    "category": {"type": ["string", "null"]},
                    "details": {"type": ["string", "null"]},
                    "price_bhyt_vnd": {"type": ["integer", "null"]},
                    "price_regular_vnd": {"type": ["integer", "null"]},
                    "price_on_request_vnd": {"type": ["integer", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["kind", "name"],
            },
        },
    },
    "required": ["document_title", "is_scanned", "records"],
}
EXTRACTION_INSTRUCTION = """
Trích xuất dữ liệu của Bệnh viện Tim Hà Nội thành JSON theo schema. Lấy địa chỉ/cơ sở/giờ làm
việc, khoa phòng, dịch vụ và mọi mức giá. Phân biệt chính xác BHYT, dịch vụ thường và theo yêu
cầu. Giá là số nguyên VND; không suy đoán dữ liệu thiếu hoặc chữ mờ, hãy dùng null và ghi chú.
Giữ nguyên mã dịch vụ, đơn vị, phạm vi áp dụng. Không lấy menu/footer lặp lại nếu không liên quan.
"""


def _safe_filename(url: str, content_type: str | None = None) -> str:
    path_name = Path(urlparse(url).path).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", path_name).strip("._") or "document"
    if "." not in name and content_type:
        name += mimetypes.guess_extension(content_type.split(";", 1)[0]) or ""
    return name[:180]


def google_drive_file_id(url: str) -> str | None:
    """Extract a public Google Drive file id from common link formats."""
    patterns = (r"/file/d/([A-Za-z0-9_-]+)", r"[?&]id=([A-Za-z0-9_-]+)")
    return next((match.group(1) for p in patterns if (match := re.search(p, url))), None)


def _allowed_download(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in HOSPITAL_HOSTS | DRIVE_HOSTS


def download_public_file(url: str, destination_dir: Path) -> Path:
    """Download a hospital or public Drive file without accepting arbitrary hosts."""
    if not _allowed_download(url):
        raise ValueError(f"Từ chối tải file ngoài danh sách host cho phép: {url}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    drive_id = google_drive_file_id(url)
    request_url = (
        f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&confirm=t"
        if drive_id
        else url
    )
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        response = client.get(request_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        # Some large public Drive files return a confirmation HTML page.
        if drive_id and "text/html" in content_type:
            match = re.search(r'href="([^"]*(?:confirm=|download)[^"]*)"', response.text)
            if match:
                confirmed_url = urljoin(
                    str(response.url), html.unescape(match.group(1)).replace("&amp;", "&")
                )
                response = client.get(confirmed_url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
        length = int(response.headers.get("content-length", "0") or 0)
        if length > MAX_DOWNLOAD_BYTES or len(response.content) > MAX_DOWNLOAD_BYTES:
            raise ValueError("Tài liệu vượt giới hạn 50 MB của pipeline.")
        if "text/html" in content_type and drive_id:
            raise RuntimeError(
                "Google Drive không trả về file công khai; hãy kiểm tra quyền chia sẻ."
            )
        filename = _safe_filename(str(response.url), content_type)
        if drive_id:
            signatures = {
                b"%PDF-": ".pdf",
                b"\x89PNG": ".png",
                b"\xff\xd8\xff": ".jpg",
            }
            detected_suffix = next(
                (
                    suffix
                    for signature, suffix in signatures.items()
                    if response.content.startswith(signature)
                ),
                None,
            )
            if detected_suffix:
                filename = f"drive_{drive_id}{detected_suffix}"
        target = destination_dir / filename
        target.write_bytes(response.content)
        return target


async def crawl_pages(start_urls: tuple[str, ...], max_pages: int = 40) -> list[dict[str, Any]]:
    """Use Playwright to render relevant pages and discover embedded documents."""
    queue = deque(start_urls)
    seen: set[str] = set()
    pages: list[dict[str, Any]] = []
    page_timeout = int(os.getenv("HOSPITAL_PAGE_TIMEOUT_MS", "45000"))
    retries = max(1, min(int(os.getenv("HOSPITAL_CRAWL_RETRIES", "2")), 4))
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True, locale="vi-VN")
        page = await context.new_page()
        while queue and len(pages) < max_pages:
            url = queue.popleft().split("#", 1)[0]
            if url in seen or (urlparse(url).hostname or "").lower() not in HOSPITAL_HOSTS:
                continue
            seen.add(url)
            last_error: Exception | None = None
            snapshot: dict[str, Any] | None = None
            for attempt in range(1, retries + 1):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=page_timeout)
                    await page.wait_for_timeout(750)
                    snapshot = await page.evaluate(
                    """() => ({
                      url: location.href,
                      title: document.title,
                      text: (document.querySelector(
                        'main, article, .detail, .content'
                      ) || document.body)
                        .innerText.slice(0, 60000),
                      links: [...document.querySelectorAll('a[href]')].map(a => a.href),
                      documents: [...document.querySelectorAll(
                        'iframe[src], object[data], embed[src]'
                      )]
                        .map(e => e.src || e.data)
                    })"""
                    )
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < retries:
                        await page.wait_for_timeout(500 * attempt)
            if snapshot is None:
                pages.append({"url": url, "error": str(last_error), "records": []})
                continue
            pages.append(snapshot)
            for link in snapshot["links"]:
                absolute = urljoin(snapshot["url"], link).split("#", 1)[0]
                host = (urlparse(absolute).hostname or "").lower()
                relevant = any(marker in absolute.lower() for marker in RELEVANT_MARKERS)
                if host in HOSPITAL_HOSTS and relevant:
                    queue.append(absolute)
                is_document = absolute.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))
                if host in DRIVE_HOSTS or is_document:
                    snapshot["documents"].append(absolute)
            snapshot["documents"] = list(dict.fromkeys(snapshot["documents"]))
        await browser.close()
    return pages


def _normalize_search(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _web_result_score(query: str, page: dict[str, Any]) -> int:
    query_tokens = set(re.findall(r"[a-z0-9]+", _normalize_search(query)))
    title = _normalize_search(page.get("title", ""))
    body = _normalize_search(page.get("text", ""))
    title_overlap = sum(token in title for token in query_tokens)
    body_overlap = sum(token in body for token in query_tokens)
    exact_bonus = 10 if _normalize_search(query) in f"{title} {body}" else 0
    return title_overlap * 5 + body_overlap + exact_bonus


def _web_excerpt(query: str, text: str, max_chars: int = 3500) -> str:
    tokens = set(re.findall(r"[a-z0-9]+", _normalize_search(query)))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    relevant = [
        line
        for line in lines
        if tokens & set(re.findall(r"[a-z0-9]+", _normalize_search(line)))
    ]
    selected = relevant[:30] if relevant else lines[:30]
    return "\n".join(selected)[:max_chars]


async def search_official_hospital_web(query: str, max_pages: int = 12) -> dict[str, Any]:
    """Search current official hospital pages with retries and ranked results.

    Args:
        query: Vietnamese topic, service name, price type, department, or facility.
        max_pages: Maximum relevant official pages to inspect, from 1 through 30.
    """
    query = query.strip()
    if not query:
        return {"status": "error", "message": "Vui lòng nhập nội dung cần tìm trên web."}
    configured_max = int(os.getenv("HOSPITAL_WEB_SEARCH_MAX_PAGES", "12"))
    effective_max = max(1, min(max_pages, configured_max, 30))
    pages = await crawl_pages(DEFAULT_START_URLS, max_pages=effective_max)
    errors = [page for page in pages if page.get("error")]
    ranked = sorted(
        (
            (_web_result_score(query, page), page)
            for page in pages
            if not page.get("error")
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    matches = [
        {
            "title": page.get("title"),
            "url": page.get("url"),
            "excerpt": _web_excerpt(query, page.get("text", "")),
            "documents": [url for url in page.get("documents", []) if _allowed_download(url)],
            "relevance_score": score,
        }
        for score, page in ranked[:5]
        if score > 0
    ]
    return {
        "status": "success" if matches else "not_found",
        "query": query,
        "searched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "pages_inspected": len(pages),
        "page_error_count": len(errors),
        "matches": matches,
        "notice": "Kết quả web hiện thời; mở URL phù hợp bằng hospital_web để kiểm tra chi tiết.",
    }


def _gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY để dùng Gemini Files API.")
    return genai.Client(api_key=api_key)


def _extraction_backend() -> str:
    backend = os.getenv("DOCUMENT_EXTRACTION_BACKEND", "auto").strip().lower()
    if backend == "auto":
        return "files_api" if os.getenv("GEMINI_API_KEY", "").strip() else "openai_compatible"
    if backend not in {"files_api", "openai_compatible"}:
        raise RuntimeError(
            "DOCUMENT_EXTRACTION_BACKEND phải là auto, files_api hoặc openai_compatible."
        )
    return backend


def _document_model() -> str:
    configured = os.getenv("DOCUMENT_EXTRACTION_MODEL", "").strip()
    if configured:
        return configured.removeprefix("openai/")
    hospital_model = os.getenv("HOSPITAL_ASSISTANT_MODEL", "google/gemini-2.5-flash").strip()
    return hospital_model.removeprefix("openai/")


def _parse_json_response(text: str | None) -> dict[str, Any]:
    if not text:
        raise RuntimeError("Mô hình không trả về nội dung trích xuất.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _extract_openai_compatible(prompt: str, file_path: Path | None = None) -> dict[str, Any]:
    """Use the existing OpenAI-compatible endpoint with an optional inline PDF/image."""
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if file_path:
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
        content.insert(
            0,
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
            },
        )
    response = _openai_client().chat.completions.create(
        model=_document_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "Chỉ trả về một JSON object hợp lệ, không markdown. "
                    "JSON phải tuân theo schema: "
                    + json.dumps(EXTRACTION_SCHEMA, ensure_ascii=False)
                ),
            },
            {"role": "user", "content": content},
        ],
        temperature=0,
    )
    return _parse_json_response(response.choices[0].message.content)


def extract_with_gemini(file_path: Path) -> dict[str, Any]:
    """Extract one PDF/image with Files API or the configured compatible endpoint."""
    prompt = (
        "Đọc toàn bộ tài liệu. Nếu PDF là bản scan, dùng thị giác để OCR từng hàng của bảng. "
        "is_scanned=true nếu phần lớn nội dung cần đọc bằng thị giác.\n" + EXTRACTION_INSTRUCTION
    )
    if _extraction_backend() == "openai_compatible":
        return _extract_openai_compatible(prompt, file_path)

    client = _gemini_client()
    uploaded = client.files.upload(file=file_path)
    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_DOCUMENT_MODEL", "gemini-2.5-flash"),
            contents=[uploaded, prompt],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=EXTRACTION_SCHEMA,
            ),
        )
        if not response.text:
            raise RuntimeError(f"Gemini không trả về nội dung cho {file_path.name}.")
        return json.loads(response.text)
    finally:
        if uploaded.name:
            client.files.delete(name=uploaded.name)


def extract_page_with_gemini(title: str, text: str) -> dict[str, Any]:
    """Extract structured facts from rendered webpage text."""
    prompt = f"Tiêu đề: {title}\n\nNội dung trang:\n{text}\n\n{EXTRACTION_INSTRUCTION}"
    if _extraction_backend() == "openai_compatible":
        return _extract_openai_compatible(prompt)

    client = _gemini_client()
    response = client.models.generate_content(
        model=os.getenv("GEMINI_DOCUMENT_MODEL", "gemini-2.5-flash"),
        contents=[prompt],
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=EXTRACTION_SCHEMA,
        ),
    )
    if not response.text:
        raise RuntimeError(f"Gemini không trích xuất được trang {title}.")
    return json.loads(response.text)


def _source(page: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", page.get("text", "")[:5000])
    return {
        "title": page.get("title") or page.get("url"),
        "url": page.get("url"),
        "published_at": dates[0] if dates else None,
        "retrieved_at": retrieved_at,
    }


def sync_knowledge(output: Path, download_dir: Path, max_pages: int = 40) -> dict[str, Any]:
    """Run the complete ingestion pipeline and atomically replace the JSON index."""
    # Validate credentials before crawling or touching the current index.
    if _extraction_backend() == "files_api":
        _gemini_client()
    else:
        _openai_client()
    retrieved_at = datetime.now().astimezone().isoformat(timespec="seconds")
    pages = asyncio.run(crawl_pages(DEFAULT_START_URLS, max_pages=max_pages))
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    processed_urls: set[str] = set()
    for page in pages:
        source = _source(page, retrieved_at)
        if page.get("error"):
            errors.append({"url": page["url"], "error": page["error"]})
            continue
        try:
            extracted_page = extract_page_with_gemini(page.get("title", ""), page.get("text", ""))
            for record in extracted_page.get("records", []):
                records.append({**record, "source": source})
        except Exception as exc:
            errors.append({"url": page["url"], "error": f"page extraction: {exc}"})
        for document_url in page.get("documents", []):
            if document_url in processed_urls or not _allowed_download(document_url):
                continue
            processed_urls.add(document_url)
            try:
                file_path = download_public_file(document_url, download_dir)
                extracted = extract_with_gemini(file_path)
                document_source = {**source, "document_url": document_url}
                for record in extracted.get("records", []):
                    records.append({**record, "source": document_source})
            except Exception as exc:
                errors.append({"url": document_url, "error": str(exc)})
    if not records:
        raise RuntimeError(
            "Không trích xuất được bản ghi nào; giữ nguyên chỉ mục hiện tại "
            "và kiểm tra crawl_errors."
        )
    web_pages = []
    for page in pages:
        if page.get("error"):
            continue
        source = _source(page, retrieved_at)
        web_pages.append(
            {
                "title": page.get("title"),
                "url": page.get("url"),
                "text": page.get("text", ""),
                "documents": [
                    url for url in page.get("documents", []) if _allowed_download(url)
                ],
                "published_at": source.get("published_at"),
                "retrieved_at": retrieved_at,
            }
        )
    payload = {
        "metadata": {
            "generated_at": retrieved_at,
            "root_url": "https://benhvientimhanoi.vn/",
            "record_count": len(records),
            "pipeline": f"playwright+{_extraction_backend()}+vision_ocr",
        },
        "records": records,
        "web_pages": web_pages,
        "crawl_errors": errors,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    return payload


async def refresh_hospital_knowledge(max_pages: int = 20) -> dict[str, Any]:
    """Refresh the price agent's hospital index from official web pages and documents.

    This tool runs Playwright crawling, downloads public hospital/Google Drive files,
    extracts webpage and PDF/image content using Gemini Files API or OPENAI_BASE_URL,
    performs vision OCR for scanned tables, and atomically updates the local index.

    Args:
        max_pages: Maximum number of relevant hospital pages to crawl in this refresh.
    """
    enabled = os.getenv("ALLOW_AGENT_KNOWLEDGE_REFRESH", "false").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return {
            "status": "disabled",
            "message": (
                "Tự động đồng bộ đang tắt. Quản trị viên cần đặt "
                "ALLOW_AGENT_KNOWLEDGE_REFRESH=true ở backend tin cậy."
            ),
        }

    configured_max = int(os.getenv("HOSPITAL_REFRESH_MAX_PAGES", "40"))
    effective_max = max(1, min(max_pages, configured_max, 100))
    output = Path(
        os.getenv(
            "HOSPITAL_KNOWLEDGE_PATH",
            "hanoi_heart_assistant/data/hospital_knowledge.json",
        )
    )
    download_dir = Path(os.getenv("HOSPITAL_DOWNLOAD_DIR", ".cache/hospital_documents"))
    try:
        result = await asyncio.to_thread(
            sync_knowledge,
            output,
            download_dir,
            effective_max,
        )
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "index_preserved": True,
        }
    metadata = result["metadata"]
    return {
        "status": "success",
        "generated_at": metadata["generated_at"],
        "record_count": metadata["record_count"],
        "pipeline": metadata["pipeline"],
        "crawl_error_count": len(result["crawl_errors"]),
        "knowledge_path": str(output),
        "message": "Đã cập nhật chỉ mục; hãy gọi lại công cụ tra cứu trước khi trả lời.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Đồng bộ dữ liệu Bệnh viện Tim Hà Nội")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            os.getenv(
                "HOSPITAL_KNOWLEDGE_PATH",
                "hanoi_heart_assistant/data/hospital_knowledge.json",
            )
        ),
    )
    parser.add_argument("--downloads", type=Path, default=Path(".cache/hospital_documents"))
    parser.add_argument("--max-pages", type=int, default=40)
    args = parser.parse_args()
    result = sync_knowledge(args.output, args.downloads, max_pages=args.max_pages)
    print(json.dumps(result["metadata"], ensure_ascii=False, indent=2))
    if result["crawl_errors"]:
        print(f"Có {len(result['crawl_errors'])} lỗi; xem crawl_errors trong file đầu ra.")


if __name__ == "__main__":
    main()

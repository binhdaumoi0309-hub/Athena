"""Offline website/Drive/OCR ingestion into Firestore Vector Search."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .document_ingestion import (
    DEFAULT_START_URLS,
    _allowed_download,
    _source,
    crawl_pages,
    sync_knowledge,
)
from .firebase_vector_tools import (
    create_firestore_vector_index,
    index_knowledge_in_firestore,
    load_knowledge_file,
)

load_dotenv()


def refresh_web_pages_only(output: Path, max_pages: int) -> dict[str, Any]:
    """Refresh rendered web text without rerunning PDF OCR."""
    knowledge = load_knowledge_file(output)
    retrieved_at = datetime.now().astimezone().isoformat(timespec="seconds")
    pages = asyncio.run(crawl_pages(DEFAULT_START_URLS, max_pages=max_pages))
    web_pages = []
    errors = []
    for page in pages:
        if page.get("error"):
            errors.append({"url": page["url"], "error": page["error"]})
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
    if not web_pages:
        raise RuntimeError("Không crawl được trang web nào; giữ nguyên knowledge file.")
    knowledge["web_pages"] = web_pages
    knowledge["web_crawl_errors"] = errors
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    return knowledge


def ingest_hospital_to_firebase(
    output: Path,
    download_dir: Path,
    max_pages: int = 40,
    skip_crawl: bool = False,
) -> dict[str, Any]:
    """Crawl/extract all hospital sources and replace the Firestore vector corpus."""
    knowledge = (
        load_knowledge_file(output)
        if skip_crawl
        else sync_knowledge(output, download_dir, max_pages=max_pages)
    )
    vector_result = index_knowledge_in_firestore(knowledge)
    return {
        "knowledge_generated_at": knowledge.get("metadata", {}).get("generated_at"),
        "record_count": len(knowledge.get("records", [])),
        "web_page_count": len(knowledge.get("web_pages", [])),
        **vector_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Đồng bộ website/PDF/ảnh Bệnh viện Tim Hà Nội vào Firestore vectors"
    )
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
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Chỉ embed file JSON hiện có, không crawl/OCR lại.",
    )
    parser.add_argument(
        "--crawl-web-only",
        action="store_true",
        help="Cập nhật raw web text nhưng dùng lại kết quả PDF/ảnh OCR hiện có.",
    )
    parser.add_argument(
        "--create-index",
        action="store_true",
        help="Tạo Firestore vector index và thoát, không chạy ingestion.",
    )
    parser.add_argument(
        "--wait-index",
        action="store_true",
        help="Chờ vector index tạo xong (có thể mất nhiều phút).",
    )
    args = parser.parse_args()
    if args.create_index:
        print(
            json.dumps(
                create_firestore_vector_index(wait=args.wait_index),
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    effective_max = max(1, min(args.max_pages, 100))
    if args.crawl_web_only:
        knowledge = refresh_web_pages_only(args.output, effective_max)
        vector_result = index_knowledge_in_firestore(knowledge)
        result = {
            "knowledge_generated_at": knowledge.get("metadata", {}).get("generated_at"),
            "record_count": len(knowledge.get("records", [])),
            "web_page_count": len(knowledge.get("web_pages", [])),
            **vector_result,
        }
    else:
        result = ingest_hospital_to_firebase(
            args.output,
            args.downloads,
            max_pages=effective_max,
            skip_crawl=args.skip_crawl,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

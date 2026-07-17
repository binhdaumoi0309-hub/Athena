"""Search the versioned hospital knowledge index produced by document ingestion."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_KNOWLEDGE_PATH = Path(__file__).parents[1] / "data" / "hospital_knowledge.json"
PRICE_FIELDS = ("price_bhyt_vnd", "price_regular_vnd", "price_on_request_vnd")


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _knowledge_path() -> Path:
    configured = os.getenv("HOSPITAL_KNOWLEDGE_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_KNOWLEDGE_PATH


@lru_cache(maxsize=4)
def _load_index(path: str, modified_ns: int) -> dict[str, Any]:
    del modified_ns  # included only to invalidate the cache after a sync
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _index() -> dict[str, Any]:
    path = _knowledge_path()
    if not path.exists():
        return {"metadata": {}, "records": []}
    return _load_index(str(path.resolve()), path.stat().st_mtime_ns)


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", _normalize(value)) if len(token) > 1}


def _record_text(record: dict[str, Any]) -> str:
    values = [
        record.get("kind"),
        record.get("name"),
        record.get("code"),
        record.get("category"),
        record.get("details"),
        record.get("notes"),
        " ".join(record.get("aliases", [])),
    ]
    return " ".join(str(value) for value in values if value)


def _score(query: str, record: dict[str, Any]) -> int:
    normalized_query = _normalize(query)
    normalized_record = _normalize(_record_text(record))
    query_tokens = _tokens(query)
    overlap = len(query_tokens & _tokens(normalized_record))
    phrase_bonus = 8 if normalized_query and normalized_query in normalized_record else 0
    name_bonus = 3 if normalized_query in _normalize(str(record.get("name", ""))) else 0
    return overlap * 2 + phrase_bonus + name_bonus


def search_hospital_information(query: str, topic: str = "auto", limit: int = 10) -> dict[str, Any]:
    """Search facilities, hours, departments, services, and official price records.

    Args:
        query: Vietnamese name, service code, department, facility, or comparison request.
        topic: One of auto, facility, hours, department, service, price, comparison.
        limit: Maximum number of best matching records, from 1 through 20.
    """
    query = query.strip()
    if not query:
        return {"status": "error", "message": "Vui lòng nhập nội dung cần tra cứu."}
    allowed_topics = {"auto", "facility", "hours", "department", "service", "price", "comparison"}
    if topic not in allowed_topics:
        topics = ", ".join(sorted(allowed_topics))
        return {"status": "error", "message": f"topic phải thuộc: {topics}."}
    data = _index()
    records = data.get("records", [])
    if topic != "auto":
        records = [record for record in records if record.get("kind") == topic]
    ranked = sorted(
        ((score, record) for record in records if (score := _score(query, record)) > 0),
        key=lambda item: item[0],
        reverse=True,
    )
    matches = [record for _, record in ranked[: max(1, min(limit, 20))]]
    sources: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for match in matches:
        source = match.get("source") or {}
        if source.get("url") and source["url"] not in seen_urls:
            seen_urls.add(source["url"])
            sources.append(source)
    return {
        "status": "success",
        "query": query,
        "topic": topic,
        "updated_at": data.get("metadata", {}).get("generated_at"),
        "matches": matches,
        "sources": sources,
        "notice": (
            "Giá và lịch có thể thay đổi. Chỉ trả lời theo bản ghi và nguồn bên dưới; "
            "nếu thiếu hoặc cũ, đề nghị xác nhận qua hotline 19001082."
        ),
    }


def search_service_prices(query: str) -> dict[str, Any]:
    """Search official indexed price records while preserving the original tool name."""
    result = search_hospital_information(query=query, topic="price", limit=15)
    if result.get("status") == "success" and not result["matches"]:
        # A service may be indexed without a corresponding price in the source.
        result = search_hospital_information(query=query, topic="service", limit=15)
        result["price_not_found"] = True
    return result

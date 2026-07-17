"""Firestore vector ingestion and semantic search for hospital knowledge."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from collections.abc import Iterable
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import google.auth
from dotenv import load_dotenv
from google import genai
from google.cloud import firestore, firestore_admin_v1
from google.cloud.firestore_admin_v1.types import Index
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from google.genai import types

from ..llm import _openai_client

load_dotenv()


def _embedding_model() -> str:
    return os.getenv("HOSPITAL_EMBEDDING_MODEL", "gemini-embedding-001").strip()


def _embedding_backend() -> str:
    backend = os.getenv("HOSPITAL_EMBEDDING_BACKEND", "google_genai_vertex").strip().lower()
    if backend not in {"google_genai_vertex", "openai_compatible"}:
        raise RuntimeError(
            "HOSPITAL_EMBEDDING_BACKEND phải là google_genai_vertex hoặc openai_compatible."
        )
    return backend


def _embedding_dimension() -> int:
    dimension = int(os.getenv("HOSPITAL_EMBEDDING_DIMENSION", "768"))
    if not 1 <= dimension <= 2048:
        raise RuntimeError("HOSPITAL_EMBEDDING_DIMENSION phải từ 1 đến 2048.")
    return dimension


def _firebase_project_id() -> str:
    configured = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    if configured:
        return configured
    base_url = os.getenv("OPENAI_BASE_URL", "")
    match = re.search(r"/projects/([^/]+)", base_url)
    if match:
        return match.group(1)
    _, adc_project = google.auth.default()
    if adc_project:
        return adc_project
    raise RuntimeError("Thiếu FIREBASE_PROJECT_ID và không xác định được project từ ADC/base URL.")


@lru_cache(maxsize=1)
def _firestore_client() -> firestore.Client:
    return firestore.Client(
        project=_firebase_project_id(),
        database=os.getenv("FIRESTORE_DATABASE", "(default)").strip() or "(default)",
    )


def _collection() -> Any:
    name = os.getenv("FIRESTORE_VECTOR_COLLECTION", "hospital_knowledge_chunks").strip()
    if not name:
        raise RuntimeError("FIRESTORE_VECTOR_COLLECTION không được để trống.")
    return _firestore_client().collection(name)


def _batched(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


@lru_cache(maxsize=1)
def _genai_embedding_client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=_firebase_project_id(),
        location=os.getenv("FIREBASE_EMBEDDING_LOCATION", "global").strip() or "global",
    )


def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """Create multilingual embeddings using Vertex AI or an OpenAI-compatible endpoint."""
    if not texts:
        return []
    batch_size = max(1, min(int(os.getenv("HOSPITAL_EMBEDDING_BATCH_SIZE", "5")), 250))
    expected_dimension = _embedding_dimension()
    embeddings: list[list[float]] = []
    backend = _embedding_backend()
    for batch in _batched(texts, batch_size):
        if backend == "openai_compatible":
            response = _openai_client().embeddings.create(model=_embedding_model(), input=batch)
            vectors = [
                list(item.embedding)
                for item in sorted(response.data, key=lambda item: item.index)
            ]
        else:
            response = _genai_embedding_client().models.embed_content(
                model=_embedding_model(),
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=expected_dimension,
                ),
            )
            vectors = [list(item.values or []) for item in (response.embeddings or [])]
        for vector in vectors:
            if len(vector) != expected_dimension:
                raise RuntimeError(
                    f"Embedding trả về {len(vector)} chiều, cấu hình yêu cầu {expected_dimension}."
                )
            embeddings.append(vector)
    return embeddings


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    compact = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not compact:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(compact):
        end = min(start + chunk_size, len(compact))
        if end < len(compact):
            boundary = max(compact.rfind("\n", start, end), compact.rfind(". ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append(compact[start:end].strip())
        if end >= len(compact):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _canonical_url(value: str | None) -> str | None:
    if not value:
        return value
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").removeprefix("www.")
    netloc = hostname if not parsed.port else f"{hostname}:{parsed.port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def _record_content(record: dict[str, Any]) -> str:
    source = record.get("source") or {}
    labels = {
        "Loại": record.get("kind"),
        "Tên": record.get("name"),
        "Mã": record.get("code"),
        "Danh mục": record.get("category"),
        "Chi tiết": record.get("details"),
        "Giá BHYT (VND)": record.get("price_bhyt_vnd"),
        "Giá thường (VND)": record.get("price_regular_vnd"),
        "Giá theo yêu cầu (VND)": record.get("price_on_request_vnd"),
        "Đơn vị": record.get("unit"),
        "Ghi chú": record.get("notes"),
        "Nguồn": _canonical_url(source.get("url")),
        "Tài liệu": _canonical_url(source.get("document_url")),
        "Ngày tài liệu": source.get("published_at"),
        "Ngày thu thập": source.get("retrieved_at"),
    }
    return "\n".join(f"{label}: {value}" for label, value in labels.items() if value is not None)


def build_vector_chunks(knowledge: dict[str, Any]) -> list[dict[str, Any]]:
    """Build deterministic chunks from structured OCR records and rendered web text."""
    chunk_size = max(500, int(os.getenv("HOSPITAL_VECTOR_CHUNK_CHARS", "3500")))
    overlap = max(
        0,
        min(int(os.getenv("HOSPITAL_VECTOR_CHUNK_OVERLAP", "300")), chunk_size // 3),
    )
    generated_at = knowledge.get("metadata", {}).get("generated_at")
    chunks: list[dict[str, Any]] = []

    for record in knowledge.get("records", []):
        source = record.get("source") or {}
        chunks.append(
            {
                "kind": record.get("kind", "record"),
                "title": record.get("name") or source.get("title"),
                "content": _record_content(record),
                "source_url": _canonical_url(source.get("url")),
                "document_url": _canonical_url(source.get("document_url")),
                "published_at": source.get("published_at"),
                "retrieved_at": source.get("retrieved_at") or generated_at,
            }
        )

    for page in knowledge.get("web_pages", []):
        for index, content in enumerate(_split_text(page.get("text", ""), chunk_size, overlap)):
            chunks.append(
                {
                    "kind": "web_page",
                    "title": page.get("title"),
                    "content": content,
                    "source_url": _canonical_url(page.get("url")),
                    "document_url": None,
                    "published_at": page.get("published_at"),
                    "retrieved_at": page.get("retrieved_at") or generated_at,
                    "part": index,
                }
            )

    unique: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        identity = json.dumps(chunk, ensure_ascii=False, sort_keys=True)
        chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        unique[chunk_id] = {**chunk, "chunk_id": chunk_id}
    return list(unique.values())


def index_knowledge_in_firestore(knowledge: dict[str, Any]) -> dict[str, Any]:
    """Embed all chunks, upsert them, then optionally remove stale chunks."""
    chunks = build_vector_chunks(knowledge)
    if not chunks:
        raise RuntimeError("Không có dữ liệu để đưa vào Firestore vector database.")
    collection = _collection()
    existing = {
        snapshot.id: snapshot.to_dict()
        for snapshot in collection.select(
            ["chunk_id", "embedding_model", "embedding_dimension"]
        ).stream()
    }
    to_embed = [
        chunk
        for chunk in chunks
        if chunk["chunk_id"] not in existing
        or existing[chunk["chunk_id"]].get("embedding_model") != _embedding_model()
        or existing[chunk["chunk_id"]].get("embedding_dimension") != _embedding_dimension()
    ]
    vectors = embed_texts([chunk["content"] for chunk in to_embed])
    indexed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    current_ids = {chunk["chunk_id"] for chunk in chunks}

    batch = _firestore_client().batch()
    operations = 0
    for chunk, vector in zip(to_embed, vectors, strict=True):
        reference = collection.document(chunk["chunk_id"])
        batch.set(
            reference,
            {
                **chunk,
                "embedding": Vector(vector),
                "embedding_model": _embedding_model(),
                "embedding_dimension": len(vector),
                "indexed_at": indexed_at,
            },
        )
        operations += 1
        if operations == 450:
            batch.commit()
            batch = _firestore_client().batch()
            operations = 0
    if operations:
        batch.commit()

    pruned = 0
    prune_enabled = os.getenv("FIREBASE_VECTOR_PRUNE_STALE", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if prune_enabled:
        delete_batch = _firestore_client().batch()
        delete_operations = 0
        for snapshot in collection.select(["chunk_id"]).stream():
            if snapshot.id in current_ids:
                continue
            delete_batch.delete(snapshot.reference)
            pruned += 1
            delete_operations += 1
            if delete_operations == 450:
                delete_batch.commit()
                delete_batch = _firestore_client().batch()
                delete_operations = 0
        if delete_operations:
            delete_batch.commit()

    return {
        "status": "success",
        "collection": collection.id,
        "indexed_at": indexed_at,
        "chunk_count": len(chunks),
        "embedded_count": len(to_embed),
        "pruned_count": pruned,
        "embedding_model": _embedding_model(),
        "embedding_dimension": _embedding_dimension(),
    }


def create_firestore_vector_index(wait: bool = False) -> dict[str, Any]:
    """Create the required 768-dimensional Firestore vector index."""
    project = _firebase_project_id()
    database = os.getenv("FIRESTORE_DATABASE", "(default)").strip() or "(default)"
    collection = os.getenv(
        "FIRESTORE_VECTOR_COLLECTION", "hospital_knowledge_chunks"
    ).strip()
    parent = f"projects/{project}/databases/{database}/collectionGroups/{collection}"
    vector_config = Index.IndexField.VectorConfig(
        dimension=_embedding_dimension(),
        flat=Index.IndexField.VectorConfig.FlatIndex(),
    )
    index = Index(
        query_scope=Index.QueryScope.COLLECTION,
        fields=[Index.IndexField(field_path="embedding", vector_config=vector_config)],
    )
    operation = firestore_admin_v1.FirestoreAdminClient().create_index(
        parent=parent,
        index=index,
    )
    result = operation.result(timeout=900) if wait else None
    return {
        "status": "ready" if result else "creating",
        "operation": operation.operation.name,
        "collection": collection,
        "embedding_dimension": _embedding_dimension(),
        "index_name": result.name if result else None,
    }


def _search_vector_database(query: str, limit: int) -> dict[str, Any]:
    query_vector = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    vector_query = _collection().find_nearest(
        vector_field="embedding",
        query_vector=Vector(query_vector),
        distance_measure=DistanceMeasure.COSINE,
        limit=max(1, min(limit, 20)),
        distance_result_field="vector_distance",
    )
    matches = []
    for snapshot in vector_query.stream():
        data = snapshot.to_dict()
        matches.append(
            {
                "content": data.get("content"),
                "kind": data.get("kind"),
                "title": data.get("title"),
                "source_url": data.get("source_url"),
                "document_url": data.get("document_url"),
                "published_at": data.get("published_at"),
                "retrieved_at": data.get("retrieved_at"),
                "vector_distance": data.get("vector_distance"),
            }
        )
    return {
        "status": "success",
        "query": query,
        "matches": matches,
        "embedding_model": _embedding_model(),
        "notice": "Kết quả semantic search từ dữ liệu web/PDF/ảnh đã được đồng bộ.",
    }


async def search_hospital_vector_database(query: str, limit: int = 8) -> dict[str, Any]:
    """Search hospital web, PDF, image, and price knowledge using Firestore vectors.

    Args:
        query: Vietnamese question, service, price, facility, department, or comparison.
        limit: Maximum nearest chunks to return, from 1 through 20.
    """
    query = query.strip()
    if not query:
        return {"status": "error", "message": "Vui lòng nhập nội dung cần tra cứu."}
    try:
        return await asyncio.to_thread(_search_vector_database, query, limit)
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "hint": "Kiểm tra Firebase project, ADC, vector index và chạy ingestion trước.",
        }


def load_knowledge_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


async def search_doctors_vector_database(query: str, limit: int = 5) -> dict[str, Any]:
    """Tìm kiếm danh sách bác sĩ phù hợp dựa trên năng lực, chuyên môn, triệu chứng bệnh và khu vực khám.

    Args:
        query: Triệu chứng bệnh của bệnh nhân, chuyên khoa yêu cầu, tên bác sĩ hoặc khu vực khám.
        limit: Số lượng bác sĩ tối đa cần trả về (từ 1 đến 10).
    """
    query = query.strip()
    if not query:
        return {"status": "error", "message": "Vui lòng nhập nội dung cần tìm kiếm bác sĩ."}
    try:
        def _search():
            query_vector = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
            collection = _firestore_client().collection("doctor_capabilities")
            vector_query = collection.find_nearest(
                vector_field="embedding",
                query_vector=Vector(query_vector),
                distance_measure=DistanceMeasure.COSINE,
                limit=max(1, min(limit, 10)),
                distance_result_field="vector_distance",
            )
            matches = []
            for snapshot in vector_query.stream():
                data = snapshot.to_dict()
                matches.append({
                    "id": data.get("id"),
                    "name": data.get("title"),
                    "description": data.get("content"),
                    "zone": data.get("zone"),
                    "vector_distance": data.get("vector_distance")
                })
            return {"status": "success", "matches": matches}
        return await asyncio.to_thread(_search)
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "hint": "Đảm bảo đã chạy ingestion cho bác sĩ và đã tạo index cho collection 'doctor_capabilities'."
        }


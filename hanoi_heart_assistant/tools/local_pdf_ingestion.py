"""OCR one local PDF and merge it into the existing Firestore vector corpus."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .document_ingestion import extract_with_gemini
from .firebase_vector_tools import index_knowledge_in_firestore, load_knowledge_file

load_dotenv()


def ingest_local_pdf(document: Path, knowledge_path: Path) -> dict[str, Any]:
    """OCR a local PDF, replace its previous records, and index the full corpus."""
    document = document.resolve(strict=True)
    if document.suffix.casefold() != ".pdf":
        raise ValueError(f"Chỉ hỗ trợ PDF, nhận được: {document.name}")

    extracted = extract_with_gemini(document)
    extracted_records = extracted.get("records", [])
    if not extracted_records:
        raise RuntimeError(f"Không OCR được bản ghi nào từ {document.name}.")

    knowledge = load_knowledge_file(knowledge_path)
    retrieved_at = datetime.now().astimezone().isoformat(timespec="seconds")
    document_uri = document.as_uri()
    source = {
        "title": extracted.get("document_title") or document.stem,
        "url": document_uri,
        "document_url": document_uri,
        "published_at": extracted.get("document_date"),
        "retrieved_at": retrieved_at,
        "is_scanned": extracted.get("is_scanned"),
    }

    retained_records = [
        record
        for record in knowledge.get("records", [])
        if (record.get("source") or {}).get("document_url") != document_uri
    ]
    new_records = [{**record, "source": source} for record in extracted_records]
    knowledge["records"] = [*retained_records, *new_records]
    metadata = knowledge.setdefault("metadata", {})
    metadata["generated_at"] = retrieved_at
    metadata["record_count"] = len(knowledge["records"])
    metadata["last_local_document"] = document_uri

    # Index the complete merged corpus so stale pruning cannot remove unrelated data.
    vector_result = index_knowledge_in_firestore(knowledge)

    knowledge_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = knowledge_path.with_suffix(knowledge_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(knowledge, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(knowledge_path)
    return {
        "document": str(document),
        "document_title": source["title"],
        "is_scanned": source["is_scanned"],
        "ocr_record_count": len(new_records),
        "total_record_count": len(knowledge["records"]),
        **vector_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OCR một PDF cục bộ và hợp nhất vào Firestore Vector Search hiện tại."
    )
    parser.add_argument("document", type=Path)
    parser.add_argument(
        "--knowledge",
        type=Path,
        default=Path("hanoi_heart_assistant/data/hospital_knowledge.json"),
    )
    args = parser.parse_args()
    result = ingest_local_pdf(args.document, args.knowledge)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

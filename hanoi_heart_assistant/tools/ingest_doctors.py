"""Script to ingest doctor descriptions and names into a separate Firestore Vector Search collection."""

import csv
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google.cloud.firestore_v1.vector import Vector
from google.cloud import firestore_admin_v1
from google.cloud.firestore_admin_v1.types import Index

from .firebase_vector_tools import (
    _firestore_client,
    embed_texts,
    _embedding_model,
    _embedding_dimension,
    _firebase_project_id
)

load_dotenv()

COLLECTION_NAME = "doctor_capabilities"

def load_doctors_group(names_file: str, desc_file: str, default_zone: str) -> list[dict]:
    names_path = Path(names_file)
    desc_path = Path(desc_file)
    
    if not names_path.exists() or not desc_path.exists():
        print(f"Warning: Skipping {names_file} or {desc_file} because they do not exist.")
        return []
        
    names = []
    with open(names_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row:
                names.append(row[0].strip())
                
    doctors = []
    with open(desc_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for idx, row in enumerate(reader):
            if row:
                doc_id = int(row[0])
                desc = row[1].strip()
                name = names[idx] if idx < len(names) else "Bác sĩ"
                doctors.append({
                    "id": doc_id,
                    "name": name,
                    "description": desc,
                    "zone": default_zone
                })
    return doctors

def create_doctors_vector_index(wait: bool = False):
    """Create the required vector index for the doctor_capabilities collection on Firestore."""
    print(f"Checking/Creating Firestore vector index for '{COLLECTION_NAME}'...")
    try:
        project = _firebase_project_id()
        database = os.getenv("FIRESTORE_DATABASE", "(default)").strip() or "(default)"
        parent = f"projects/{project}/databases/{database}/collectionGroups/{COLLECTION_NAME}"
        
        vector_config = Index.IndexField.VectorConfig(
            dimension=_embedding_dimension(),
            flat=Index.IndexField.VectorConfig.FlatIndex(),
        )
        index = Index(
            query_scope=Index.QueryScope.COLLECTION,
            fields=[Index.IndexField(field_path="embedding", vector_config=vector_config)],
        )
        
        client = firestore_admin_v1.FirestoreAdminClient()
        operation = client.create_index(
            parent=parent,
            index=index,
        )
        print(f"Index creation operation started: {operation.operation.name}")
        if wait:
            print("Waiting for index creation to complete (this might take a few minutes)...")
            result = operation.result(timeout=900)
            print(f"Index successfully created! Name: {result.name}")
        else:
            print("Index is being created in the background. You can check progress in the Google Cloud Console.")
    except Exception as e:
        print(f"Note/Warning during index check: {e} (Index might already exist or admin API is not enabled)")

def main():
    # 1. Create index if needed
    create_doctors_vector_index(wait=False)
    
    print("\nLoading doctor datasets...")
    all_doctors = []
    
    # Zone TN Facility 1
    all_doctors.extend(load_doctors_group(
        "data/doctors_zone_tn_fac_1.csv",
        "data/doctors_description_zone_tn_fac_1.csv",
        "Khu khám bệnh tự nguyện 1 (Cơ sở 1)"
    ))
    
    # General Hospital Facility 2
    all_doctors.extend(load_doctors_group(
        "data/doctors_zone_general_hospital_fac_2.csv",
        "data/doctors_description_general_hospital_fac_2.csv",
        "Bệnh viện Tim Hà Nội - Cơ sở 2"
    ))
    
    # Zone TN Facility 2
    all_doctors.extend(load_doctors_group(
        "data/doctors_zone_zone_tn_fac_2.csv",
        "data/doctors_description_zone_tn_fac_2.csv",
        "Khu khám bệnh tự nguyện - Cơ sở 2"
    ))
    
    if not all_doctors:
        print("No doctor data loaded. Please ensure the CSV files are in the 'data' directory.")
        return
        
    print(f"Loaded {len(all_doctors)} doctors in total.")
    
    # Build vector chunks
    chunks = []
    indexed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    
    for doc in all_doctors:
        chunk = {
            "kind": "doctor",
            "title": doc["name"],
            "content": doc["description"],
            "source_url": f"doctor://{doc['id']}?zone={doc['zone']}",
            "document_url": None,
            "published_at": indexed_at,
            "retrieved_at": indexed_at,
            "zone": doc["zone"]
        }
        identity = json.dumps(chunk, ensure_ascii=False, sort_keys=True)
        chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        chunks.append({**chunk, "chunk_id": chunk_id})
        
    print(f"Generated {len(chunks)} chunks. Creating embeddings...")
    
    # Generate embeddings
    texts = [c["content"] for c in chunks]
    vectors = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    
    print(f"Uploading to Firestore collection '{COLLECTION_NAME}'...")
    db_client = _firestore_client()
    collection = db_client.collection(COLLECTION_NAME)
    
    batch = db_client.batch()
    operations = 0
    
    for chunk, vector in zip(chunks, vectors, strict=True):
        doc_ref = collection.document(chunk["chunk_id"])
        batch.set(
            doc_ref,
            {
                **chunk,
                "embedding": Vector(vector),
                "embedding_model": _embedding_model(),
                "embedding_dimension": len(vector),
                "indexed_at": indexed_at,
            }
        )
        operations += 1
        if operations == 450:
            batch.commit()
            batch = db_client.batch()
            operations = 0
            
    if operations:
        batch.commit()
        
    print(f"Successfully ingested {len(chunks)} doctors into separate collection '{COLLECTION_NAME}'!")

if __name__ == '__main__':
    main()

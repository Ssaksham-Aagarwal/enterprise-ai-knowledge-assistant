import os
import uuid
from pathlib import Path
from typing import Any
from io import BytesIO

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/data/chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "enterprise_documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"},
)

def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, int]:
    reader = PdfReader(BytesIO(pdf_bytes))
    texts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(texts), len(reader.pages)

def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0.")
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks

def add_pdf_to_vector_store(filename: str, pdf_bytes: bytes) -> dict[str, Any]:
    text, pages = extract_pdf_text(pdf_bytes)
    if not text.strip():
        raise ValueError("No extractable text found. Scanned PDFs require OCR.")
    chunks = split_into_chunks(text)
    doc_id = str(uuid.uuid4())
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    metadata = [
        {"document_id": doc_id, "filename": Path(filename).name, "chunk_index": i}
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, documents=chunks, metadatas=metadata)
    return {"document_id": doc_id, "filename": Path(filename).name,
            "pages": pages, "chunks_stored": len(chunks)}

def retrieve_relevant_chunks(question: str, top_k: int = 4) -> list[dict[str, Any]]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    count = collection.count()
    if count == 0:
        return []
    result = collection.query(
        query_texts=[question], n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"]
    )
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    return [
        {"text": doc, "source": meta.get("filename", "unknown"),
         "document_id": meta.get("document_id"),
         "chunk_index": meta.get("chunk_index"), "distance": distance}
        for doc, meta, distance in zip(docs, metas, distances)
    ]

def generate_answer(question: str, contexts: list[dict[str, Any]]) -> str:
    import requests
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    context = "\n\n".join(
        f"[Source: {item['source']}, chunk {item['chunk_index']}]\n{item['text']}"
        for item in contexts
    )
    prompt = f"""You are an enterprise knowledge assistant.
Answer using ONLY the context below. If the answer is not present, say so.
Do not invent facts. Cite the source filename in your answer.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""
    response = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=240,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()

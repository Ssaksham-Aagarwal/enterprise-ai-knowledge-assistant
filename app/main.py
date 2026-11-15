
import logging
import time

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.rag.pipeline import (
    add_pdf_to_vector_store,
    get_collection,
    generate_answer,
    retrieve_relevant_chunks,
)
from app.metrics import (
    HTTP_REQUESTS,
    REQUEST_LATENCY,
    DOCUMENTS_INDEXED,
    PDF_UPLOADS,
    QUESTIONS_ASKED,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("knowledge-assistant")

app = FastAPI(
    title="Enterprise AI Knowledge Assistant",
    description="PDF knowledge assistant powered by RAG, ChromaDB and an LLM.",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    endpoint = request.url.path

    HTTP_REQUESTS.labels(
        request.method,
        endpoint,
        str(response.status_code)
    ).inc()

    REQUEST_LATENCY.labels(endpoint).observe(elapsed)

    return response


@app.get("/")
def home():
    return {
        "message": "Enterprise AI Knowledge Assistant is running",
        "indexed_chunks": get_collection().count()
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "vector_store": "ready"
    }


@app.get("/metrics")
def metrics():
    DOCUMENTS_INDEXED.set(get_collection().count())

    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Maximum PDF size is 20 MB."
        )

    try:
        result = add_pdf_to_vector_store(file.filename, content)

        PDF_UPLOADS.inc()

        logger.info(
            "Indexed PDF %s with %s chunks",
            result["filename"],
            result["chunks_stored"]
        )

        return {
            "message": "PDF processed and indexed successfully.",
            **result
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        logger.exception("PDF processing failed")

        raise HTTPException(
            status_code=500,
            detail="PDF processing failed. Check application logs."
        )


@app.post("/search")
def search_documents(request: QuestionRequest):

    matches = retrieve_relevant_chunks(
        request.question,
        request.top_k
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No documents indexed. Upload a PDF first."
        )

    QUESTIONS_ASKED.inc()

    return {
        "question": request.question,
        "matches": matches
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):

    matches = retrieve_relevant_chunks(
        request.question,
        request.top_k
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No documents indexed. Upload a PDF first."
        )

    QUESTIONS_ASKED.inc()

    try:
        answer = generate_answer(request.question, matches)

        sources = sorted({
            match["source"] for match in matches
        })

        return {
            "question": request.question,
            "answer": answer,
            "sources": sources
        }

    except requests.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Ollama. Check that Ollama is running."
        )

    except requests.HTTPError as exc:
        logger.exception("LLM request failed")

        raise HTTPException(
            status_code=502,
            detail=f"LLM request failed: {exc}"
        )

    except Exception:
        logger.exception("Answer generation failed")

        raise HTTPException(
            status_code=500,
            detail="Answer generation failed. Check application logs."
        )

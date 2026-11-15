# Enterprise AI Knowledge Assistant — Technical Presentation

## Slide 1 — Project Overview
Build an enterprise knowledge assistant that lets users upload PDF documents and ask natural-language questions grounded in those documents.

## Slide 2 — Problem Statement
Enterprise information is distributed across lengthy documents. Manually locating policy details is time-consuming. A retrieval-based assistant can find relevant passages and summarize them with source references.

## Slide 3 — Technology Stack
- Python, FastAPI and Streamlit
- PyPDF for extraction
- Sentence Transformers for embeddings
- ChromaDB for vector storage and similarity retrieval
- Ollama for local LLM inference
- Docker and Kubernetes for packaging and deployment
- GitHub Actions for CI
- Prometheus and Grafana for metrics and dashboards
- Loki as the log aggregation component (log shipping requires collector configuration)

## Slide 4 — Architecture
User → Streamlit → FastAPI → PDF extraction → chunking → embeddings → ChromaDB.
Question → embedding/retrieval → top-k passages → prompt/context → Ollama → grounded answer and sources.

## Slide 5 — RAG Workflow
1. Upload a PDF.
2. Extract text.
3. Split text into overlapping chunks.
4. Generate vector embeddings.
5. Store chunks and metadata in ChromaDB.
6. Embed the question and retrieve similar chunks.
7. Provide retrieved context to the LLM.
8. Return an answer and source filenames.

## Slide 6 — API Design
- GET `/` — service information
- GET `/health` — health check
- POST `/upload-pdf` — PDF ingestion
- POST `/search` — semantic retrieval
- POST `/ask` — retrieval plus LLM answer
- GET `/metrics` — Prometheus metrics

## Slide 7 — Containerization and Deployment
Docker image packages Python dependencies and application source. Docker Compose starts API, frontend, Ollama, Prometheus, Grafana and Loki. Kubernetes manifests define API/frontend services, persistent volumes, Ollama and monitoring components.

## Slide 8 — CI/CD
GitHub Actions checks out code, installs dependencies, runs pytest and builds a Docker image on pushes and pull requests to main. Registry publishing and automatic deployment are future extensions requiring secrets and cluster credentials.

## Slide 9 — Monitoring and Logging
Prometheus scrapes request counters, latency histograms, PDF upload and question counters. Grafana visualizes traffic and latency. Application logs are available through container logs. Loki is included, but a collector such as Grafana Alloy or Promtail must be configured for centralized log ingestion.

## Slide 10 — Demo Plan
1. Start services.
2. Upload a sample policy PDF.
3. Show successful indexing response.
4. Ask a question with `/search`.
5. Ask the same question with `/ask`.
6. Show Grafana metrics.
7. Show Docker containers and Kubernetes resources.

## Slide 11 — Limitations and Next Steps
OCR for scanned PDFs, authentication, authorization, document deletion, evaluation datasets, reranking, streaming answers, managed vector storage, automatic log shipping, image publishing and cluster deployment automation.

## Slide 12 — Conclusion
The project demonstrates an end-to-end RAG application and a practical DevOps deployment path, while identifying the operational work required before production use.

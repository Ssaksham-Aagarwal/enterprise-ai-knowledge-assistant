# Enterprise AI Knowledge Assistant

An end-to-end mini enterprise application that accepts PDF documents and answers questions using Retrieval-Augmented Generation (RAG).

## Architecture

1. **Streamlit** provides the user interface.
2. **FastAPI** handles PDF uploads, retrieval and question-answering APIs.
3. **PyPDF** extracts text from PDFs.
4. Text is split into overlapping chunks.
5. **Sentence Transformers** creates embeddings.
6. **ChromaDB** persists vectors and retrieves relevant passages.
7. **Ollama** runs the LLM locally and generates grounded answers.
8. **Docker Compose** runs the application and supporting services.
9. **Kubernetes manifests** describe API, frontend, Ollama, Prometheus and Grafana deployments.
10. **Prometheus/Grafana** provide metrics and dashboards. Application logs are written to stdout and can be inspected with Docker/Kubernetes logs; Loki is included in Compose as the log aggregation endpoint.

## Requirements

- Windows 10/11 with WSL 2, or Linux/macOS
- Python 3.11 recommended for local development
- VS Code (recommended)
- Docker Desktop for container deployment
- Ollama for local LLM answer generation
- Kubernetes cluster (Docker Desktop Kubernetes, Minikube or another cluster) for Kubernetes deployment

## Run locally (Windows PowerShell)

Open the project root in VS Code. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the API in terminal 1:

```powershell
uvicorn app.main:app --reload
```

Start Streamlit in terminal 2:

```powershell
streamlit run app/frontend.py
```

Open:
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

The first embedding operation downloads the Sentence Transformers model. The first API import initializes ChromaDB.

## Ollama setup

Install Ollama from https://ollama.com/download, then:

```powershell
ollama pull llama3.2
ollama serve
```

If Ollama is already running as a desktop service, `ollama serve` may report that the port is already in use; in that case just run the pull command and leave Ollama running. The local default URL is `http://localhost:11434`.

## API workflow

1. `POST /upload-pdf` — upload a text-based PDF.
2. `POST /search` — test semantic retrieval:

```json
{"question":"What is the leave policy?","top_k":4}
```

3. `POST /ask` — retrieve context and ask Ollama to generate a grounded answer using the same JSON body.

Other endpoints:
- `GET /` — basic application status
- `GET /health` — health check
- `GET /metrics` — Prometheus metrics

## Docker Compose

From the repository root:

```bash
docker compose up --build -d
docker compose exec ollama ollama pull llama3.2
```

Then open:
- Streamlit: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default local demo login: admin / admin)

The first model download can be several GB. Keep sufficient disk space and RAM available. For a CPU-only laptop, generation may be slow.

View logs:

```bash
docker compose logs -f api
docker compose logs -f frontend
```

Stop:

```bash
docker compose down
```

Persistent named volumes retain ChromaDB, Ollama models and Grafana data. `docker compose down -v` deletes those volumes.

## Kubernetes deployment

1. Build and push the image to a registry:

```bash
docker build -t YOUR_DOCKERHUB_USERNAME/enterprise-ai-knowledge-assistant:latest .
docker login
docker push YOUR_DOCKERHUB_USERNAME/enterprise-ai-knowledge-assistant:latest
```

2. Replace `YOUR_DOCKERHUB_USERNAME` in `kubernetes/api.yaml` and `kubernetes/frontend.yaml`.
3. Apply manifests:

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/ollama.yaml
kubectl apply -f kubernetes/api.yaml
kubectl apply -f kubernetes/frontend.yaml
kubectl apply -f kubernetes/prometheus.yaml
```

4. Pull the model into the Ollama pod:

```bash
kubectl -n knowledge-assistant get pods
kubectl -n knowledge-assistant exec deploy/ollama -- ollama pull llama3.2
```

5. Access the frontend:

```bash
kubectl -n knowledge-assistant get services
kubectl -n knowledge-assistant port-forward service/frontend 8501:8501
```

Then open http://localhost:8501. For local clusters, ensure storage classes and sufficient memory/disk are available. The manifests are a learning/demo baseline, not a production-hardened deployment.

## CI/CD

GitHub Actions runs dependency installation, tests and a Docker build on pushes and pull requests to `main`. It does not push images or deploy to a cluster. To enable registry publishing and deployment, add registry credentials as GitHub Actions secrets and extend the workflow with authenticated push/deploy steps.

## Monitoring and logging

- Prometheus scrapes FastAPI metrics at `/metrics`.
- Grafana is provisioned with a Prometheus datasource and a starter dashboard.
- Open Grafana at http://localhost:3000 and select the **Enterprise AI Knowledge Assistant** dashboard.
- Application logs are emitted to stdout/stderr. Use `docker compose logs -f api` or `kubectl logs` to inspect them.
- Loki runs in the Compose stack, but automatic log shipping is not enabled in this starter. Configure Grafana Alloy or Promtail to ship container/pod logs to Loki before claiming centralized log ingestion is complete.

## Tests

```powershell
pytest -q
```

## Limitations and production considerations

- PDF text extraction does not OCR scanned/image-only PDFs.
- ChromaDB is embedded in the API process for this learning project. For multi-replica production deployments, use a managed/standalone vector database and shared object storage.
- The demo does not include user authentication, document-level access control, malware scanning, rate limiting or audit-grade security.
- Validate retrieved passages and answers before using the system for business-critical decisions.
- Do not upload confidential company documents to a personal or unapproved environment.

## Deliverables

- Application source code
- README and setup instructions
- Dockerfile and Docker Compose
- Kubernetes manifests
- GitHub Actions CI workflow
- Prometheus configuration and Grafana dashboard
- Technical presentation in `docs/`

from prometheus_client import Counter, Histogram, Gauge

HTTP_REQUESTS = Counter(
    "knowledge_assistant_http_requests_total",
    "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "knowledge_assistant_request_latency_seconds",
    "HTTP request latency", ["endpoint"]
)
DOCUMENTS_INDEXED = Gauge(
    "knowledge_assistant_documents_indexed",
    "Number of PDF documents indexed during this process"
)
PDF_UPLOADS = Counter("knowledge_assistant_pdf_uploads_total", "Successful PDF uploads")
QUESTIONS_ASKED = Counter("knowledge_assistant_questions_total", "Questions submitted")

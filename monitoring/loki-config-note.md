# Logging

The application writes structured, timestamped logs to stdout/stderr. Docker captures container logs; view them with:

```bash
docker compose logs -f api
```

Loki is included as a log aggregation service. For production log ingestion, deploy Promtail or Grafana Alloy as a Docker/Kubernetes log collector and configure it to push container/pod logs to `http://loki:3100/loki/api/v1/push`. The starter compose stack does not claim automatic log shipping until that collector is configured.

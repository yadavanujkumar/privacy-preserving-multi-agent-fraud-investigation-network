# Privacy-Preserving Multi-Agent Fraud Investigation Network

## Overview

A **zero-trust, enterprise-grade** multi-agent FinTech platform that streams real-time transaction data and detects complex fraud rings. It integrates:

- **Federated Learning** – share anomaly patterns across institutions without exposing PII
- **Graph-aware risk scoring** – Neo4j fraud-ring detection with multi-hop traversal
- **Explainable AI (XAI)** – human-readable investigation summaries for compliance officers
- **LangGraph orchestration** – composable, auditable agent pipelines
- **Structured JSON logging + correlation IDs** – full observability across services
- **Graceful shutdown + health probes** – production-ready lifecycle management

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│  Client                                                    │
│    POST /api/transactions  (UUID, amount, source, target)  │
└───────────────────────────────┬───────────────────────────┘
                                │ Zod-validated + Correlation-ID
                                ▼
┌───────────────────────────────────────────────────────────┐
│  TypeScript API Service  (Express + Winston + Zod)         │
│  /health/live  /health/ready                               │
└───────────────────────────────┬───────────────────────────┘
                                │ kafkajs (idempotent producer)
                                ▼
┌───────────────────────────────────────────────────────────┐
│  Redpanda (Kafka-compatible event bus)                     │
│  Topics: high-value-transactions  |  all-transactions      │
└───────────────────────────────┬───────────────────────────┘
                                │ kafka-python consumer (retry)
                                ▼
┌───────────────────────────────────────────────────────────┐
│  Python Agent Service  (FastAPI + LangGraph)               │
│  1. fetch_graph  → Neo4j multi-hop connection count        │
│  2. run_model    → multi-factor risk score                 │
│     • high_amount (+0.45)  • high_connections (+0.35)      │
│     • cross_region (+0.10) • velocity_breach (+0.10)       │
│  3. generate_xai → CRITICAL/HIGH/MEDIUM/LOW explanation    │
│  /health/live  /health/ready  /metrics                     │
└───────────────────────────────────────────────────────────┘
                    │
                    ▼
       Neo4j Graph Database
```

### Component breakdown

| Layer | Technology | Role |
|---|---|---|
| Ingestion API | TypeScript / Express | Zod validation, correlation IDs, structured logging, graceful shutdown |
| Event Bus | Redpanda (Kafka-compatible) | High-throughput durable message streaming |
| Agent Orchestration | Python / LangGraph | Multi-step fraud investigation pipeline |
| Graph DB | Neo4j 5 | Fraud-ring detection via graph traversal |
| Infra (local) | Docker Compose | Health-checked, networked service stack |
| Infra (production) | Kubernetes + Terraform/EKS | HPA, probes, resource limits, multi-AZ |

---

## Quick Start (Docker Compose)

```bash
docker-compose up -d
```

Services start in dependency order with health-check gates. Once healthy:

```bash
# Submit a transaction
curl -X POST http://localhost:3000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "amount": 25000,
    "source": "US-acct-abc123",
    "target": "EU-acct-xyz789"
  }'
# → {"status":"Accepted","correlationId":"<uuid>"}

# Check Python agent metrics
curl http://localhost:8000/metrics
# → {"messages_processed": 1, "messages_failed": 0}
```

### Health endpoints

| Service | Liveness | Readiness |
|---|---|---|
| TypeScript API | `GET :3000/health/live` | `GET :3000/health/ready` |
| Python Agents | `GET :8000/health/live` | `GET :8000/health/ready` |
| Python Metrics | `GET :8000/metrics` | – |

---

## Local Testing

### TypeScript

```bash
cd typescript-service
npm install
npm test
```

### Python

```bash
cd python-agents
pip install -r requirements.txt
pytest tests/ -v
```

---

## Configuration Reference

All configuration is via environment variables.

### TypeScript Service

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | HTTP server port |
| `KAFKA_BROKER` | `localhost:9093` | Comma-separated Kafka broker list |
| `LOG_LEVEL` | `info` | Winston log level |

### Python Agent Service

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BROKER` | `localhost:9093` | Kafka broker address |
| `KAFKA_TOPIC` | `high-value-transactions` | Topic to consume |
| `KAFKA_GROUP_ID` | `fraud-agents-group` | Consumer group |
| `KAFKA_RETRY_ATTEMPTS` | `10` | Connection retry count |
| `KAFKA_RETRY_DELAY_S` | `5` | Seconds between retries |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASS` | `secretpassword` | Neo4j password (use a K8s Secret) |
| `HIGH_VALUE_THRESHOLD` | `10000` | Amount threshold for risk factor |
| `HIGH_CONNECTIONS_THRESHOLD` | `10` | Graph connections threshold for risk factor |
| `LOG_LEVEL` | `INFO` | Python log level |

---

## Production Deployment (AWS EKS)

### Prerequisites

- Terraform ≥ 1.5
- kubectl
- AWS credentials with EKS permissions

```bash
cd infra/terraform
terraform init
terraform plan -var="cluster_name=fraud-investigation-prod"
terraform apply
```

The Terraform configuration provisions:
- **Multi-AZ VPC** with public + private subnets
- **NAT Gateways** for private subnet egress
- **EKS cluster** (v1.30) with full control-plane logging
- **Managed node group** with auto-scaling (2–10 × `m5.large` by default)
- All required IAM roles and policy attachments

Then deploy the Kubernetes manifests:

```bash
aws eks update-kubeconfig --name fraud-investigation-prod --region us-west-2

# Create the Neo4j password secret
kubectl create secret generic fraud-investigation-secrets \
  --from-literal=neo4j_password=<YOUR_SECURE_PASSWORD>

kubectl apply -f infra/k8s/deployment.yaml
```

The manifest creates:
- `ConfigMap` with all non-secret configuration
- `Deployment` + `Service` + `HPA` for both services
- Liveness/readiness probes, resource requests/limits, non-root security context

---

## Security Considerations

- Passwords are injected via Kubernetes `Secret` (not hardcoded in manifests)
- Containers run as non-root with `readOnlyRootFilesystem: true`
- Kafka producer is configured as **idempotent** to prevent duplicate messages
- Input validation (Zod) rejects malformed or missing transaction fields before they reach the event bus
- All API responses include a `correlationId` for audit tracing

# Privacy-Preserving Multi-Agent Fraud Investigation Network

## Overview
A zero-trust, multi-agent FinTech platform designed to stream real-time transaction data and detect complex fraud rings. It integrates Federated Learning to share anomaly patterns securely across institutions without exposing Personally Identifiable Information (PII). Additionally, it leverages Explainable AI (XAI) and multi-agent orchestration to compile human-readable investigation summaries for compliance officers.

## Architecture
- **API / Ingestion (TypeScript):** Handles high-throughput transaction ingestion using Clean Architecture and Domain-Driven Design principles.
- **Event Bus (Redpanda):** Real-time message brokering for high-value transaction events.
- **Agents / ML (Python):** Consumes events, evaluates graph connections (Neo4j), runs federated model inferences (TensorFlow Federated), and orchestrates logic (LangGraph).
- **Infrastructure:** Containerized via Docker Compose for local dev, with Kubernetes manifests and Terraform for AWS EKS production deployments.

## Setup
1. Run `docker-compose up -d` to spin up Redpanda, Neo4j, the TS Service, and the Python Agents.
2. Access the API at `http://localhost:3000/api/transactions`.

## Local Testing
- TypeScript: `cd typescript-service && npm test`
- Python: `cd python-agents && pytest`
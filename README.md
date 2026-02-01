# Unified Revenue Context Engine (MVP)

## Overview
A production-grade, compliance-native platform for real-time revenue signal aggregation, context engineering, and agentic orchestration. Not a CRM, email sender, or lead database.

## Architecture
- **FastAPI (async)** backend
- **Postgres** (immutable, auditable data store)
- **Redis** (hot cache)
- **Kafka** (event backbone)
- Modular monolith structure

## Core Modules
- Signal Ingestion
- Signal Store
- Context Graph Engine
- Agent Orchestration
- Compliance & Audit
- API Gateway
- Integration Connectors

## Setup
1. Install Python 3.11+, Postgres, Redis, Kafka
2. `pip install -r requirements.txt`
3. Configure `.env` with your DB and service URLs
4. Run DB migrations (Alembic or similar)
5. Start FastAPI: `uvicorn app.api.main:app --reload`

## Setup Instructions

1. Clone repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start all services via Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
4. Run unit tests:
   ```bash
   pytest tests/
   ```

## Monitoring & Observability

### Prometheus Metrics

Access metrics at `http://localhost:8000/metrics`

**Key Metrics**:
- `intent_score_calculation_seconds` - Intent score computation latency
- `signals_processed_total{source,type,status}` - Signal processing throughput
- `cache_hits_total` / `cache_misses_total` - Cache performance
- `api_request_seconds{method,endpoint,status}` - API latency
- `kafka_consumers_active` - Active worker count

### Health Checks

- `GET /health` - Basic liveness probe
- `GET /health/detailed` - Dependency health (DB, Redis, Kafka)
- `GET /health/workers` - Worker heartbeat monitoring

### Request Tracing

All requests include `X-Request-ID` header for distributed tracing:
```bash
curl -H "X-Request-ID: trace-123" http://localhost:8000/api/signals
```

Request IDs propagate through logs and Kafka events.

### Worker Parallelism

- **3x context-engine workers** - Parallel signal processing
- **2x orchestration-engine workers** - Parallel action orchestration
- Kafka consumer groups automatically distribute load
- Each worker updates heartbeat in Redis

## Compliance
- DPDP, GDPR, CCPA native
- Immutable audit log
- Consent/erasure propagation
- Human-in-the-loop for high-risk actions

## What This Is NOT
- Not a CRM, email sender, or lead database
- No scraping of login-gated platforms
- No rule-only automation
- No polling for CRM sync

## Example: Salesforce Webhook

Send a POST request to ingest a Salesforce Opportunity update:
```bash
curl -X POST http://localhost:8000/api/integrations/salesforce/webhook \
  -H "Content-Type: application/json" \
  -d '{"AccountId": "test-account-001", "Id": "oppty-123", "StageName": "Demo Scheduled"}'
```

## Workflow
- Signal is ingested, normalized, deduplicated, stored, and published to Kafka.
- Context Engine updates intent score (time-decay weighted) in DB and publishes context.updated.
- Orchestration Engine detects high intent, creates review task (mocked), logs audit event, and publishes action.executed.

## Audit Events
- All state transitions are logged in audit_logs table.

## Test Data
- 1 test account, ICP definition, signal type weights seeded via Alembic.

## Success Criteria
- POST webhook → signal in DB
- intent_score updated in account_contexts
- Task created (mocked)
- Audit events logged

## Notes
- All DB operations are async
- Kafka is used for real eventing
- Replace mocked Salesforce API with real integration for production

## Replace all placeholder logic before production use.

## New Endpoints
- POST /api/consent: Grant consent
- GET /api/consent/{email}: Check consent
- DELETE /api/consent/{email}: Revoke consent
- GET /api/actions/pending: List pending email actions
- POST /api/actions/{id}/approve: Approve action
- POST /api/actions/{id}/reject: Reject action
- GET /api/approval/ui: Approval queue UI

## Approval Workflow Diagram

High-Intent Signal → EmailOrchestrationAgent (LLM, consent check, confidence scoring) → Approval Queue (API/UI) → Approve/Reject → Mock Outreach → Audit Log

## Approval UI
- Shows: Account context, email preview, agent reasoning side-by-side
- Approve/Reject (and edit, if enabled)

## Configuration
- .env: OPENAI_API_KEY, OUTREACH_API_KEY, EMAIL_DAILY_LIMIT_PER_ACCOUNT, HIGH_INTENT_THRESHOLD

## Alembic
- Run `alembic upgrade head` to add approval queue indexes

## Testing
- Run `pytest tests/` for unit/integration tests
- LLM responses are mocked for deterministic tests

## Compliance
- Consent is validated before proposing any email
- All approvals/rejections are logged with user_id
- No email is ever auto-executed

## Laboratory Mode Guide
- Start with `EXECUTION_MODE=laboratory` in .env
- All lab agents/tables are isolated from production
- Create, run, compare, and promote experiments via `/api/laboratory` endpoints
- Shadow execution: Lab agents read prod signals, write only to lab schema
- No external API calls or prod DB writes in lab mode

## Experiment Workflow
1. Create experiment (POST `/api/laboratory/experiments`)
2. Run experiment (POST `/api/laboratory/experiments/{id}/run`)
3. Compare results (GET `/api/laboratory/experiments/{id}/compare`)
4. Promote to production (POST `/api/laboratory/experiments/{id}/promote`)

## Context Enrichment
- Enrichment agent triggers on high-intent, low-quality context
- Budget tracked in Redis, capped at $0.50/account/month
- Mock Clearbit API for safe testing

## Metrics
- Prometheus-style: `laboratory_experiments_active`, `enrichment_api_calls_total`, `enrichment_budget_spent_dollars`, `context_quality_score_distribution`

## Safety
- Laboratory mode never writes to prod DB or calls external APIs
- Promotion requires explicit approval
- All enrichment calls logged in audit_events

## Database Optimizations

### Audit Log Partitioning
- Audit logs partitioned by month for improved query performance
- Automatic partition creation via cron job: `python scripts/create_audit_partitions.py`
- Run monthly: `0 0 1 * *`

### Performance Indexes
- Composite indexes on signals, actions, account_contexts
- GIN indexes for JSONB queries
- Partial indexes for pending approval queues

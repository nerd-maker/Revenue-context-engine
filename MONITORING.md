# Monitoring & Alerting Guide

## Metrics
- **API Latency/Error Rate**: Exposed via Prometheus, scraped by CloudWatch/Grafana
- **Kafka Lag**: Monitored via CloudWatch and Grafana dashboards
- **Postgres Health**: RDS metrics (CPU, connections, replication lag)
- **Redis Health**: ElastiCache metrics (memory, evictions, CPU)
- **Worker Throughput**: Custom Prometheus metrics for signals processed/sec
- **Per-Tenant Usage**: Usage dashboard, Prometheus metrics

## Dashboards
- **Grafana**: Unified dashboard for API, Kafka, DB, Redis, and per-tenant usage
- **CloudWatch**: Alarms for error rate, latency, resource exhaustion

## Alerting
- **PagerDuty**: Integrated with CloudWatch/Grafana for critical alerts
- **On-call Rotation**: Ensure schedule is up to date in PagerDuty

## Log Aggregation
- **CloudWatch Logs**: All FastAPI, worker, and integration logs
- **Audit Log Export**: S3 export for compliance

## Runbook for Alert Response
1. Acknowledge alert in PagerDuty
2. Check relevant dashboard (Grafana/CloudWatch)
3. Investigate logs for error context
4. Escalate if root cause is not clear
5. Document incident and resolution

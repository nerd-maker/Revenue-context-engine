# Revenue Context Engine - Operations Runbook

## Quick Reference

**Emergency Contacts**:
- On-Call Engineer: Check PagerDuty schedule
- Escalation: CTO
- Database Team: dba@company.com
- Infrastructure: devops@company.com

**Response Time SLAs**:
- P0 (Critical): 15 minutes
- P1 (High): 1 hour
- P2 (Medium): 4 hours

---

## 1. Database Failover

### Symptoms
- Health check fails: `/health/detailed` returns 503
- CloudWatch alarm: `db-cpu-high` or `db-connections-high`
- Application logs show database connection errors

### Diagnosis
```bash
# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier prod-revenue-context-db \
  --query 'DBInstances[0].DBInstanceStatus'

# Check connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=prod-revenue-context-db \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Resolution Steps

**1. Manual Failover (if Multi-AZ)**:
```bash
aws rds reboot-db-instance \
  --db-instance-identifier prod-revenue-context-db \
  --force-failover
```

**2. Monitor failover** (takes 2-5 minutes):
```bash
aws rds wait db-instance-available \
  --db-instance-identifier prod-revenue-context-db
```

**3. Verify application recovery**:
```bash
curl https://api.prod.revenue-context.com/health/detailed
```

**4. Check for connection leaks**:
```sql
SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction';
```

---

## 2. Kafka Consumer Lag

### Symptoms
- CloudWatch alarm: `kafka-lag-high`
- Worker health check stale: `/health/workers` returns 503
- Delayed signal processing

### Diagnosis
```bash
# Check consumer lag
kafka-consumer-groups.sh --bootstrap-server $KAFKA_BROKERS \
  --group context_engine_group \
  --describe

# Check worker count
aws ecs describe-services \
  --cluster prod-revenue-context \
  --services context-engine \
  --query 'services[0].runningCount'
```

### Resolution Steps

**1. Scale up workers**:
```bash
aws ecs update-service \
  --cluster prod-revenue-context \
  --service context-engine \
  --desired-count 5
```

**2. Check for processing errors**:
```bash
aws logs tail /ecs/production/context-engine --follow --filter-pattern "ERROR"
```

**3. Check Dead Letter Queue**:
```bash
kafka-console-consumer.sh --bootstrap-server $KAFKA_BROKERS \
  --topic signals.raw.dlq \
  --from-beginning \
  --max-messages 10
```

**4. If lag persists, check database performance**:
```bash
# Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## 3. API Error Rate Spike

### Symptoms
- CloudWatch alarm: `api-error-rate-high`
- 5xx errors > 5%
- Customer reports of failures

### Diagnosis
```bash
# Check ECS task health
aws ecs describe-tasks \
  --cluster prod-revenue-context \
  --tasks $(aws ecs list-tasks --cluster prod-revenue-context --service-name api --query 'taskArns' --output text)

# Check recent errors
aws logs tail /ecs/production/api --follow --filter-pattern "ERROR" --since 10m
```

### Resolution Steps

**1. Check application logs**:
```bash
aws logs tail /ecs/production/api --follow --filter-pattern "ERROR|CRITICAL"
```

**2. Check dependencies**:
```bash
curl https://api.prod.revenue-context.com/health/detailed
```

**3. Check database**:
```bash
# CPU usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=prod-revenue-context-db \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

**4. Check Redis**:
```bash
redis-cli -h $REDIS_HOST INFO stats
```

**5. If external API issue, check circuit breaker**:
```bash
curl https://api.prod.revenue-context.com/metrics | grep circuit_breaker_state
```

**6. Scale up if needed**:
```bash
aws ecs update-service \
  --cluster prod-revenue-context \
  --service api \
  --desired-count 5
```

---

## 4. LLM Budget Exhaustion

### Symptoms
- Users report "Budget exceeded" errors
- LLM API calls failing
- Email generation stopped

### Diagnosis
```bash
# Check current spend
redis-cli -h $REDIS_HOST GET "llm:spend:global:$(date +%Y-%m-%d)"

# Check budget metrics
curl https://api.prod.revenue-context.com/metrics | grep llm_budget
```

### Resolution Steps

**1. Review spend justification**:
```bash
# Check LLM call volume
curl https://api.prod.revenue-context.com/metrics | grep llm_api_calls_total
```

**2. Increase budget (if justified)**:
```bash
# Update environment variable in Secrets Manager
aws secretsmanager update-secret \
  --secret-id prod/revenue-context/config \
  --secret-string '{"LLM_DAILY_BUDGET": "200.0"}'
```

**3. Restart services to pick up new config**:
```bash
aws ecs update-service \
  --cluster prod-revenue-context \
  --service api \
  --force-new-deployment
```

**4. Monitor spend**:
```bash
watch -n 60 'redis-cli -h $REDIS_HOST GET "llm:spend:global:$(date +%Y-%m-%d)"'
```

---

## 5. Rollback Procedure

### When to Rollback
- Deployment causes error rate spike
- Performance degradation
- Critical bug discovered
- Failed smoke tests

### Steps

**1. Identify previous stable version**:
```bash
# Get current task definition
aws ecs describe-services \
  --cluster prod-revenue-context \
  --services api \
  --query 'services[0].taskDefinition'

# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix prod-api \
  --sort DESC \
  --max-items 5
```

**2. Run rollback script**:
```bash
./scripts/rollback.sh production <previous_image_tag>
```

**3. Monitor rollback**:
```bash
# Watch service status
watch -n 10 'aws ecs describe-services --cluster prod-revenue-context --services api context-engine orchestration-engine --query "services[*].[serviceName,runningCount,desiredCount]" --output table'
```

**4. Verify health**:
```bash
curl https://api.prod.revenue-context.com/health
curl https://api.prod.revenue-context.com/health/detailed
```

**5. Notify stakeholders**:
```bash
# Post to Slack
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Production rollback completed to version <previous_tag>"}'
```

---

## 6. High Memory Usage

### Symptoms
- ECS tasks being killed (OOMKilled)
- CloudWatch alarm: `ecs-memory-high`

### Resolution
```bash
# Check memory metrics
aws cloudwatch get-metric-statistics \
  --namespace ECS/ContainerInsights \
  --metric-name MemoryUtilized \
  --dimensions Name=ClusterName,Value=prod-revenue-context \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Increase task memory
# Edit task definition and update memory from 2048 to 4096
aws ecs register-task-definition --cli-input-json file://task-def.json
aws ecs update-service --cluster prod-revenue-context --service api --task-definition prod-api:NEW_REVISION
```

---

## 7. Certificate Expiration

### Prevention
- ACM certificates auto-renew if DNS validation is configured
- Set calendar reminder 30 days before expiration

### If Expired
```bash
# Request new certificate
aws acm request-certificate \
  --domain-name api.prod.revenue-context.com \
  --validation-method DNS

# Update ALB listener
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --certificates CertificateArn=$NEW_CERT_ARN
```

---

## Common Commands

### View Logs
```bash
# API logs
aws logs tail /ecs/production/api --follow

# Worker logs
aws logs tail /ecs/production/context-engine --follow

# Filter errors
aws logs tail /ecs/production/api --follow --filter-pattern "ERROR|CRITICAL"
```

### Check Service Health
```bash
# ECS services
aws ecs describe-services \
  --cluster prod-revenue-context \
  --services api context-engine orchestration-engine

# Task count
aws ecs list-tasks --cluster prod-revenue-context --service-name api
```

### Database Queries
```bash
# Connect to database
psql $DATABASE_URL

# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Check long-running queries
SELECT pid, now() - query_start as duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
ORDER BY duration DESC;
```

---

## Monitoring Dashboards

- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=production-revenue-context
- **Grafana**: https://grafana.company.com/d/revenue-context
- **PagerDuty**: https://company.pagerduty.com

---

## Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| P0 - Critical | 15 minutes | On-Call → Engineering Manager → CTO |
| P1 - High | 1 hour | On-Call → Engineering Manager |
| P2 - Medium | 4 hours | On-Call Engineer |
| P3 - Low | Next business day | Ticket queue |

---

## Post-Incident

After resolving an incident:

1. **Document** in incident log
2. **Create post-mortem** (for P0/P1)
3. **Update runbook** with learnings
4. **Create action items** to prevent recurrence

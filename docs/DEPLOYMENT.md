# Deployment Guide

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured
- Docker installed
- GitHub repository with Actions enabled

---

## Initial Setup

### 1. Configure AWS Credentials

```bash
aws configure
# Enter AWS Access Key ID, Secret Access Key, and region (us-east-1)
```

### 2. Create S3 Bucket for Terraform State

```bash
aws s3 mb s3://revenue-context-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket revenue-context-terraform-state \
  --versioning-configuration Status=Enabled
```

### 3. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name revenue-context-engine \
  --region us-east-1
```

---

## Staging Deployment

### 1. Initialize Terraform

```bash
cd terraform/environments/staging
terraform init
```

### 2. Review and Apply

```bash
# Plan
terraform plan -out=tfplan

# Review the plan carefully
# Apply
terraform apply tfplan
```

### 3. Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t revenue-context-engine:staging .

# Tag
docker tag revenue-context-engine:staging <account-id>.dkr.ecr.us-east-1.amazonaws.com/revenue-context-engine:staging

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/revenue-context-engine:staging
```

### 4. Deploy to ECS

```bash
./scripts/deploy.sh staging staging
```

### 5. Verify Deployment

```bash
# Check health
curl https://api.staging.revenue-context.com/health

# Check detailed health
curl https://api.staging.revenue-context.com/health/detailed

# Check metrics
curl https://api.staging.revenue-context.com/metrics
```

---

## Production Deployment

### 1. Apply Terraform

```bash
cd terraform/environments/prod
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 2. Configure DNS

```bash
# Create Route53 record pointing to ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch file://dns-change.json
```

### 3. Deploy via CI/CD

```bash
# Push to main branch triggers deployment
git push origin main
```

Or manually:

```bash
./scripts/deploy.sh production <image-tag>
```

### 4. Run Database Migrations

```bash
# Connect to ECS task
aws ecs execute-command \
  --cluster prod-revenue-context \
  --task <task-id> \
  --container api \
  --interactive \
  --command "/bin/bash"

# Inside container
alembic upgrade head
```

### 5. Verify Production

```bash
# Health checks
curl https://api.prod.revenue-context.com/health
curl https://api.prod.revenue-context.com/health/detailed

# Smoke test
curl -X POST https://api.prod.revenue-context.com/api/signals \
  -H "Content-Type: application/json" \
  -d '{"account_id":"test","source":"test","type":"web_visit","payload":{}}'
```

---

## Post-Deployment Checklist

- [ ] Health checks passing
- [ ] Metrics endpoint accessible
- [ ] CloudWatch alarms configured
- [ ] PagerDuty integration tested
- [ ] Grafana dashboards populated
- [ ] Database migrations applied
- [ ] Secrets rotated
- [ ] Backup/restore tested
- [ ] Load test executed
- [ ] Documentation updated
- [ ] Team trained on runbook

---

## Rollback Procedure

If deployment fails:

```bash
./scripts/rollback.sh production <previous-tag>
```

---

## Monitoring Setup

### 1. Configure PagerDuty

```bash
# Update SNS subscription
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:<account-id>:prod-revenue-context-alerts \
  --protocol https \
  --notification-endpoint <pagerduty-endpoint>
```

### 2. Import Grafana Dashboard

1. Login to Grafana
2. Navigate to Dashboards → Import
3. Upload `grafana/dashboards/revenue-context.json`
4. Select Prometheus data source

---

## Troubleshooting

### Deployment Fails

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster prod-revenue-context \
  --services api \
  --query 'services[0].events[0:5]'

# Check task logs
aws logs tail /ecs/production/api --follow
```

### Database Connection Issues

```bash
# Test RDS Proxy connection
psql -h <rds-proxy-endpoint> -U app_user -d revenue_context

# Check security groups
aws ec2 describe-security-groups --group-ids <sg-id>
```

### Certificate Issues

```bash
# Verify ACM certificate
aws acm describe-certificate --certificate-arn <cert-arn>

# Check ALB listener
aws elbv2 describe-listeners --load-balancer-arn <alb-arn>
```

# Production Deployment Guide

## Prerequisites
- AWS account with permissions for ECS, RDS, ElastiCache, MSK, S3, Secrets Manager
- Docker, Terraform, AWS CLI installed

## Steps
1. **Build Docker Images**
   - `docker build -t <repo>/revenue-platform:latest .`
   - `docker push <repo>/revenue-platform:latest`
2. **Configure Secrets**
   - Store DB, Redis, JWT, Salesforce, and email secrets in AWS Secrets Manager
3. **Provision Infrastructure**
   - `cd terraform`
   - `terraform init && terraform apply`
4. **Deploy to ECS**
   - Update ECS task definition with new image/tag
   - Deploy via AWS Console or CLI
5. **Run Alembic Migrations**
   - `alembic upgrade head` (run in ECS task or via bastion)
6. **Verify Health**
   - Check CloudWatch logs, Grafana dashboards, and API health endpoints
7. **Set Up Monitoring/Alerting**
   - Ensure CloudWatch/Grafana/PagerDuty integration is active

## Rollback
- Revert ECS task definition to previous image/tag
- Restore RDS snapshot if needed

## Security
- All secrets in AWS Secrets Manager
- Encrypted storage (RDS, S3, Redis)
- TLS for all endpoints

## Compliance
- Test GDPR, audit export, and retention endpoints
- Review runbooks and monitoring guides

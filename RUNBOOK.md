# Operational Runbooks

## Deploy New Version (Blue/Green)
1. Build and push Docker image
2. Update ECS service with new task definition
3. Wait for new tasks to pass health checks
4. Switch ALB target group to new tasks
5. Monitor logs and metrics
6. Rollback if errors detected

## Scale Workers
- Update ECS service desired count for worker tasks
- Monitor CPU/memory and Kafka lag

## Respond to API Outage
- Check CloudWatch logs for errors
- Restart ECS tasks if needed
- Check RDS/Redis health

## Handle Kafka Lag Spike
- Increase consumer task count
- Check for slow processing or deadlocks

## Restore from Backup
- Use RDS snapshot to restore DB
- Update connection string if endpoint changes

## Tenant Onboarding Checklist
- Create tenant record in DB
- Set up Salesforce OAuth
- Configure ICP/brand voice
- Test signal ingestion and approval

## Security/Compliance
- Rotate secrets in AWS Secrets Manager every 90 days
- Review audit logs monthly
- Test GDPR/data export endpoints quarterly

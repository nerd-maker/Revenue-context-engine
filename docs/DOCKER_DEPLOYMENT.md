# Docker Deployment Guide

Complete guide for deploying the Revenue Context Engine using Docker.

---

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- OpenAI API key

---

## Quick Start

### 1. Clone and Configure

```bash
cd "c:\Users\Utkarsh\Desktop\new project"

# Create .env file
cp .env.example .env

# Edit .env with your values
notepad .env
```

**Required environment variables**:
```env
# Database
DB_PASSWORD=your_secure_password_here

# Redis
REDIS_PASSWORD=your_redis_password_here

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Optional
LLM_DAILY_LIMIT_PER_ACCOUNT=10
HIGH_INTENT_THRESHOLD=70
```

### 2. Build and Start

```bash
# Build all services
docker-compose -f docker-compose.fullstack.yml build

# Start all services
docker-compose -f docker-compose.fullstack.yml up -d

# Check status
docker-compose -f docker-compose.fullstack.yml ps
```

### 3. Run Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.fullstack.yml exec backend alembic upgrade head

# Verify
docker-compose -f docker-compose.fullstack.yml exec backend alembic current
```

### 4. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Service Architecture

```
┌─────────────┐
│   Frontend  │ :80
│   (nginx)   │
└──────┬──────┘
       │
       ├─────► /api/* ────┐
       │                  │
       └─────► /ws/*  ────┤
                          ▼
                   ┌──────────────┐
                   │   Backend    │ :8000
                   │   (FastAPI)  │
                   └──────┬───────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐   ┌─────────────┐
│  PostgreSQL │    │    Redis    │   │    Kafka    │
│     :5432   │    │    :6379    │   │   :19092    │
└─────────────┘    └─────────────┘   └─────────────┘
       ▲
       │
┌──────┴────────┐
│ Context Engine│
│    Worker     │
└───────────────┘
```

---

## Management Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose.fullstack.yml logs -f

# Specific service
docker-compose -f docker-compose.fullstack.yml logs -f backend
docker-compose -f docker-compose.fullstack.yml logs -f frontend
docker-compose -f docker-compose.fullstack.yml logs -f context-engine-worker
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.fullstack.yml restart

# Restart specific service
docker-compose -f docker-compose.fullstack.yml restart backend
```

### Stop and Remove

```bash
# Stop all services
docker-compose -f docker-compose.fullstack.yml down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose -f docker-compose.fullstack.yml down -v
```

### Scale Workers

```bash
# Run 3 context engine workers
docker-compose -f docker-compose.fullstack.yml up -d --scale context-engine-worker=3
```

---

## Database Management

### Backup Database

```bash
# Create backup
docker-compose -f docker-compose.fullstack.yml exec postgres pg_dump -U postgres revenue_context > backup.sql

# With timestamp
docker-compose -f docker-compose.fullstack.yml exec postgres pg_dump -U postgres revenue_context > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose -f docker-compose.fullstack.yml exec -T postgres psql -U postgres revenue_context < backup.sql
```

### Access PostgreSQL CLI

```bash
docker-compose -f docker-compose.fullstack.yml exec postgres psql -U postgres revenue_context
```

---

## Monitoring

### Health Checks

```bash
# Check all health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl http://localhost:8000/health/workers
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics
```

### Resource Usage

```bash
# View resource usage
docker stats
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose -f docker-compose.fullstack.yml logs backend

# Common issues:
# 1. Database not ready - wait for postgres healthcheck
# 2. Missing environment variables - check .env file
# 3. Port 8000 already in use - change port in docker-compose.yml
```

### Frontend Shows 502 Error

```bash
# Check if backend is running
docker-compose -f docker-compose.fullstack.yml ps backend

# Check nginx logs
docker-compose -f docker-compose.fullstack.yml logs frontend

# Restart frontend
docker-compose -f docker-compose.fullstack.yml restart frontend
```

### Worker Not Processing Messages

```bash
# Check worker logs
docker-compose -f docker-compose.fullstack.yml logs context-engine-worker

# Check Kafka is running
docker-compose -f docker-compose.fullstack.yml ps kafka

# Restart worker
docker-compose -f docker-compose.fullstack.yml restart context-engine-worker
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.fullstack.yml ps postgres

# Test connection
docker-compose -f docker-compose.fullstack.yml exec backend python -c "from app.core.database import engine; print('Connected!')"
```

---

## Production Deployment

### Security Hardening

1. **Change default passwords**:
   ```env
   DB_PASSWORD=<strong-random-password>
   REDIS_PASSWORD=<strong-random-password>
   ```

2. **Use secrets management**:
   - Use Docker secrets or external secret manager
   - Never commit .env to git

3. **Enable HTTPS**:
   - Add SSL certificate to nginx
   - Update nginx.conf for HTTPS

4. **Restrict network access**:
   - Remove port mappings for internal services
   - Use Docker networks

### Performance Tuning

1. **Scale workers**:
   ```bash
   docker-compose -f docker-compose.fullstack.yml up -d --scale context-engine-worker=5
   ```

2. **Increase database connections**:
   - Edit `app/core/database.py` pool_size
   - Increase PostgreSQL max_connections

3. **Add caching**:
   - Already configured with Redis
   - Tune TTL values in code

---

## Updating

### Update Application Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.fullstack.yml build
docker-compose -f docker-compose.fullstack.yml up -d

# Run new migrations
docker-compose -f docker-compose.fullstack.yml exec backend alembic upgrade head
```

### Update Dependencies

```bash
# Update Python dependencies
# Edit requirements.txt, then:
docker-compose -f docker-compose.fullstack.yml build backend context-engine-worker

# Update Node dependencies
# Edit frontend/package.json, then:
docker-compose -f docker-compose.fullstack.yml build frontend
```

---

## Backup Strategy

### Automated Backups

Create a cron job:

```bash
# /etc/cron.daily/backup-revenue-context.sh
#!/bin/bash
cd /path/to/project
docker-compose -f docker-compose.fullstack.yml exec -T postgres pg_dump -U postgres revenue_context | gzip > /backups/revenue_context_$(date +\%Y\%m\%d).sql.gz

# Keep only last 30 days
find /backups -name "revenue_context_*.sql.gz" -mtime +30 -delete
```

---

## Next Steps

1. **Configure integrations**: Visit http://localhost/admin/integrations
2. **Set up ICP**: Visit http://localhost/admin/settings
3. **Invite team**: Visit http://localhost/admin/team
4. **Monitor metrics**: Visit http://localhost:8000/metrics

---

## Support

For issues, check:
- Logs: `docker-compose -f docker-compose.fullstack.yml logs`
- Health: `curl http://localhost:8000/health/detailed`
- Metrics: `curl http://localhost:8000/metrics`

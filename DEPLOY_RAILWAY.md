# Railway Deployment - Quick Start

## ✅ Your Project is Ready!

I've prepared everything for Railway deployment:

1. **✅ Created `railway.json`** - Deployment configuration
2. **✅ Made Kafka optional** - Works without Kafka on Railway
3. **✅ Verified structure** - Your folder structure is perfect!

---

## 🚀 Deploy in 5 Steps (15 minutes)

### 1. Push to GitHub

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### 2. Create Railway Project

- Go to https://railway.app/new
- Click "Deploy from GitHub repo"
- Select your repository

### 3. Add Databases

- Click "+ New" → "PostgreSQL"
- Click "+ New" → "Redis"

### 4. Set Environment Variables

Click "Variables" and add:

```env
OPENAI_API_KEY=sk-...
JWT_SECRET=<run: openssl rand -hex 32>
ENCRYPTION_KEY=<run: openssl rand -hex 32>
ENV=production
KAFKA_BOOTSTRAP_SERVERS=
```

### 5. Deploy!

Railway auto-deploys. Check logs for success.

---

## 🎯 Generate Secrets

```bash
# JWT Secret
openssl rand -hex 32

# Encryption Key
openssl rand -hex 32
```

---

## ✅ Verify Deployment

```bash
# Test health endpoint
curl https://your-app.railway.app/health

# View API docs
https://your-app.railway.app/docs
```

---

## 💰 Cost: ~$17-25/month

- PostgreSQL: $5
- Redis: $5
- Backend: $5-10
- Frontend: $2-5

---

## 📚 Full Guide

See `docs/RAILWAY_DEPLOYMENT.md` for complete instructions.

---

*Ready to deploy? Follow the 5 steps above!*

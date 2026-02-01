# Railway Deployment Guide - Unified Revenue Context Engine

## 🚀 Quick Deploy (15 Minutes)

Your project is **ready for Railway**! I've fixed the structure and made Kafka optional.

---

## ✅ What I Fixed

1. **✅ Created `railway.json`** - Railway deployment configuration
2. **✅ Made Kafka optional** - Updated `app/core/config.py`
3. **✅ Verified structure** - Your flat structure is perfect for Railway!

---

## 📋 Prerequisites

1. **GitHub Account** - Push your code to GitHub
2. **Railway Account** - Sign up at https://railway.app (free $5 credit)
3. **API Keys:**
   - OpenAI API key
   - Outreach API key (optional)
   - Other integration keys (optional)

---

## 🎯 Step-by-Step Deployment

### Step 1: Push to GitHub

```bash
# Navigate to your project
cd "C:\Users\Utkarsh\Desktop\new project"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub
4. Select your repository
5. Railway will detect it's a Python project

### Step 3: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically creates `DATABASE_URL` variable
4. Wait for database to provision (~30 seconds)

### Step 4: Add Redis

1. Click **"+ New"** again
2. Select **"Database"** → **"Redis"**
3. Railway automatically creates `REDIS_URL` variable
4. Wait for Redis to provision (~30 seconds)

### Step 5: Configure Environment Variables

In your backend service, click **"Variables"** tab and add:

```env
# Required
OPENAI_API_KEY=sk-proj-your-key-here
JWT_SECRET=<generate-with-command-below>
ENCRYPTION_KEY=<generate-with-command-below>

# Optional
OUTREACH_API_KEY=your-outreach-key
CLEARBIT_API_KEY=your-clearbit-key
SALESFORCE_CLIENT_ID=your-salesforce-id
SALESFORCE_CLIENT_SECRET=your-salesforce-secret

# Configuration
ENV=production
EXECUTION_MODE=production
HIGH_INTENT_THRESHOLD=75
EMAIL_DAILY_LIMIT_PER_ACCOUNT=5
ENRICHMENT_BUDGET_PER_ACCOUNT=0.50

# Kafka (leave empty to disable)
KAFKA_BOOTSTRAP_SERVERS=
```

**Generate Secrets:**

```bash
# Generate JWT_SECRET (32 characters)
openssl rand -hex 32

# Generate ENCRYPTION_KEY (32 characters)
openssl rand -hex 32
```

### Step 6: Deploy!

Railway will automatically deploy when you push to GitHub.

**Or deploy manually:**
1. Click **"Deploy"** in Railway dashboard
2. Wait for build (~2-3 minutes)
3. Check deployment logs

### Step 7: Run Migrations

After first deployment:

1. Click on your service
2. Go to **"Settings"** → **"Deploy"**
3. The migrations run automatically via `railway.json` startCommand
4. Or run manually: Click **"..."** → **"Run Command"** → `alembic upgrade head`

### Step 8: Verify Deployment

1. Click on your service
2. Click **"Deployments"** → **"View Logs"**
3. Look for: `Application startup complete`
4. Click **"Settings"** → **"Domains"** to get your URL
5. Test: `https://your-app.railway.app/health`

---

## 🌐 Access Your Application

### Backend API

```
https://your-backend-name.railway.app
```

**Test endpoints:**
```bash
# Health check
curl https://your-app.railway.app/health

# Detailed health
curl https://your-app.railway.app/health/detailed

# API docs
https://your-app.railway.app/docs
```

### Frontend (Optional - Deploy Separately)

1. Click **"+ New"** → **"Empty Service"**
2. Connect same GitHub repo
3. Set **Root Directory:** `/frontend`
4. **Build Command:** `npm install && npm run build`
5. **Start Command:** `npx serve -s dist -l $PORT`
6. Add environment variable:
   ```
   VITE_API_URL=https://your-backend-name.railway.app
   ```

---

## 🔧 Troubleshooting

### Issue: Build Fails

**Check logs:**
```
1. Click service → "Deployments" → "View Logs"
2. Look for error messages
```

**Common fixes:**
```bash
# Missing dependencies
# Solution: Verify requirements.txt is complete

# Python version mismatch
# Solution: Add runtime.txt with: python-3.11
```

### Issue: Database Connection Fails

**Solution:**
```
1. Verify PostgreSQL service is running
2. Check DATABASE_URL is set (Railway does this automatically)
3. Check logs for connection errors
```

### Issue: Migrations Don't Run

**Run manually:**
```bash
# In Railway dashboard:
1. Click service → "..." → "Run Command"
2. Enter: alembic upgrade head
3. Click "Run"
```

### Issue: App Crashes on Startup

**Check:**
```
1. Environment variables are set correctly
2. JWT_SECRET is not the default value
3. ENCRYPTION_KEY is set
4. Database is accessible
```

---

## 💰 Cost Estimate

### Free Tier
- **$5 credit/month** (free)
- Good for development/testing

### Paid Usage
- **PostgreSQL:** ~$5/month
- **Redis:** ~$5/month
- **Backend Service:** ~$5-10/month
- **Frontend Service:** ~$2-5/month

**Total:** ~$17-25/month

---

## 🔐 Security Checklist

- [ ] Changed JWT_SECRET from default
- [ ] Generated strong ENCRYPTION_KEY
- [ ] Set ENV=production
- [ ] OpenAI API key is secure
- [ ] Database password is strong (Railway auto-generates)
- [ ] HTTPS enabled (Railway does this automatically)

---

## 📊 Monitoring

### View Logs

```
1. Click service
2. Go to "Deployments"
3. Click "View Logs"
4. Filter by severity
```

### Metrics

Railway provides:
- CPU usage
- Memory usage
- Network traffic
- Request count

### Alerts

Set up in Railway:
1. Go to project settings
2. Click "Notifications"
3. Add webhook or email

---

## 🔄 Updates & Redeployment

### Automatic Deployment

Railway auto-deploys on git push:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

### Manual Deployment

```
1. Go to Railway dashboard
2. Click service
3. Click "Deploy" → "Redeploy"
```

---

## 🎯 Post-Deployment Tasks

### 1. Test All Endpoints

```bash
# Health check
curl https://your-app.railway.app/health

# Create test signal
curl -X POST https://your-app.railway.app/api/integrations/salesforce/webhook \
  -H "Content-Type: application/json" \
  -d '{"AccountId": "test-001", "Id": "opp-123", "StageName": "Demo Scheduled"}'
```

### 2. Set Up Custom Domain (Optional)

1. Go to service settings
2. Click "Domains" → "Custom Domain"
3. Enter your domain: `api.yourdomain.com`
4. Add CNAME record in your DNS:
   ```
   Type: CNAME
   Name: api
   Value: your-app.railway.app
   ```

### 3. Enable Monitoring

- Set up Prometheus metrics endpoint
- Configure Grafana dashboard
- Set up error tracking (Sentry)

---

## 📝 Environment Variables Reference

### Required

```env
DATABASE_URL=<auto-set-by-railway>
REDIS_URL=<auto-set-by-railway>
OPENAI_API_KEY=sk-...
JWT_SECRET=<32-char-hex>
ENCRYPTION_KEY=<32-char-hex>
ENV=production
```

### Optional

```env
OUTREACH_API_KEY=...
CLEARBIT_API_KEY=...
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
KAFKA_BOOTSTRAP_SERVERS=<leave-empty-to-disable>
EXECUTION_MODE=production
HIGH_INTENT_THRESHOLD=75
EMAIL_DAILY_LIMIT_PER_ACCOUNT=5
```

---

## 🚨 Important Notes

### Kafka is Disabled

Since Railway doesn't support Kafka, I've made it optional:

- **Current:** Kafka features disabled
- **Alternative:** Use Redis Pub/Sub for async tasks
- **Future:** Add Upstash Kafka ($10/month) or CloudKarafka

### Workers

Background workers need separate Railway service:

1. Click "+ New" → "Empty Service"
2. Same GitHub repo
3. Start Command: `python -m app.jobs.worker`

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] PostgreSQL added
- [ ] Redis added
- [ ] Environment variables set
- [ ] Secrets generated
- [ ] First deployment successful
- [ ] Migrations run
- [ ] Health check passes
- [ ] API docs accessible
- [ ] Custom domain configured (optional)

---

## 🎉 You're Live!

Your application is now deployed on Railway!

**Next Steps:**
1. Test all features
2. Monitor logs for errors
3. Set up alerts
4. Add custom domain
5. Scale as needed

---

## 📞 Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app

---

*Deployment Date: 2026-02-01*  
*Platform: Railway.app*  
*Status: Ready to Deploy*

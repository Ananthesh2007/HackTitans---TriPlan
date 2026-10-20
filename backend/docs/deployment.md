# Deployment Guide (Oct 23, 2026)

This guide covers deploying the TriPlan backend to production.

## Deployment Platform: Render

We're using Render.com for backend hosting (free tier available, easy deployment).

## Pre-Deployment Checklist

### 1. Environment Variables
Create `.env.production` or configure in Render dashboard:

```bash
# App Configuration
APP_ENV=production

# Frontend CORS - UPDATE THIS WITH YOUR LIVE FRONTEND URL
FRONTEND_ORIGINS=https://your-triplan-frontend.netlify.app,https://triplan.vercel.app

# LLM Configuration (OpenAI or Gemini)
LLM_PROVIDER=openai
LLM_API_KEY=your-actual-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT_SECONDS=45
LLM_MAX_TOKENS=4000
LLM_TEMPERATURE=0.3

# Optional: Force mock mode (set to false for production)
FORCE_MOCK_AI=false
```

### 2. Dependencies Check
Ensure `requirements.txt` has all dependencies:
```bash
cd backend
python -m pip freeze > requirements.txt
```

### 3. Security Audit
- [ ] No secrets in code (all in environment variables)
- [ ] `.env` is in `.gitignore`
- [ ] Only `.env.example` is committed
- [ ] CORS restricted to known domains
- [ ] HTTPS enforced
- [ ] Input validation via Pydantic

### 4. Database Preparation
- [ ] Database directory will be created automatically
- [ ] `backend/data/` is gitignored
- [ ] SQLite file will persist on Render's disk

## Deployment Steps

### Option 1: Render.com (Recommended)

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Select `HackTitans---TriPlan` repo

3. **Configure Service**
   ```
   Name: triplan-backend
   Region: Singapore (or closest to your users)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   - Go to "Environment" tab
   - Add all variables from `.env.production`
   - Especially important: `FRONTEND_ORIGINS` with your live frontend URL

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (5-10 minutes)
   - Note the live URL: `https://triplan-backend.onrender.com`

### Option 2: Railway.app

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `HackTitans---TriPlan`

3. **Configure**
   ```
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   - Go to Variables tab
   - Add all from `.env.production`

5. **Deploy**
   - Railway auto-deploys on push to main

## Post-Deployment Verification

### 1. Health Check
```bash
# Test the health endpoint
curl https://your-backend-url.onrender.com/health

# Expected response:
{
  "status": "ok",
  "service": "triplan-backend",
  "environment": "production"
}
```

### 2. CORS Check
```bash
# Test CORS headers
curl -H "Origin: https://your-frontend-url.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS \
  https://your-backend-url.onrender.com/api/trips

# Should see Access-Control-Allow-Origin header
```

### 3. Database Test
```bash
# Create a test trip
curl -X POST https://your-backend-url.onrender.com/api/trips \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Mumbai",
    "destination": "Goa",
    "days": 3,
    "budget": 20000,
    "people": 2,
    "travel_date": "2026-11-15",
    "interests": ["beaches", "food"],
    "diet": "none"
  }'

# Save the trip_id from response

# Retrieve the trip
curl https://your-backend-url.onrender.com/api/trips/{trip_id}

# Should return the same trip (proves database persistence works)
```

### 4. HTTPS Check
```bash
# Verify HTTPS is enforced
curl http://your-backend-url.onrender.com/health
# Should redirect to https:// or return error
```

### 5. Error Handling Test
```bash
# Test invalid input
curl -X POST https://your-backend-url.onrender.com/api/trips \
  -H "Content-Type: application/json" \
  -d '{"destination": "Paris", "days": 0}'

# Should return 422 validation error in JSON format
```

## Frontend Configuration

Update frontend to point to live backend:

```javascript
// frontend/src/config.js or similar
const API_BASE_URL = process.env.VITE_API_URL || 'https://triplan-backend.onrender.com'
```

Or in `.env` for Vite:
```bash
VITE_API_URL=https://triplan-backend.onrender.com
```

## Monitoring & Logs

### Render Logs
- Go to Render dashboard → Your service → Logs tab
- Monitor for errors after deployment
- Check database initialization logs

### Common Issues

**Issue: CORS errors**
- Solution: Add frontend URL to `FRONTEND_ORIGINS` environment variable
- Format: `https://your-frontend.com` (no trailing slash)

**Issue: Database not persisting**
- Solution: Check Render disk persistence is enabled
- Render free tier has ephemeral storage; consider upgrading for production

**Issue: Slow cold starts**
- Solution: Render free tier sleeps after 15min inactivity
- First request will be slow (30s+)
- Consider paid tier for always-on

**Issue: LLM timeout**
- Solution: Increase `LLM_TIMEOUT_SECONDS` to 60
- Or set `FORCE_MOCK_AI=true` for demo

## Rollback Plan

If deployment fails:
1. Revert to previous commit
2. Redeploy from Render dashboard
3. Check logs for errors
4. Fix issues locally, test, then redeploy

## Date: 23-10-2026 - Backend deployment to production
Status: Pending - Deploy, configure, verify all endpoints work live.

## Live API URL
Once deployed, update this with the actual URL:
```
Production API: https://_____.onrender.com
Health Check: https://_____.onrender.com/health
API Docs: https://_____.onrender.com/docs
```

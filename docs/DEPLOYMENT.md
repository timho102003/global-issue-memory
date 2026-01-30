# Deployment Guide: Vercel + Railway

This guide covers deploying the GIM (Global Issue Memory) application with:
- **Backend** on [Railway](https://railway.app) (Python MCP server)
- **Frontend** on [Vercel](https://vercel.com) (Next.js dashboard)

---

## Prerequisites

- GitHub repository with `gim/` (backend) and `frontend/` directories
- Railway account (https://railway.app)
- Vercel account (https://vercel.com)
- All external service credentials ready:
  - Supabase project URL and key
  - Qdrant Cloud cluster URL and API key
  - Google AI API key

---

## Backend: Railway

### 1. Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **New Project** → **Deploy from GitHub Repo**
3. Select your repository
4. Set **Root Directory** to `gim/`
5. Railway auto-detects the `Dockerfile` and begins building

### 2. Configure Environment Variables

In the Railway service settings, add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Supabase project URL |
| `SUPABASE_KEY` | `your-anon-key` | Supabase anon/service key |
| `QDRANT_URL` | `https://your-cluster.qdrant.io` | Qdrant Cloud URL |
| `QDRANT_API_KEY` | `your-qdrant-key` | Qdrant API key |
| `GOOGLE_API_KEY` | `your-google-key` | Google AI API key |
| `JWT_SECRET_KEY` | *(generate below)* | Min 32 characters |
| `TRANSPORT_MODE` | `http` | Required for Railway |
| `FRONTEND_URL` | *(set after Vercel deploy)* | CORS origin |
| `OAUTH_ISSUER_URL` | `https://your-backend.up.railway.app` | OAuth issuer URL |

Generate a JWT secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Note:** Do NOT set `HTTP_PORT` — Railway provides `PORT` automatically, and the Dockerfile maps it.

### 3. Verify Deployment

Once deployed, hit the health endpoint:
```bash
curl https://your-backend.up.railway.app/health
# Expected: {"status": "healthy"}
```

---

## Frontend: Vercel

### 1. Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project** → **Import Git Repository**
3. Select your repository
4. Set **Root Directory** to `frontend/`
5. Framework Preset: **Next.js** (auto-detected)

### 2. Configure Environment Variables

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_GIM_API_URL` | `https://your-backend.up.railway.app` |

### 3. Deploy

Click **Deploy**. Vercel builds and deploys automatically.

---

## Chicken-and-Egg Resolution

The backend needs the frontend URL for CORS, and the frontend needs the backend URL for API calls. Follow this order:

1. **Deploy backend first** (without `FRONTEND_URL`)
2. **Deploy frontend** with the Railway backend URL as `NEXT_PUBLIC_GIM_API_URL`
3. **Copy the Vercel URL** → go to Railway → set `FRONTEND_URL` to the Vercel URL
4. **Redeploy the backend** (Railway redeploys automatically on env var change)

---

## CI/CD

GitHub Actions workflows run automatically:

- **Backend CI** (`.github/workflows/backend-ci.yml`): Runs `pytest` on push/PR affecting `gim/**`
- **Frontend CI** (`.github/workflows/frontend-ci.yml`): Runs `lint` + `build` on push/PR affecting `frontend/**`

Both Railway and Vercel auto-deploy on push to `main`:
- Railway watches the `gim/` directory
- Vercel watches the `frontend/` directory

---

## Post-Deployment Checklist

- [ ] Backend `/health` returns 200
- [ ] Frontend loads in browser
- [ ] No CORS errors in browser console
- [ ] GIM ID creation works
- [ ] Token exchange works
- [ ] Issue search works
- [ ] Dashboard stats load

---

## Troubleshooting

### CORS Errors
- Verify `FRONTEND_URL` in Railway matches the Vercel URL exactly (including `https://`, no trailing slash)
- Check browser console for the blocked origin

### OAuth Errors
- Verify `OAUTH_ISSUER_URL` matches Railway's public URL exactly
- Ensure the URL uses `https://`

### Port Issues
- Do NOT manually set `HTTP_PORT` in Railway — Railway provides `PORT` automatically
- The Dockerfile maps `PORT` → `HTTP_PORT`

### Build Failures
- Check all required environment variables are set in the platform dashboard
- Backend requires: `SUPABASE_URL`, `SUPABASE_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `GOOGLE_API_KEY`, `JWT_SECRET_KEY`
- Frontend requires: `NEXT_PUBLIC_GIM_API_URL`

### Container Crashes
- Check Railway logs for startup errors
- Verify `TRANSPORT_MODE=http` is set
- Ensure `JWT_SECRET_KEY` is at least 32 characters

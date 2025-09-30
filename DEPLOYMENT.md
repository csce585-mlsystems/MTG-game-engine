# Deployment Guide

This guide covers multiple hosting options for your MTG Land Simulation API.

## Quick Deployment Options

### 1. Railway (Recommended - Free Tier Available)

Railway is the easiest option with excellent Python support:

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Initialize:**
   ```bash
   railway login
   cd /path/to/your/project
   railway init
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

4. **Set Environment Variables (if needed):**
   ```bash
   railway variables set PORT=8000
   ```

Your API will be live at: `https://your-app-name.railway.app`

### 2. Render (Free Tier Available)

1. **Connect GitHub Repository:**
   - Push your code to GitHub
   - Go to [render.com](https://render.com)
   - Create account and connect GitHub

2. **Create Web Service:**
   - Click "New +" → "Web Service"
   - Select your repository
   - Use these settings:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Deploy:**
   - Render will automatically deploy from your `render.yaml` config

### 3. Heroku

1. **Install Heroku CLI:**
   ```bash
   # On Ubuntu/Debian
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login and Create App:**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

### 4. Google Cloud Run

1. **Install gcloud CLI and authenticate:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and Deploy:**
   ```bash
   gcloud run deploy mtg-simulator \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### 5. DigitalOcean App Platform

1. **Connect GitHub Repository:**
   - Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
   - Create App → GitHub → Select Repository

2. **Configure:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Run Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Environment Configuration

For production deployment, you may want to set these environment variables:

```bash
# Optional: Set specific port (most platforms set this automatically)
export PORT=8000

# Optional: Set log level
export LOG_LEVEL=info

# Optional: Disable reload in production
export RELOAD=false
```

## Testing Your Deployed API

Once deployed, test your API:

```bash
# Replace YOUR_DEPLOYED_URL with your actual URL
curl https://YOUR_DEPLOYED_URL.com/health

# Test simulation
curl "https://YOUR_DEPLOYED_URL.com/simulate/quick?total_cards=60&lands_in_deck=24&num_simulations=1000"
```

## Performance Considerations

### Free Tier Limitations:
- **Railway:** 500 hours/month, sleeps after 30min inactivity
- **Render:** 750 hours/month, sleeps after 15min inactivity  
- **Heroku:** 550 hours/month, sleeps after 30min inactivity

### Optimization Tips:
1. **Cold Start:** First request after sleep may be slow (2-10 seconds)
2. **Keep Alive:** Use a service like [UptimeRobot](https://uptimerobot.com) to ping your API every 5 minutes
3. **Caching:** Consider adding Redis for caching frequent simulations
4. **Rate Limiting:** Add rate limiting for production use

## Custom Domain (Optional)

Most platforms support custom domains:

1. **Railway:** `railway domains add yourdomain.com`
2. **Render:** Add custom domain in dashboard
3. **Heroku:** `heroku domains:add yourdomain.com`

## Monitoring and Logs

View logs on each platform:

```bash
# Railway
railway logs

# Heroku  
heroku logs --tail

# Render
# View in dashboard

# Google Cloud Run
gcloud logging read "resource.type=cloud_run_revision"
```

## Security Considerations

For production use, consider:

1. **Rate Limiting:**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @app.post("/simulate")
   @limiter.limit("10/minute")
   async def simulate_land_probability(request: Request, ...):
   ```

2. **CORS Configuration:**
   ```python
   # Update CORS origins for production
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domains
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **API Keys (Optional):**
   ```python
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @app.post("/simulate")
   async def simulate_land_probability(
       request: SimulationRequest, 
       token: str = Depends(security)
   ):
   ```

## Recommended: Railway Deployment

For the quickest deployment, I recommend Railway:

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Navigate to your project
cd /home/bir4y/Desktop/csce585/MTG-game-engine

# 3. Login to Railway
railway login

# 4. Initialize project
railway init

# 5. Deploy
railway up

# 6. Get your URL
railway status
```

Your API will be live in under 2 minutes!

## Next Steps

1. Deploy using your preferred platform
2. Update the `BASE_URL` in `test_api.py` to your deployed URL
3. Test all endpoints with the deployed version
4. Share your API URL for others to use
5. Consider adding a simple web frontend

## Troubleshooting

**Common Issues:**

1. **Port Binding Error:** Make sure your app binds to `0.0.0.0:$PORT`
2. **Module Not Found:** Ensure all dependencies are in `requirements.txt`
3. **Timeout:** Increase simulation limits or add timeout handling
4. **Memory Limits:** Free tiers have memory constraints (~512MB)

**Getting Help:**
- Check platform-specific documentation
- Review deployment logs
- Test locally first with `python3 main.py`

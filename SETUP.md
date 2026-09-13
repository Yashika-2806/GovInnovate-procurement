# GovInnovate Setup Guide — External Dependencies

## Required: Google Gemini API Key

The Risk Detector agent uses Google's Gemini API for real startup risk analysis.

### Step 1: Obtain Gemini API Key

1. Go to: https://aistudio.google.com/app/apikeys
2. Click "Create API Key"
3. Copy the generated key

### Step 2: Configure Locally

Create file: `risk_backend/.env`

```
GEMINI_API_KEY=your_key_here_from_step_1
TAVILY_API_KEY=optional_for_web_search
```

**IMPORTANT**: 
- Never commit `.env` (it's in .gitignore)
- This is local configuration only
- The key is NOT sent to the repository

### Step 3: Verify Setup

```bash
# Check that the file exists
dir risk_backend\.env

# Start all services
.venv\Scripts\python.exe start.py

# In another terminal, test Risk Detector
.venv\Scripts\python.exe -c "
import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://localhost:8003/api/analyze',
            json={'problem_statement': 'Energy infrastructure'},
            timeout=10)
        print(f'Status: {r.status_code}')
        print(f'Response: {r.json()}')

asyncio.run(test())
"
```

### What Each File Does

| File | Purpose | Requires Key? |
|------|---------|---------------|
| `risk_backend/.env` | Local Gemini/Tavily config | YES (for real inference) |
| `risk_backend/main.py` | Risk Detector FastAPI entry point | YES (at startup if not stubbed) |
| `risk_backend/src/utils/llm_client.py` | Gemini SDK client | YES (raises ValueError if missing) |

### If GEMINI_API_KEY is Missing

The Risk Detector will fail at startup with:

```
ValueError: GEMINI_API_KEY not set
```

This is **intentional**. The system does NOT fall back to stubs or fake responses.

Real agent execution requires real credentials.

### Optional: Tavily Web Search

The Risk Detector can also use Tavily API for market/competitive research.

```
TAVILY_API_KEY=your_tavily_key_here
```

This is optional; Risk Detector will work with Gemini alone.

---

## Full Setup Checklist

- [ ] Python 3.12 installed
- [ ] Repository cloned
- [ ] `.venv` created: `python -m venv .venv`
- [ ] Dependencies installed: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
- [ ] `pip check` passes (no conflicts)
- [ ] `risk_backend/.env` created with GEMINI_API_KEY
- [ ] All five services start: `.venv\Scripts\python.exe start.py`
- [ ] Frontend starts: `cd frontend && npm run dev`
- [ ] Workflow test passes: `.venv\Scripts\python.exe test_integration.py`

---

## Troubleshooting

### "GEMINI_API_KEY not set"

Risk Detector requires the key in `risk_backend/.env`.

Add it and restart: `.venv\Scripts\python.exe start.py`

### "Connection refused on port 8003"

Risk Detector service failed to start. Check:

```bash
# Try starting just Risk Detector to see the error
cd risk_backend
.venv\Scripts\python.exe -c "
import sys, os
sys.path.insert(0, '.')
from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8003)
"
```

If you see `ValueError: GEMINI_API_KEY not set`, add the key to `risk_backend/.env`.

### "Service unavailable at localhost:8003"

Orchestrator failed to reach Risk Detector. This could mean:

1. Risk Detector didn't start (check GEMINI_API_KEY)
2. Port 8003 is already in use: `netstat -tlnp | grep 8003`
3. Service crashed after starting

The orchestrator will NOT fabricate a risk response. It will return:

```json
{
  "status": 503,
  "detail": "RiskDetector service unavailable at localhost:8003 (...). No AI result fabricated."
}
```

This is correct behavior.

---

## API Key Security

- **Never** commit `.env` to Git
- **Never** paste the key into chat or tickets
- **Never** expose the key in logs or error messages
- `.env` is in `.gitignore`
- Use different keys for dev/staging/prod
- Rotate keys periodically


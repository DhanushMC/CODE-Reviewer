# Secure Code Reviewer — Setup, Bug Fixes & Integration Guide

## What Was Fixed

### Backend Bugs Fixed

| File | Bug | Fix |
|------|-----|-----|
| `config.py` | `env_file = "../.env"` — breaks when running from `backend/` | Changed to `env_file = ".env"` |
| `config.py` | Default model `gpt-4-turbo` is expensive/often unavailable | Changed to `gpt-4o-mini` (affordable, capable) |
| `main.py` | `uvicorn.run(app, ...)` with `reload=True` crashes | Changed to `uvicorn.run("app.main:app", ...)` (string ref needed for reload) |
| `ml/detector.py` | Un-fine-tuned CodeBERT gives random predictions (12% confidence) — was trusted blindly | Now rule-based detection dominates; ML only used if confidence > 0.5 |
| `rag/vectordb.py` | `QdrantClient` always passed `api_key=None` — crashes Qdrant Cloud | Now conditionally creates client with or without API key |
| `rag/vectordb.py` | Upserted examples one-by-one in a loop — slow and makes many requests | Batch upsert in a single call |
| `rag/vectordb.py` | `search_similar` with language filter returns 0 results for unsupported languages — silently fails | Added fallback search without language filter |
| `rag/vectordb.py` | Used `scroll()` to compute next ID — unreliable | Changed to `count()` |
| `llm/client.py` | Language identifier stripping used hardcoded value list — missed some | Made comparison case-insensitive and more robust |
| `llm/client.py` | If LLM doesn't follow `FIXED_CODE: ... EXPLANATION:` format — returns original code silently | Added fallback code block extraction |
| `api/routes/intent.py` | `.dict()` is deprecated in Pydantic v2 | Changed to `.model_dump()` |
| `sandbox/executor.py` | `docker.from_env()` without `.ping()` — no error if Docker daemon is down | Added `client.ping()` on init |
| `sandbox/executor.py` | `cpu_quota` calculation: `int("1".replace(".", "")) * 10000 = 10000` — wrong (should be 100000 for 1 CPU) | Fixed to `float(cpu_limit) * 100000` |
| `sandbox/executor.py` | `cpu_period` not set alongside `cpu_quota` — Docker ignores `cpu_quota` without it | Added `cpu_period=100000` |
| `sandbox/executor.py` | Pytest result parsing looked for `test_` anywhere in the line — false positives | Changed to look for ` PASSED` / ` FAILED` markers in pytest's actual output format |

### Frontend Bugs Fixed

| File | Bug | Fix |
|------|-----|-----|
| `app/layout.tsx` | `globals.css` was NEVER imported — **zero styles applied** | Added `import './globals.css'` |
| `app/results/page.tsx` | `useSearchParams()` used without `<Suspense>` — Next.js 13+ build error | Wrapped in `<Suspense>` with inner component pattern |
| `app/intent/page.tsx` | Same `useSearchParams` without `<Suspense>` | Fixed same way |
| `app/fix/page.tsx` | Same `useSearchParams` without `<Suspense>` | Fixed same way |
| `app/tests/page.tsx` | Same `useSearchParams` without `<Suspense>` | Fixed same way |
| `app/approve/page.tsx` | Same `useSearchParams` without `<Suspense>` | Fixed same way |
| `lib/api.ts` | All API calls threw generic "Analysis failed" — no details from backend | Added `apiFetch()` helper that extracts FastAPI `detail` from error responses |
| `app/results/page.tsx` | `severityColors[result.severity]` — no null check, crashes if severity is null | Added fallback for null severity |
| `docker-compose.yml` | No Dockerfiles existed but `build:` was specified | Created `backend/Dockerfile` and `frontend/Dockerfile` |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (for sandbox execution)
- An OpenRouter API key → https://openrouter.ai

### Step 1: Environment Setup

Copy and fill in `.env`:
```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000
```

---

### Step 2: Start Qdrant (Vector DB)

**Option A — Docker (recommended):**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Option B — Via docker-compose:**
```bash
docker-compose up qdrant
```

The first time the backend starts, it will auto-populate 7 vulnerability example patterns.

---

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

---

### Step 4: Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be at: http://localhost:3000

---

### Step 5 (Optional): Full Docker Stack

```bash
# From project root:
docker-compose up --build
```

---

## Integrating External Services

### 1. OpenRouter (LLM)

The system uses OpenRouter as an LLM gateway, which supports GPT-4o-mini, Claude, Mistral, etc.

1. Sign up at https://openrouter.ai
2. Go to **Keys** → Create new key
3. Add to `.env`: `OPENROUTER_API_KEY=sk-or-v1-...`

To change the model, edit `config.py`:
```python
openrouter_model: str = "openai/gpt-4o-mini"   # cheapest + fast
# or:
openrouter_model: str = "anthropic/claude-3-haiku"
openrouter_model: str = "openai/gpt-4o"
```

---

### 2. Qdrant Cloud (Production Vector DB)

For production, use Qdrant Cloud instead of local Docker:

1. Sign up at https://cloud.qdrant.io
2. Create a cluster → copy the **URL** and **API Key**
3. Update `.env`:
```env
QDRANT_URL=https://xxxx.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

---

### 3. Docker Sandbox (for running tests)

The sandbox executes generated tests inside isolated Docker containers.

**Requirements:**
- Docker Desktop must be running on the host
- The backend needs access to the Docker socket

For local dev: Docker Desktop is sufficient — `docker.from_env()` connects automatically.

For Docker-in-Docker (when backend itself runs in Docker):
- The `docker-compose.yml` already mounts `/var/run/docker.sock` into the backend container
- This is a "sibling container" pattern — safe for dev/demo

---

### 4. Fine-Tuning CodeBERT (for production ML accuracy)

Currently the CodeBERT model is loaded with **base weights** (not trained on vulnerability data). This means the ML component gives unreliable results — the system relies on rule-based detection.

To use the ML component properly:

1. **Get a vulnerability dataset:**
   - [Big-Vul](https://github.com/ZeoVan/MSR_20_Code_vulnerability_suggestion_BigVul)
   - [Devign](https://sites.google.com/view/devign)
   - [NVD CVE Dataset](https://nvd.nist.gov/developers/vulnerabilities)

2. **Fine-tune the model** using the classifier in `ml/detector.py`:
```python
# Training snippet (run separately):
from transformers import Trainer, TrainingArguments
# ... load dataset, tokenize, train VulnerabilityClassifier
model.save_pretrained("models/codebert-vuln-finetuned")
```

3. **Load fine-tuned weights** in `detector.py`:
```python
# In VulnerabilityDetector.__init__:
self.model.load_state_dict(
    torch.load("models/codebert-vuln-finetuned/pytorch_model.bin")
)
```

---

## Project Architecture (Quick Reference)

```
User uploads code
     ↓
Phase 1: /api/analyze
  └─ CodeBERT + rule-based → vulnerability_type, session_id
     ↓ (if vulnerable)
Phase 2: /api/explain  
  └─ LLM + Qdrant RAG → explanation, similar_examples
     ↓ (user accepts)
Phase 3: /api/intent
  └─ Store developer intent (purpose, valid/invalid cases, constraints)
     ↓
Phase 4: /api/fix
  └─ LLM + intent + RAG → fixed_code
     ↓
Phase 5: /api/generate-tests
  └─ LLM + intent → pytest/jest test file
     ↓
Phase 6: /api/run-tests
  └─ Docker sandbox → test results (pass/fail)
     ↓ (if all pass)
Phase 7: /api/approve
  └─ User approves → final_code returned for download
```

---

## Running the Full Demo

1. Start backend + qdrant (see above)
2. Open http://localhost:3000
3. Paste this vulnerable Python code:
```python
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()
```
4. Select **Python**, click **Analyze Code**
5. The system will detect SQL Injection → click **Get Detailed Explanation**
6. Click **Yes, Fix It** → Fill in intent → Submit
7. Review fix → Generate tests → Run in sandbox → Approve

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `OPENROUTER_API_KEY not configured` | Add key to `.env` and restart backend |
| `Session not found (404)` | Sessions are in-memory. If backend restarts, start fresh from `/analyze` |
| `Docker not available` | Start Docker Desktop. Tests will fail gracefully without it |
| `Qdrant connection refused` | Run `docker run -p 6333:6333 qdrant/qdrant` |
| Frontend has no styling | Ensure `globals.css` is imported in `layout.tsx` (already fixed) |
| `useSearchParams` build error | All pages are now wrapped in `<Suspense>` (already fixed) |
| ML gives wrong vulnerability type | Expected — CodeBERT is not fine-tuned. Rule-based detection is the reliable signal |

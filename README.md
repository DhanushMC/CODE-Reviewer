# Intent-Aware AI Secure Code Reviewer

Professional full-stack web application for ML-based vulnerability detection with intent-aware code correction and sandbox validation.

**SEM-8 Final Year Project** | Academic + Enterprise Grade

---

## 🎯 Project Overview

This system provides **automated, intelligent security code review** using:
- **Phase 1 (SEM-7)**: CodeBERT ML-based vulnerability detection + RAG knowledge base
- **Phase 2 (SEM-8 - NOVELTY)**: Intent-aware code fixing with LLM + sandbox validation

### Key Features

✅ **ML-Based Detection** - CodeBERT neural network with rule-based refinement  
✅ **7 Vulnerability Types** - SQL Injection, XSS, Command Injection, Path Traversal, Hardcoded Secrets, Weak Crypto, XXE  
✅ **7 Programming Languages** - Python, JavaScript, Java, C++, C#, Go, PHP  
✅ **Intent Capture (SEM-8 Novelty)** - Developer specifies purpose & constraints before fixes  
✅ **RAG-Enhanced Explanations** - Qdrant vector DB with similar vulnerability examples  
✅ **Intent-Aware Fixing** - LLM generates fixes respecting developer intent  
✅ **Automated Test Generation** - Creates tests that fail on vulnerable, pass on fixed code  
✅ **Docker Sandbox Execution** - Isolated, resource-limited test validation  
✅ **Professional UI** - Next.js with glassmorphism, gradients, and modern aesthetics

---

## 🏗️ Architecture

```
User Upload Code
        ↓
ML Detection (CodeBERT + Rules) → If Safe → END
        ↓
LLM Explanation + RAG Examples
        ↓
User Acceptance Gate
        ↓
Intent Capture (SEM-8 Novelty)
        ↓
Intent-Aware Fix (LLM + RAG)
        ↓
Unit Test Generation
        ↓
Sandbox Execution (Docker)
        ↓
Final Approval → Apply Fix
```

### Tech Stack

**Frontend**
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- Lucide Icons

**Backend**
- FastAPI (Python)
- PyTorch + Transformers (CodeBERT)
- Qdrant (Vector DB)
- OpenRouter API (LLM)
- Docker (Sandbox)

---

## 🚀 Setup Instructions

### Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.10+
- **Docker** Desktop
- **Qdrant** (local or cloud)
- **OpenRouter API Key**

### 1. Clone Repository

```bash
cd d:/FINALyearPROJECT/SEM8
cd secure-code-reviewer
```

### 2. Environment Configuration

Create `.env` file in project root:

```env
# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Qdrant Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. Start Qdrant (Vector Database)

**Option A: Docker**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Option B: Cloud**
- Sign up at [qdrant.tech](https://qdrant.tech/)
- Update `QDRANT_URL` and `QDRANT_API_KEY` in `.env`

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start server
python -m app.main
```

Backend runs at: `http://localhost:8000`

API Docs: `http://localhost:8000/docs`

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

## 📖 Usage Guide

### Step-by-Step Workflow

1. **Open Application**
   - Navigate to `http://localhost:3000`
   - Click "Start Code Review"

2. **Upload Code**
   - Select programming language
   - Paste vulnerable code
   - Click "Analyze Code"

3. **View Results**
   - **If Safe**: Success message, no fix needed
   - **If Vulnerable**: View type, severity, confidence, evidence

4. **Get Explanation**
   - Click "Get Detailed Explanation"
   - Review natural language explanation
   - See similar vulnerability examples from RAG

5. **Accept/Reject**
   - Click "Yes, Fix It" to proceed
   - Click "No, Cancel" to stop

6. **Capture Intent (SEM-8 Novelty)**
   - Describe function purpose
   - Add valid input test cases
   - Add invalid input test cases
   - Select security constraints
   - Select side effects
   - Submit intent

7. **Review Fix**
   - View side-by-side diff (vulnerable vs fixed)
   - Read fix explanation
   - Click "Generate Tests"

8. **Review Tests**
   - View generated test code
   - See test descriptions
   - Click "Run Tests in Sandbox"

9. **Test Results**
   - **If Pass**: Proceed to approval
   - **If Fail**: Fix rejected, review errors

10. **Final Approval**
    - Review summary
    - Click "Apply Fix" to accept
    - Click "Reject Fix" to cancel

11. **Success**
    - Download fixed code
    - View final secure implementation

---

## 🧪 Example: Testing SQL Injection

**Vulnerable Python Code:**
```python
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()
```

**Expected Workflow:**
1. System detects SQL_INJECTION with HIGH severity
2. Explains concatenation vulnerability
3. Shows RAG examples of parameterized queries
4. You specify intent: "Fetch user by ID, reject non-numeric input"
5. System fixes using `cursor.execute(query, (user_id,))`
6. Generates tests including SQL injection attempts
7. Tests pass in sandbox
8. You approve, download secure code

---

## 📁 Project Structure

```
secure-code-reviewer/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── ml/              # CodeBERT detector
│   │   ├── rag/             # Qdrant vector DB
│   │   ├── llm/             # OpenRouter client
│   │   ├── sandbox/         # Docker executor
│   │   ├── schemas/         # Pydantic models
│   │   └── utils/           # Session management
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Landing
│   │   ├── analyze/         # Code upload
│   │   ├── results/         # Vulnerability display
│   │   ├── intent/          # Intent capture (SEM-8)
│   │   ├── fix/             # Fix preview
│   │   ├── tests/           # Test preview & execution
│   │   ├── approve/         # Final approval
│   │   ├── success/         # Success page
│   │   └── safe/            # No vulnerability page
│   └── lib/api.ts           # API client
│
└── .env                     # Configuration
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | ML-based vulnerability detection |
| `/api/explain` | POST | LLM explanation + RAG examples |
| `/api/intent` | POST | Capture developer intent |
| `/api/fix` | POST | Generate intent-aware fix |
| `/api/generate-tests` | POST | Create unit tests |
| `/api/run-tests` | POST | Execute tests in sandbox |
| `/api/approve` | POST | Final approval/rejection |
| `/health` | GET | Health check |

Full API documentation: `http://localhost:8000/docs`

---

## 🧠 SEM-8 Novelty: Intent-Aware Fixing

**Problem**: Traditional auto-fix tools often:
- Break existing logic
- Add unnecessary features
- Ignore developer's actual purpose

**Solution**: Intent Capture
- Developer explicitly states function purpose
- Provides valid/invalid input examples
- Specifies security constraints & side effects
- LLM uses this to generate **context-aware** fixes

**Example Intent:**
```json
{
  "purpose": "Fetch user by ID from database",
  "valid_cases": [
    {"input": "123", "expected": "Return user object"}
  ],
  "invalid_cases": [
    {"input": "abc", "expected": "Raise ValueError"}
  ],
  "security_constraints": ["no_sql_injection"],
  "side_effects": ["read_only"]
}
```

LLM generates fix that:
- Fixes SQL injection
- Preserves read-only behavior
- Validates input as expected
- Maintains original signature

---

## 🔒 Security Features

- **No Auto-Fix**: User approval required at every gate
- **Sandbox Isolation**: Docker containers with no network, resource limits
- **ML Detection**: Not LLM guessing - actual neural network classification
- **RAG Validation**: Fixes based on verified secure patterns
- **Test Validation**: Fixes must pass security exploit tests

---

## 🎓 Academic Context

**Semester 7 (Completed)**
- Knowledge base creation
- Vulnerability detection
- Explanation generation

**Semester 8 (This Project)**
- **Novelty**: Intent-aware code correction
- Automated test generation
- Sandbox validation
- Professional web UI

---

## 🐛 Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (need 3.10+)
- Install dependencies: `pip install -r requirements.txt`
- Verify OpenRouter API key in `.env`

**Frontend won't start:**
- Check Node version: `node --version` (need 18+)
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

**Qdrant connection failed:**
- Ensure Qdrant is running: `docker ps | grep qdrant`
- Check `QDRANT_URL` in `.env`

**Tests failing in sandbox:**
- Ensure Docker Desktop is running
- Check Docker daemon: `docker ps`
- Verify image access: `docker pull python:3.11-slim`

**LLM requests failing:**
- Verify OpenRouter API key
- Check balance/credits at OpenRouter dashboard
- Try different model in `backend/app/config.py`

---

## 📊 Supported Languages & Vulnerabilities

**Languages**: Python, JavaScript, Java, C++, C#, Go, PHP

**Vulnerabilities**:
1. SQL Injection
2. Cross-Site Scripting (XSS)
3. Command Injection
4. Path Traversal
5. Hardcoded Secrets
6. Weak Cryptography
7. XML External Entity (XXE)

---

## 🤝 Contributing

This is a final-year academic project. For production use, consider:
- Fine-tuning CodeBERT on larger vulnerability datasets
- Adding more language support
- Implementing persistent session storage (Redis)
- Adding user authentication
- Expanding test framework support
- Creating CI/CD pipeline

---

## 📝 License

Academic Project - SEM-8 Final Year  
Intent-Aware AI Secure Code Reviewer

---

## 🙏 Acknowledgments

- **CodeBERT**: Microsoft Research
- **OpenRouter**: LLM API aggregation
- **Qdrant**: Vector database
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework

---

**Built with ❤️ for secure software development**

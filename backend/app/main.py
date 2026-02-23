from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import analyze, explain, intent, fix, tests, sandbox, git_fetch, detect

app = FastAPI(
    title="Secure Code Reviewer API",
    description="Intent-Aware AI-Driven Vulnerability Detection and Correction System",
    version="1.0.0"
)

# CORS Configuration
# BUG FIX: settings.allowed_origins could be a single URL or comma-separated list
origins = [o.strip() for o in settings.allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "secure-code-reviewer-api"}

# Register Routes
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(explain.router, prefix="/api", tags=["Explanation"])
app.include_router(intent.router, prefix="/api", tags=["Intent"])
app.include_router(fix.router, prefix="/api", tags=["Fixing"])
app.include_router(tests.router, prefix="/api", tags=["Testing"])
app.include_router(sandbox.router, prefix="/api", tags=["Sandbox"])
app.include_router(git_fetch.router, prefix="/api", tags=["Git"])
app.include_router(detect.router, prefix="/api", tags=["Detection"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # BUG FIX: pass app as string for reload to work

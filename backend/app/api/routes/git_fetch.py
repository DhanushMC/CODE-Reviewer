from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import subprocess
import shutil

router = APIRouter()

LANGUAGE_EXTENSIONS = {
    "python":     [".py"],
    "javascript": [".js", ".ts", ".jsx", ".tsx"],
    "java":       [".java"],
    "cpp":        [".cpp", ".cc", ".c", ".h", ".hpp"],
    "csharp":     [".cs"],
    "go":         [".go"],
    "php":        [".php"],
}

IGNORED_DIRS = {
    "node_modules", "__pycache__", ".git", "vendor",
    "dist", "build", ".next", "venv", "env", ".venv",
    "target", "bin", "obj", "out"
}

MAX_FILES = 20
MAX_FILE_SIZE_BYTES = 100_000  # 100 KB per file


class GitFetchRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    language: str = "python"


class GitFetchResponse(BaseModel):
    code: str
    file_count: int
    files: list[str]


@router.post("/git-fetch", response_model=GitFetchResponse)
async def fetch_git_repo(request: GitFetchRequest):
    """
    Clone a public Git repository and extract source files for analysis.
    Supports GitHub, GitLab, Bitbucket (public repos only).
    """
    # Validate URL
    url = request.repo_url.strip()
    if not url.startswith(("https://", "http://")):
        raise HTTPException(status_code=400, detail="Invalid repository URL. Must start with https://")

    # Block obviously bad URLs
    blocked = ["localhost", "127.0.0.1", "0.0.0.0", "internal", "169.254"]
    if any(b in url for b in blocked):
        raise HTTPException(status_code=400, detail="Internal/local URLs are not allowed")

    extensions = LANGUAGE_EXTENSIONS.get(request.language, [".py"])
    tmpdir = tempfile.mkdtemp()

    try:
        # Clone with shallow clone (faster, less data)
        clone_cmd = [
            "git", "clone",
            "--depth", "1",
            "--branch", request.branch,
            "--single-branch",
            url,
            tmpdir
        ]

        result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )

        if result.returncode != 0:
            # Try without branch (use default branch)
            clone_cmd_no_branch = [
                "git", "clone", "--depth", "1", url, tmpdir
            ]
            result2 = subprocess.run(
                clone_cmd_no_branch,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result2.returncode != 0:
                err = result2.stderr[:300] if result2.stderr else "Unknown error"
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to clone repository: {err}"
                )

        # Walk directory and collect source files
        code_files = []
        file_paths = []

        for root, dirs, files in os.walk(tmpdir):
            # Skip ignored directories in-place (modifies dirs to stop os.walk from descending)
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]

            for filename in files:
                if len(code_files) >= MAX_FILES:
                    break

                if not any(filename.endswith(ext) for ext in extensions):
                    continue

                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, tmpdir)

                # Skip large files
                try:
                    if os.path.getsize(full_path) > MAX_FILE_SIZE_BYTES:
                        continue
                except OSError:
                    continue

                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    code_files.append(f"// ===== FILE: {relative_path} =====\n{content}")
                    file_paths.append(relative_path)
                except Exception:
                    continue

        if not code_files:
            raise HTTPException(
                status_code=404,
                detail=f"No {request.language} files found in the repository. "
                       f"Check the language selection or repository contents."
            )

        combined_code = "\n\n".join(code_files)

        return GitFetchResponse(
            code=combined_code,
            file_count=len(code_files),
            files=file_paths
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Repository clone timed out. Repository may be too large.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git fetch failed: {str(e)}")
    finally:
        # Always cleanup temp directory
        shutil.rmtree(tmpdir, ignore_errors=True)

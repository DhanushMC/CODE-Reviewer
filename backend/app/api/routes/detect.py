from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import re

router = APIRouter()


class DetectRequest(BaseModel):
    code: str
    filename: Optional[str] = None


class DetectionResult(BaseModel):
    language: str
    language_confidence: float
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    runtime: Optional[str] = None
    api_endpoints: List[Dict[str, str]] = []
    dependencies: List[str] = []
    file_types: List[str] = []
    project_type: Optional[str] = None  # "web_api", "cli", "library", "frontend", etc.
    database: Optional[str] = None
    auth_mechanisms: List[str] = []
    summary: str = ""


# ─── Language detection patterns ──────────────────────────────────────────────

LANGUAGE_PATTERNS = {
    "python": {
        "keywords": [r'\bdef\b', r'\bimport\b', r'\bfrom\b.*\bimport\b', r'\bclass\b.*:', r'if __name__.*main'],
        "syntax":   [r'^\s*#', r'\.py\b', r'print\(', r':\s*$'],
        "weight":   1.0
    },
    "javascript": {
        "keywords": [r'\bconst\b', r'\blet\b', r'\bvar\b', r'=>', r'\bfunction\b', r'require\(', r'module\.exports'],
        "syntax":   [r'console\.log', r'\.js\b', r'async\s+function', r'\.then\('],
        "weight":   1.0
    },
    "typescript": {
        "keywords": [r':\s*string\b', r':\s*number\b', r':\s*boolean\b', r'interface\s+\w+', r'type\s+\w+\s*=', r'<T>'],
        "syntax":   [r'\.ts\b', r'\.tsx\b', r'import\s+type\b'],
        "weight":   1.1  # slightly higher than JS
    },
    "java": {
        "keywords": [r'\bpublic\s+class\b', r'\bprivate\b', r'\bprotected\b', r'System\.out\.println', r'\bvoid\b', r'@Override'],
        "syntax":   [r'\.java\b', r'import\s+java\.', r'new\s+\w+\('],
        "weight":   1.0
    },
    "cpp": {
        "keywords": [r'#include\s*<', r'\bstd::', r'\bcout\b', r'\bcin\b', r'int\s+main\s*\('],
        "syntax":   [r'\.cpp\b', r'\.cc\b', r'namespace\s+\w+'],
        "weight":   1.0
    },
    "csharp": {
        "keywords": [r'\bnamespace\b', r'\busing\s+System\b', r'\bConsole\.Write', r'\bpublic\s+static\b', r'\[HttpGet\]'],
        "syntax":   [r'\.cs\b', r'var\s+\w+\s*=\s*new\b'],
        "weight":   1.0
    },
    "go": {
        "keywords": [r'\bpackage\s+main\b', r'\bfunc\b', r'\bfmt\.', r':=', r'\bgo\s+func\b', r'\bchan\b'],
        "syntax":   [r'\.go\b', r'import\s+\('],
        "weight":   1.0
    },
    "php": {
        "keywords": [r'<\?php', r'\$\w+\s*=', r'echo\s+', r'function\s+\w+\s*\(', r'\$_POST\b', r'\$_GET\b'],
        "syntax":   [r'\.php\b', r'->\w+\('],
        "weight":   1.0
    },
    "ruby": {
        "keywords": [r'\bdef\s+\w+\b', r'\bend\b', r'\bputs\b', r'\brequire\b', r'\battr_accessor\b'],
        "syntax":   [r'\.rb\b', r'\|.*\|'],
        "weight":   1.0
    },
    "rust": {
        "keywords": [r'\bfn\s+main\b', r'\blet\s+mut\b', r'\buse\s+std::', r'\bmatch\b', r'\bimpl\b', r'->.*\{'],
        "syntax":   [r'\.rs\b', r'println!\('],
        "weight":   1.0
    },
}

# ─── Framework detection patterns ─────────────────────────────────────────────

FRAMEWORK_PATTERNS = {
    # Python frameworks
    "FastAPI":   [r'from\s+fastapi\s+import', r'FastAPI\(\)', r'@app\.(get|post|put|delete|patch)\(', r'APIRouter\(\)'],
    "Flask":     [r'from\s+flask\s+import', r'Flask\(__name__\)', r'@app\.route\(', r'render_template\('],
    "Django":    [r'from\s+django\b', r'django\.db\.models', r'urlpatterns\s*=', r'INSTALLED_APPS\s*='],
    "Tornado":   [r'import\s+tornado', r'tornado\.web\.Application', r'RequestHandler'],
    "aiohttp":   [r'from\s+aiohttp\s+import', r'aiohttp\.web', r'web\.Application\(\)'],

    # JS/TS frameworks
    "Express":   [r'require\([\'"]express[\'"]\)', r'express\(\)', r'app\.(get|post|put|delete|use)\(', r'Router\(\)'],
    "NestJS":    [r'@Controller\(', r'@Injectable\(', r'@Module\(', r'from\s+[\'"]@nestjs/'],
    "Next.js":   [r'from\s+[\'"]next/', r'getServerSideProps', r'getStaticProps', r'useRouter\(\)'],
    "React":     [r'from\s+[\'"]react[\'"]', r'useState\(', r'useEffect\(', r'ReactDOM\.render', r'jsx'],
    "Vue":       [r'from\s+[\'"]vue[\'"]', r'createApp\(', r'v-model', r'defineComponent\('],
    "Koa":       [r'require\([\'"]koa[\'"]\)', r'new\s+Koa\(\)', r'ctx\.body\s*='],
    "Hapi":      [r'require\([\'"]@hapi/hapi[\'"]\)', r'Hapi\.server\('],

    # Java frameworks
    "Spring Boot": [r'@SpringBootApplication', r'@RestController', r'@RequestMapping', r'@Autowired', r'SpringApplication\.run'],
    "Quarkus":     [r'@QuarkusMain', r'import\s+io\.quarkus', r'@Path\('],
    "Micronaut":   [r'@MicronautTest', r'import\s+io\.micronaut'],

    # PHP frameworks
    "Laravel":  [r'use\s+Illuminate\\', r'Route::get\(', r'Eloquent', r'artisan'],
    "Symfony":  [r'use\s+Symfony\\', r'@Route\(', r'ContainerInterface'],
    "CodeIgniter": [r'CI_Controller', r'\$this->load->'],

    # Go frameworks
    "Gin":   [r'gin\.New\(\)', r'gin\.Default\(\)', r'c\.JSON\(', r'"github\.com/gin-gonic/gin"'],
    "Echo":  [r'echo\.New\(\)', r'"github\.com/labstack/echo"', r'c\.String\('],
    "Fiber": [r'fiber\.New\(\)', r'"github\.com/gofiber/fiber"'],

    # Ruby
    "Rails":   [r'Rails\.application', r'ActiveRecord::Base', r'ActionController::Base'],
    "Sinatra": [r'require\s+[\'"]sinatra[\'"]', r'get\s+[\'"]/', r'post\s+[\'"]/', ],
}

# ─── API endpoint extraction ───────────────────────────────────────────────────

ENDPOINT_PATTERNS = [
    # FastAPI / Flask
    {"regex": r'@(?:app|router)\.(get|post|put|delete|patch|options)\s*\(\s*["\']([^"\']+)["\']',
     "method_group": 1, "path_group": 2},
    # Django urls
    {"regex": r'path\s*\(\s*["\']([^"\']*)["\']',
     "method_group": None, "path_group": 1},
    # Express
    {"regex": r'(?:app|router)\.(get|post|put|delete|patch|use)\s*\(\s*["\']([^"\']+)["\']',
     "method_group": 1, "path_group": 2},
    # Spring Boot
    {"regex": r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']',
     "method_group": 1, "path_group": 2},
    # NestJS
    {"regex": r'@(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']*)["\']',
     "method_group": 1, "path_group": 2},
    # Gin/Echo/Fiber (Go)
    {"regex": r'\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["\']([^"\']+)["\']',
     "method_group": 1, "path_group": 2},
    # Rails
    {"regex": r'(?:get|post|put|delete|patch)\s+["\']([^"\']+)["\']',
     "method_group": None, "path_group": 1},
]

# ─── Database detection ────────────────────────────────────────────────────────

DATABASE_PATTERNS = {
    "PostgreSQL":  [r'psycopg2', r'postgresql', r'pg\.Pool', r'asyncpg', r'POSTGRES'],
    "MySQL":       [r'mysql', r'pymysql', r'MySQLdb', r'createConnection.*mysql'],
    "SQLite":      [r'sqlite3', r'SQLite', r'\.db\b'],
    "MongoDB":     [r'pymongo', r'MongoClient', r'mongoose', r'mongodb://'],
    "Redis":       [r'redis', r'Redis\(', r'aioredis'],
    "Elasticsearch": [r'elasticsearch', r'ElasticSearch'],
    "Cassandra":   [r'cassandra', r'CassandraCluster'],
    "Oracle":      [r'cx_Oracle', r'oracle'],
    "SQL Server":  [r'pyodbc', r'mssql', r'sqlserver'],
    "DynamoDB":    [r'dynamodb', r'DynamoDB'],
    "Supabase":    [r'supabase', r'createClient.*supabase'],
    "Prisma":      [r'PrismaClient', r'from\s+[\'"]@prisma/client[\'"]'],
    "SQLAlchemy":  [r'SQLAlchemy', r'from\s+sqlalchemy', r'create_engine\('],
}

# ─── Auth mechanism detection ──────────────────────────────────────────────────

AUTH_PATTERNS = {
    "JWT":         [r'jwt', r'JSON Web Token', r'Bearer\s+', r'jsonwebtoken', r'PyJWT'],
    "OAuth2":      [r'oauth2', r'OAuth', r'authorization_code', r'client_credentials'],
    "Basic Auth":  [r'BasicAuth', r'Authorization.*Basic', r'base64.*password'],
    "API Key":     [r'api[_-]?key', r'x-api-key', r'apiKey'],
    "Session":     [r'session\[', r'req\.session', r'flask\.session', r'SessionMiddleware'],
    "Passport.js": [r'passport\.use\(', r'passport\.authenticate\('],
    "Django Auth": [r'@login_required', r'django\.contrib\.auth', r'authenticate\('],
}

# ─── Project type detection ────────────────────────────────────────────────────

PROJECT_TYPE_PATTERNS = {
    "REST API":        [r'@app\.(get|post|put|delete)', r'Router\(\)', r'@RestController', r'gin\.New\(\)'],
    "GraphQL API":     [r'graphql', r'GraphQL', r'type\s+Query\s*{', r'Resolver'],
    "Frontend App":    [r'useState\(', r'useEffect\(', r'render\(', r'<App\s*/>', r'ReactDOM'],
    "Full Stack":      [r'getServerSideProps', r'getStaticProps', r'Next\.js', r'Nuxt'],
    "CLI Tool":        [r'argparse', r'click\.command', r'sys\.argv', r'commander', r'yargs'],
    "Background Worker": [r'celery', r'dramatiq', r'bull', r'Queue\(', r'@task'],
    "WebSocket Server": [r'WebSocket\(', r'socket\.io', r'ws\b', r'on\([\'"]connection[\'"]'],
    "Microservice":    [r'grpc', r'protobuf', r'service\s+\w+\s*\{', r'rpc\s+\w+\s*\('],
    "Library/SDK":     [r'setup\.py', r'pyproject\.toml', r'package\.json.*version', r'module\.exports\s*='],
}


def detect_language(code: str, filename: Optional[str] = None) -> tuple[str, float]:
    """Detect programming language from code content."""
    scores: Dict[str, float] = {}

    # Filename hint (strong signal)
    if filename:
        ext_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
            ".cpp": "cpp", ".cc": "cpp", ".c": "cpp",
            ".cs": "csharp", ".go": "go", ".php": "php",
            ".rb": "ruby", ".rs": "rust",
        }
        for ext, lang in ext_map.items():
            if filename.endswith(ext):
                scores[lang] = scores.get(lang, 0) + 5.0  # strong boost

    # Pattern matching
    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0.0
        for pattern in patterns["keywords"]:
            matches = len(re.findall(pattern, code, re.IGNORECASE | re.MULTILINE))
            score += matches * 2.0
        for pattern in patterns["syntax"]:
            matches = len(re.findall(pattern, code, re.IGNORECASE | re.MULTILINE))
            score += matches * 1.0
        score *= patterns["weight"]
        scores[lang] = scores.get(lang, 0) + score

    if not scores or max(scores.values()) == 0:
        return "python", 0.3

    best_lang = max(scores, key=lambda k: scores[k])
    total = sum(scores.values())
    confidence = min(scores[best_lang] / total if total > 0 else 0, 0.99)

    # Normalize typescript → typescript (keep, don't collapse to js)
    return best_lang, round(confidence, 2)


def detect_framework(code: str) -> Optional[str]:
    """Detect the primary framework used."""
    scores: Dict[str, int] = {}
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        score = sum(
            1 for p in patterns
            if re.search(p, code, re.IGNORECASE | re.MULTILINE)
        )
        if score > 0:
            scores[framework] = score

    if not scores:
        return None
    return max(scores, key=lambda k: scores[k])


def extract_endpoints(code: str) -> List[Dict[str, str]]:
    """Extract API endpoints from code."""
    endpoints = []
    seen = set()

    for pattern_info in ENDPOINT_PATTERNS:
        matches = re.finditer(
            pattern_info["regex"], code, re.IGNORECASE | re.MULTILINE
        )
        for match in matches:
            mg = pattern_info["method_group"]
            pg = pattern_info["path_group"]

            method = match.group(mg).upper() if mg else "GET"
            path = match.group(pg) if pg else "/"

            # Normalize Spring mapping names
            method_map = {
                "GETMAPPING": "GET", "POSTMAPPING": "POST",
                "PUTMAPPING": "PUT", "DELETEMAPPING": "DELETE",
                "PATCHMAPPING": "PATCH", "REQUESTMAPPING": "ANY",
            }
            method = method_map.get(method, method)

            key = f"{method}:{path}"
            if key not in seen:
                seen.add(key)
                endpoints.append({"method": method, "path": path})

    return endpoints[:30]  # cap at 30


def detect_database(code: str) -> Optional[str]:
    """Detect database being used."""
    for db, patterns in DATABASE_PATTERNS.items():
        if any(re.search(p, code, re.IGNORECASE) for p in patterns):
            return db
    return None


def detect_auth(code: str) -> List[str]:
    """Detect authentication mechanisms."""
    found = []
    for auth, patterns in AUTH_PATTERNS.items():
        if any(re.search(p, code, re.IGNORECASE) for p in patterns):
            found.append(auth)
    return found


def detect_project_type(code: str, framework: Optional[str]) -> Optional[str]:
    """Detect project type."""
    for ptype, patterns in PROJECT_TYPE_PATTERNS.items():
        if any(re.search(p, code, re.IGNORECASE | re.MULTILINE) for p in patterns):
            return ptype

    # Framework-based fallback
    if framework:
        api_frameworks = {"FastAPI", "Flask", "Django", "Express", "NestJS", "Spring Boot", "Gin", "Echo", "Fiber"}
        frontend_frameworks = {"React", "Vue", "Next.js", "Angular"}
        if framework in api_frameworks:
            return "REST API"
        if framework in frontend_frameworks:
            return "Frontend App"
    return None


def extract_dependencies(code: str, language: str) -> List[str]:
    """Extract imported packages/dependencies."""
    deps = set()

    if language == "python":
        for match in re.finditer(r'^(?:import|from)\s+([\w.]+)', code, re.MULTILINE):
            dep = match.group(1).split('.')[0]
            # Skip stdlib
            stdlib = {'os', 'sys', 're', 'json', 'math', 'time', 'datetime', 'pathlib',
                      'typing', 'collections', 'functools', 'itertools', 'io', 'abc',
                      'copy', 'random', 'string', 'struct', 'threading', 'asyncio',
                      'logging', 'unittest', 'hashlib', 'hmac', 'base64', 'uuid', 'enum'}
            if dep not in stdlib:
                deps.add(dep)

    elif language in ("javascript", "typescript"):
        for match in re.finditer(r'(?:require\([\'"]|from\s+[\'"])(@?[\w\-./]+)[\'"]', code):
            dep = match.group(1)
            if not dep.startswith('.'):  # skip relative imports
                deps.add(dep.split('/')[0])  # take package root

    elif language == "java":
        for match in re.finditer(r'^import\s+([\w.]+);', code, re.MULTILINE):
            parts = match.group(1).split('.')
            if len(parts) >= 2 and parts[0] not in ('java', 'javax', 'sun'):
                deps.add(f"{parts[0]}.{parts[1]}")

    elif language == "go":
        for match in re.finditer(r'"([\w./\-]+)"', code):
            dep = match.group(1)
            if '/' in dep and not dep.startswith('fmt') and not dep.startswith('net/http'):
                deps.add(dep)

    return sorted(list(deps))[:20]


def build_summary(
    language: str,
    framework: Optional[str],
    project_type: Optional[str],
    endpoints: List[Dict],
    database: Optional[str],
    auth: List[str],
) -> str:
    parts = [f"{language.capitalize()} project"]
    if framework:
        parts[0] += f" using {framework}"
    if project_type:
        parts.append(f"type: {project_type}")
    if endpoints:
        parts.append(f"{len(endpoints)} API endpoint(s) detected")
    if database:
        parts.append(f"database: {database}")
    if auth:
        parts.append(f"auth: {', '.join(auth)}")
    return " · ".join(parts)


@router.post("/detect", response_model=DetectionResult)
async def detect_code(request: DetectRequest):
    """
    Auto-detect language, framework, API endpoints, database, auth, and more from code.
    """
    try:
        code = request.code
        if not code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")

        language, confidence = detect_language(code, request.filename)
        framework = detect_framework(code)
        endpoints = extract_endpoints(code)
        database = detect_database(code)
        auth = detect_auth(code)
        project_type = detect_project_type(code, framework)
        deps = extract_dependencies(code, language)
        summary = build_summary(language, framework, project_type, endpoints, database, auth)

        return DetectionResult(
            language=language,
            language_confidence=confidence,
            framework=framework,
            runtime=None,
            api_endpoints=endpoints,
            dependencies=deps,
            project_type=project_type,
            database=database,
            auth_mechanisms=auth,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.schemas.models import VulnerabilityType, SupportedLanguage


class VectorDatabase:
    """Qdrant-based vector database for RAG"""
    
    def __init__(self):
        # BUG FIX: handle both authenticated (cloud) and unauthenticated (local) Qdrant
        if settings.qdrant_api_key:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
        else:
            self.client = QdrantClient(url=settings.qdrant_url)
        
        self.embedding_model = SentenceTransformer(
            settings.sentence_transformer_model
        )
        
        self.collection_name = "vulnerability_patterns"
        self.embedding_dim = 384  # all-MiniLM-L6-v2 output dimension
        
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dim,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
                self._populate_initial_data()
            else:
                print(f"Collection '{self.collection_name}' already exists.")
        except Exception as e:
            print(f"Warning: Could not initialize Qdrant collection: {e}")
    
    def _populate_initial_data(self):
        """Populate with initial vulnerability examples"""
        initial_data = [
            {
                "id": 1,
                "vulnerability_type": VulnerabilityType.SQL_INJECTION.value,
                "language": SupportedLanguage.PYTHON.value,
                "vulnerable_code": 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = " + user_id\n    cursor.execute(query)\n    return cursor.fetchone()',
                "secure_code": 'def get_user(user_id):\n    query = "SELECT * FROM users WHERE id = ?"\n    cursor.execute(query, (user_id,))\n    return cursor.fetchone()',
                "description": "Use parameterized queries instead of string concatenation to prevent SQL injection"
            },
            {
                "id": 2,
                "vulnerability_type": VulnerabilityType.SQL_INJECTION.value,
                "language": SupportedLanguage.JAVASCRIPT.value,
                "vulnerable_code": 'async function getUser(userId) {\n    const query = `SELECT * FROM users WHERE id = ${userId}`;\n    return await db.query(query);\n}',
                "secure_code": "async function getUser(userId) {\n    const query = 'SELECT * FROM users WHERE id = $1';\n    return await db.query(query, [userId]);\n}",
                "description": "Use parameterized queries with placeholders"
            },
            {
                "id": 3,
                "vulnerability_type": VulnerabilityType.XSS.value,
                "language": SupportedLanguage.JAVASCRIPT.value,
                "vulnerable_code": "function displayMessage(msg) {\n    document.getElementById('output').innerHTML = msg;\n}",
                "secure_code": "function displayMessage(msg) {\n    document.getElementById('output').textContent = msg;\n}",
                "description": "Use textContent instead of innerHTML to prevent XSS"
            },
            {
                "id": 4,
                "vulnerability_type": VulnerabilityType.COMMAND_INJECTION.value,
                "language": SupportedLanguage.PYTHON.value,
                "vulnerable_code": 'import os\ndef ping_host(host):\n    os.system(f"ping -c 1 {host}")',
                "secure_code": 'import subprocess\ndef ping_host(host):\n    subprocess.run(["ping", "-c", "1", host], check=True)',
                "description": "Use subprocess with argument list instead of shell=True"
            },
            {
                "id": 5,
                "vulnerability_type": VulnerabilityType.PATH_TRAVERSAL.value,
                "language": SupportedLanguage.PYTHON.value,
                "vulnerable_code": 'def read_file(filename):\n    with open(f"/var/data/{filename}", "r") as f:\n        return f.read()',
                "secure_code": 'import os\ndef read_file(filename):\n    base_path = "/var/data/"\n    full_path = os.path.normpath(os.path.join(base_path, filename))\n    if not full_path.startswith(base_path):\n        raise ValueError("Invalid file path")\n    with open(full_path, "r") as f:\n        return f.read()',
                "description": "Validate and sanitize file paths to prevent directory traversal"
            },
            {
                "id": 6,
                "vulnerability_type": VulnerabilityType.HARDCODED_SECRETS.value,
                "language": SupportedLanguage.PYTHON.value,
                "vulnerable_code": 'def connect_db():\n    password = "SuperSecret123!"\n    return connect(password=password)',
                "secure_code": 'import os\ndef connect_db():\n    password = os.getenv("DB_PASSWORD")\n    return connect(password=password)',
                "description": "Use environment variables instead of hardcoding secrets"
            },
            {
                "id": 7,
                "vulnerability_type": VulnerabilityType.WEAK_CRYPTO.value,
                "language": SupportedLanguage.PYTHON.value,
                "vulnerable_code": 'import hashlib\ndef hash_password(password):\n    return hashlib.md5(password.encode()).hexdigest()',
                "secure_code": 'import hashlib\nimport os\ndef hash_password(password):\n    salt = os.urandom(32)\n    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)',
                "description": "Use strong hashing algorithms like PBKDF2 with salt"
            },
        ]
        
        points = []
        for example in initial_data:
            text = f"{example['vulnerable_code']}\n{example['secure_code']}\n{example['description']}"
            embedding = self.embedding_model.encode(text).tolist()
            points.append(
                models.PointStruct(
                    id=example["id"],
                    vector=embedding,
                    payload=example
                )
            )
        
        # BUG FIX: batch upsert instead of one-by-one (more efficient, fewer requests)
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Populated {len(initial_data)} vulnerability examples")
    
    def search_similar(
        self,
        code: str,
        vulnerability_type: VulnerabilityType,
        language: Optional[SupportedLanguage] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """Search for similar vulnerability patterns"""
        try:
            embedding = self.embedding_model.encode(code).tolist()
            
            filter_conditions = [
                models.FieldCondition(
                    key="vulnerability_type",
                    match=models.MatchValue(value=vulnerability_type.value)
                )
            ]
            
            if language:
                filter_conditions.append(
                    models.FieldCondition(
                        key="language",
                        match=models.MatchValue(value=language.value)
                    )
                )
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                query_filter=models.Filter(must=filter_conditions),
                limit=top_k,
                with_payload=True   # BUG FIX: explicitly request payload
            )
            
            # BUG FIX: if no results for specific language, retry without language filter
            if not results and language:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=embedding,
                    query_filter=models.Filter(
                        must=[filter_conditions[0]]  # only vulnerability_type filter
                    ),
                    limit=top_k,
                    with_payload=True
                )
            
            similar_examples = []
            for result in results:
                similar_examples.append({
                    "vulnerable_code": result.payload.get("vulnerable_code", ""),
                    "secure_code": result.payload.get("secure_code", ""),
                    "description": result.payload.get("description", ""),
                    "language": result.payload.get("language", ""),
                    "score": result.score
                })
            
            return similar_examples
        except Exception as e:
            print(f"Error searching similar examples: {e}")
            return []
    
    def add_example(
        self,
        vulnerable_code: str,
        secure_code: str,
        description: str,
        vulnerability_type: VulnerabilityType,
        language: SupportedLanguage
    ) -> bool:
        """Add a new vulnerability example to the database"""
        try:
            # BUG FIX: use count() instead of scroll() to get next ID reliably
            count_result = self.client.count(collection_name=self.collection_name)
            new_id = count_result.count + 1
            
            text = f"{vulnerable_code}\n{secure_code}\n{description}"
            embedding = self.embedding_model.encode(text).tolist()
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=new_id,
                        vector=embedding,
                        payload={
                            "vulnerability_type": vulnerability_type.value,
                            "language": language.value,
                            "vulnerable_code": vulnerable_code,
                            "secure_code": secure_code,
                            "description": description
                        }
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Error adding example: {e}")
            return False


# Global vector DB instance (lazy loaded)
_vector_db = None

def get_vector_db() -> VectorDatabase:
    """Get or create vector database instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDatabase()
    return _vector_db

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum


class VulnerabilityType(str, Enum):
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS"
    COMMAND_INJECTION = "COMMAND_INJECTION"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    HARDCODED_SECRETS = "HARDCODED_SECRETS"
    WEAK_CRYPTO = "WEAK_CRYPTO"
    XXE = "XXE"
    SAFE = "SAFE"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SupportedLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    PHP = "php"


# Request/Response Models

class AnalyzeRequest(BaseModel):
    code: str
    language: SupportedLanguage


class AnalyzeResponse(BaseModel):
    is_vulnerable: bool
    vulnerability_type: VulnerabilityType
    severity: Optional[Severity] = None
    confidence: float
    evidence: str
    line_numbers: List[int] = []
    session_id: str


class ExplainRequest(BaseModel):
    session_id: str
    code: str
    vulnerability_type: VulnerabilityType
    evidence: str


class SimilarExample(BaseModel):
    vulnerable_code: str
    secure_code: str
    description: str
    language: str


class ExplainResponse(BaseModel):
    explanation: str
    security_impact: str
    similar_examples: List[SimilarExample]


class IntentValidCase(BaseModel):
    input: str
    expected: str


class IntentInvalidCase(BaseModel):
    input: str
    expected: str


class IntentRequest(BaseModel):
    session_id: str
    purpose: str
    valid_cases: List[IntentValidCase]
    invalid_cases: List[IntentInvalidCase]
    security_constraints: List[str]
    side_effects: List[str]


class IntentResponse(BaseModel):
    intent_captured: bool
    session_id: str


class FixRequest(BaseModel):
    session_id: str


class FixResponse(BaseModel):
    fixed_code: str
    explanation: str
    changes_summary: str


class GenerateTestsRequest(BaseModel):
    session_id: str


class GenerateTestsResponse(BaseModel):
    tests: str
    test_descriptions: List[str]


class RunTestsRequest(BaseModel):
    session_id: str


class TestResult(BaseModel):
    name: str
    passed: bool
    error_message: Optional[str] = None


class RunTestsResponse(BaseModel):
    all_tests_passed: bool
    logs: str
    individual_results: List[TestResult]


class ApprovalRequest(BaseModel):
    session_id: str
    approved: bool


class ApprovalResponse(BaseModel):
    success: bool
    message: str
    final_code: Optional[str] = None


# Internal Models

class SessionData(BaseModel):
    session_id: str
    code: str
    language: SupportedLanguage
    vulnerability_type: Optional[VulnerabilityType] = None
    severity: Optional[Severity] = None
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    line_numbers: List[int] = []
    explanation: Optional[str] = None
    intent: Optional[Dict[str, Any]] = None
    fixed_code: Optional[str] = None
    tests: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None

from fastapi import APIRouter, HTTPException
from app.schemas.models import AnalyzeRequest, AnalyzeResponse, SessionData
from app.ml.detector import get_detector
from app.utils.session import create_session
import uuid

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_code(request: AnalyzeRequest):
    """
    Phase 1: ML-based vulnerability detection
    
    Analyzes code using CodeBERT + rule-based detection
    Returns vulnerability type, severity, confidence, and evidence
    """
    try:
        # Get detector
        detector = get_detector()
        
        # Detect vulnerabilities
        result = detector.detect(request.code, request.language)
        
        # Create session
        session_id = str(uuid.uuid4())
        session_data = SessionData(
            session_id=session_id,
            code=request.code,
            language=request.language,
            vulnerability_type=result["vulnerability_type"],
            severity=result["severity"],
            confidence=result["confidence"],
            evidence=result["evidence"],
            line_numbers=result["line_numbers"]
        )
        create_session(session_data)
        
        # Return response
        return AnalyzeResponse(
            is_vulnerable=result["is_vulnerable"],
            vulnerability_type=result["vulnerability_type"],
            severity=result["severity"],
            confidence=result["confidence"],
            evidence=result["evidence"],
            line_numbers=result["line_numbers"],
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

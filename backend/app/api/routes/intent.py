from fastapi import APIRouter, HTTPException
from app.schemas.models import IntentRequest, IntentResponse
from app.utils.session import get_session, update_session

router = APIRouter()


@router.post("/intent", response_model=IntentResponse)
async def capture_intent(request: IntentRequest):
    """
    Phase 3: Capture developer intent (SEM-8 NOVELTY)
    
    Stores developer's intent to guide code fixing and test generation
    """
    try:
        # Validate session exists
        session = get_session(request.session_id)
        
        # BUG FIX: .dict() is deprecated in Pydantic v2 — use .model_dump() instead
        intent_data = {
            "purpose": request.purpose,
            "valid_cases": [case.model_dump() for case in request.valid_cases],
            "invalid_cases": [case.model_dump() for case in request.invalid_cases],
            "security_constraints": request.security_constraints,
            "side_effects": request.side_effects
        }
        
        update_session(request.session_id, intent=intent_data)
        
        return IntentResponse(
            intent_captured=True,
            session_id=request.session_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent capture failed: {str(e)}")

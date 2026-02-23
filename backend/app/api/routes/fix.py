from fastapi import APIRouter, HTTPException
from app.schemas.models import FixRequest, FixResponse
from app.llm.client import get_llm_client
from app.rag.vectordb import get_vector_db
from app.utils.session import get_session, update_session

router = APIRouter()


@router.post("/fix", response_model=FixResponse)
async def fix_vulnerability(request: FixRequest):
    """
    Phase 4: Intent-aware code fixing
    
    - Uses LLM to generate fix
    - Incorporates developer intent
    - Retrieves secure patterns from RAG
    - Preserves code structure and logic
    """
    try:
        # Get session
        session = get_session(request.session_id)
        
        # Validate intent was captured
        if not session.intent:
            raise HTTPException(
                status_code=400,
                detail="Intent must be captured before generating fix"
            )
        
        # Get LLM client and vector DB
        llm = get_llm_client()
        vector_db = get_vector_db()
        
        # Search for secure patterns
        secure_examples = vector_db.search_similar(
            code=session.code,
            vulnerability_type=session.vulnerability_type,
            language=session.language,
            top_k=2
        )
        
        # Generate fix using LLM + intent + RAG
        fix_result = llm.generate_fix(
            code=session.code,
            vulnerability_type=session.vulnerability_type,
            language=session.language,
            intent=session.intent,
            secure_examples=secure_examples
        )
        
        # Update session with fixed code
        update_session(
            request.session_id,
            fixed_code=fix_result["fixed_code"]
        )
        
        return FixResponse(
            fixed_code=fix_result["fixed_code"],
            explanation=fix_result["explanation"],
            changes_summary=fix_result["changes_summary"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}")

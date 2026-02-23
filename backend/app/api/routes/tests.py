from fastapi import APIRouter, HTTPException
from app.schemas.models import GenerateTestsRequest, GenerateTestsResponse
from app.llm.client import get_llm_client
from app.utils.session import get_session, update_session

router = APIRouter()


@router.post("/generate-tests", response_model=GenerateTestsResponse)
async def generate_tests(request: GenerateTestsRequest):
    """
    Phase 5: Intent-aware unit test generation
    
    Generates tests that:
    - Test valid behavior (from intent)
    - Test invalid input handling (from intent)
    - Test security exploits (vulnerability-specific)
    - Fail on vulnerable code
    - Pass on fixed code
    """
    try:
        # Get session
        session = get_session(request.session_id)
        
        # Validate fixed code exists
        if not session.fixed_code:
            raise HTTPException(
                status_code=400,
                detail="Code must be fixed before generating tests"
            )
        
        if not session.intent:
            raise HTTPException(
                status_code=400,
                detail="Intent must be captured before generating tests"
            )
        
        # Get LLM client
        llm = get_llm_client()
        
        # Generate tests
        test_result = llm.generate_tests(
            original_code=session.code,
            fixed_code=session.fixed_code,
            language=session.language,
            vulnerability_type=session.vulnerability_type,
            intent=session.intent
        )
        
        # Update session with tests
        update_session(
            request.session_id,
            tests=test_result["tests"]
        )
        
        return GenerateTestsResponse(
            tests=test_result["tests"],
            test_descriptions=test_result["test_descriptions"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")

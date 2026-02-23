from fastapi import APIRouter, HTTPException
from app.schemas.models import ExplainRequest, ExplainResponse, SimilarExample
from app.llm.client import get_llm_client
from app.rag.vectordb import get_vector_db
from app.utils.session import get_session, update_session

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
async def explain_vulnerability(request: ExplainRequest):
    """
    Phase 2: Generate explanation with RAG
    
    - Uses LLM to explain vulnerability
    - Searches vector DB for similar patterns
    - Returns enriched explanation with examples
    """
    try:
        # Get session
        session = get_session(request.session_id)
        
        # Get LLM client and vector DB
        llm = get_llm_client()
        vector_db = get_vector_db()
        
        # Search for similar examples
        similar_results = vector_db.search_similar(
            code=request.code,
            vulnerability_type=request.vulnerability_type,
            language=session.language,
            top_k=3
        )
        
        # Generate explanation using LLM + RAG
        explanation_result = llm.generate_explanation(
            code=request.code,
            vulnerability_type=request.vulnerability_type,
            evidence=request.evidence,
            similar_examples=similar_results
        )
        
        # Update session with explanation
        update_session(
            request.session_id,
            explanation=explanation_result["explanation"]
        )
        
        # Format similar examples
        similar_examples = [
            SimilarExample(
                vulnerable_code=ex["vulnerable_code"],
                secure_code=ex["secure_code"],
                description=ex["description"],
                language=ex.get("language", "")
            )
            for ex in similar_results
        ]
        
        return ExplainResponse(
            explanation=explanation_result["explanation"],
            security_impact=explanation_result["security_impact"],
            similar_examples=similar_examples
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")

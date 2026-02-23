from fastapi import APIRouter, HTTPException
from app.schemas.models import RunTestsRequest, RunTestsResponse, ApprovalRequest, ApprovalResponse
from app.sandbox.executor import get_executor
from app.utils.session import get_session, update_session, delete_session

router = APIRouter()


@router.post("/run-tests", response_model=RunTestsResponse)
async def run_tests(request: RunTestsRequest):
    """
    Phase 6: Sandbox test execution
    
    Runs generated tests in isolated Docker container
    - No network access
    - Resource limited
    - Captures detailed results
    """
    try:
        # Get session
        session = get_session(request.session_id)
        
        # Validate tests exist
        if not session.tests:
            raise HTTPException(
                status_code=400,
                detail="Tests must be generated before running"
            )
        
        if not session.fixed_code:
            raise HTTPException(
                status_code=400,
                detail="Code must be fixed before running tests"
            )
        
        # Get sandbox executor
        executor = get_executor()
        
        # Run tests on fixed code
        result = executor.run_tests(
            code=session.fixed_code,
            tests=session.tests,
            language=session.language
        )
        
        # Update session with test results
        update_session(
            request.session_id,
            test_results=result
        )
        
        return RunTestsResponse(
            all_tests_passed=result["all_tests_passed"],
            logs=result["logs"],
            individual_results=result["individual_results"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


@router.post("/approve", response_model=ApprovalResponse)
async def final_approval(request: ApprovalRequest):
    """
    Phase 7: Final user approval
    
    - User decides to apply or reject fix
    - Only allowed if tests passed
    - Returns final code if approved
    """
    try:
        # Get session
        session = get_session(request.session_id)
        
        # Validate tests were run
        if not session.test_results:
            raise HTTPException(
                status_code=400,
                detail="Tests must be run before final approval"
            )
        
        # Check if tests passed
        if not session.test_results.get("all_tests_passed", False):
            if request.approved:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot approve fix - tests did not pass"
                )
        
        if request.approved:
            # User approved - return fixed code
            final_code = session.fixed_code
            message = "Fix approved and applied successfully"
        else:
            # User rejected - return original code
            final_code = None
            message = "Fix rejected. No changes applied."
        
        # Cleanup session
        delete_session(request.session_id)
        
        return ApprovalResponse(
            success=True,
            message=message,
            final_code=final_code
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")

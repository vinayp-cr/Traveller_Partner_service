"""
Authentication Controller
API endpoints for Xeni authentication token generation.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.auth_model import AuthResponse, AuthErrorResponse
from app.services.auth_service import AuthService
from app.core.logger import logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Initialize auth service
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    return auth_service


@router.post("/generate-token", response_model=AuthResponse, tags=["Authentication"])
async def generate_auth_token(
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Generate authentication token for Xeni API calls.
    
    This endpoint generates a new authentication signature that can be used
    for subsequent API calls to Xeni services.
    
    Returns:
        AuthResponse with authentication signature and expiry information
    """
    try:
        logger.info("Generating authentication token")
        
        auth_result = await auth_service.generate_auth_token()
        
        if auth_result.get('status') == 'success':
            logger.info("Authentication token generated successfully")
            return AuthResponse(**auth_result)
        else:
            logger.error(f"Authentication token generation failed: {auth_result.get('message')}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": auth_result.get('message', 'Authentication failed'),
                    "error_code": auth_result.get('error_code', 'unknown')
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication controller error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Authentication service error: {str(e)}",
                "error_code": "controller_error"
            }
        )


@router.get("/token-status", tags=["Authentication"])
async def get_token_status(
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current authentication token status.
    
    Returns:
        Dict containing token status and expiry information
    """
    try:
        # Check if we have a cached token
        cached_token = auth_service._get_cached_token()
        
        if cached_token:
            return {
                "status": "success",
                "message": "Valid token available",
                "has_token": True,
                "expiry": cached_token.get('expiry'),
                "signature": cached_token.get('signature', '')[:50] + "..." if cached_token.get('signature') else None
            }
        else:
            return {
                "status": "success",
                "message": "No valid token available",
                "has_token": False,
                "expiry": None,
                "signature": None
            }
            
    except Exception as e:
        logger.error(f"Token status check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Token status check failed: {str(e)}",
                "error_code": "status_check_error"
            }
        )


@router.delete("/clear-token", tags=["Authentication"])
async def clear_auth_token(
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Clear cached authentication token.
    
    This will force the next API call to generate a new token.
    
    Returns:
        Dict confirming token cache has been cleared
    """
    try:
        auth_service.clear_token_cache()
        
        return {
            "status": "success",
            "message": "Authentication token cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Token cache clear error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to clear token cache: {str(e)}",
                "error_code": "clear_error"
            }
        )

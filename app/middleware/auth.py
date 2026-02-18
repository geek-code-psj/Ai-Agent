"""Authentication middleware for API key validation."""

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(request: Request, api_key: Optional[str] = None) -> bool:
    """
    Validate API key from request.
    
    Args:
        request: FastAPI request
        api_key: API key from header
        
    Returns:
        True if valid, raises HTTPException otherwise
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # If no API key is configured, skip validation
    if not settings.api_key:
        return True
    
    # Check for API key in header
    if not api_key:
        # Try to get from header manually
        api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header."
        )
    
    # Validate API key
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True


def get_api_key_dependency():
    """
    Get API key dependency for FastAPI routes.
    
    Returns:
        API key header dependency
    """
    return api_key_header

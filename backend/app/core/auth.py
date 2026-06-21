import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Validates the Supabase JWT token and returns the user payload.
    In the MVP, if no token is provided, we might return None to allow 
    fallback to handle-based logic, or we can raise a 401.
    """
    if not credentials:
        return None
        
    token = credentials.credentials
    try:
        # Supabase JWT secret is required to verify the token signature
        if not settings.SUPABASE_JWT_SECRET:
            logger.warning("SUPABASE_JWT_SECRET is not set. Cannot verify token securely.")
            # For local testing if secret is not available, we could decode without verification:
            # payload = jwt.decode(token, options={"verify_signature": False})
            raise HTTPException(status_code=500, detail="Server auth configuration error.")
            
        payload = jwt.decode(
            token, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

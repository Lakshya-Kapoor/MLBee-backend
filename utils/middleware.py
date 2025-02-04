from fastapi import Header, HTTPException
from .auth import verify_jwt_token

def get_current_user(authorization: str = Header(None)):
    """Middleware that extracts and verifies the JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    
    token = authorization.replace("Bearer ", "")  # Remove 'Bearer ' prefix if present
    return verify_jwt_token(token)  # Returns decoded user info if valid

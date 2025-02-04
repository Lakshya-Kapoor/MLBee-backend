import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

def create_jwt_token(data: dict, expires_delta: int = 7):
    """Generates a JWT token with expiration time"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=expires_delta)
    to_encode.update({"exp": expire})  # Adding expiry time

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_jwt_token(token: str):
    """Decodes and verifies a JWT token"""
    try:
        decoded_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_data  # Returns payload if valid
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
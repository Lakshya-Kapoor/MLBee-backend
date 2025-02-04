from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.user import User
import bcrypt
from utils.auth import create_jwt_token, verify_jwt_token

router = APIRouter()

class UserBody(BaseModel):
    username: str
    email: str
    password: str

@router.post("/signup")
async def signup(user: UserBody):
    print("User:", user)
    existing = await User.find_one({"$or": [{"username": user.username}, {"email": user.email}]})

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = User(username=user.username, email=user.email, password=hashed_password)
    await new_user.insert()

    token = create_jwt_token({"username": user.username})
    return {"token": token}

@router.post("/login")
async def login(user: UserBody):
    existing = await User.find_one(User.username == user.username)

    if not existing:
        raise HTTPException(status_code=400, detail="User does not exist")

    if not bcrypt.checkpw(user.password.encode('utf-8'), existing.password.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_jwt_token({"username": user.username})
    return {"token": token}

@router.get("/verify")
async def verify(token: str):
    return verify_jwt_token(token)
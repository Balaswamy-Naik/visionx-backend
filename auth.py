from jose import jwt
from models import User
from sqlmodel import Session, select
from sqlmodel import create_engine
from passlib.context import CryptContext
from fastapi import HTTPException, Header
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visionx.db")
engine = create_engine(DATABASE_URL, echo=False)

PWDCTX = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "replace-this-secret")
JWT_ALGO = "HS256"

def get_password_hash(password: str) -> str:
    return PWDCTX.hash(password)

def verify_password(plain, hashed) -> bool:
    return PWDCTX.verify(plain, hashed)

def create_access_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGO)

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        college_id = payload.get("college_id")
        if not college_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
    with Session(engine) as sess:
        user = sess.exec(select(User).where(User.college_id == college_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

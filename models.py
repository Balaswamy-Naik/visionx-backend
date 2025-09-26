from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    college_id: str = Field(index=True, nullable=False, unique=True)
    password_hash: str
    role: str = "student"
    state: Optional[str] = None
    district: Optional[str] = None
    institute_name: Optional[str] = None
    pincode: Optional[str] = None
    language: Optional[str] = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    college_id: str = Field(index=True, nullable=False)
    answers: str
    score: int
    severity: str
    flagged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

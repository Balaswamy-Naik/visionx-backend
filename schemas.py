from pydantic import BaseModel
from typing import List, Optional

class SignupIn(BaseModel):
    collegeId: str
    password: str
    role: Optional[str] = "student"
    state: Optional[str] = None
    district: Optional[str] = None
    instituteName: Optional[str] = None
    pincode: Optional[str] = None
    language: Optional[str] = "en"

class LoginIn(BaseModel):
    collegeId: str
    password: str

class TestSubmitIn(BaseModel):
    answers: List[int]

class ChatIn(BaseModel):
    message: str

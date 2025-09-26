from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select
from models import User, TestResult
from auth import create_access_token, get_current_user, verify_password, get_password_hash
from schemas import LoginIn, SignupIn, TestSubmitIn, ChatIn
import os
import httpx
from typing import List

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visionx.db")
engine = create_engine(DATABASE_URL, echo=False)

app = FastAPI(title="VisionX Backend (FastAPI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/api/")
def root():
    return {"ok": True, "msg": "VisionX Python backend running"}

@app.post("/api/auth/signup")
def signup(payload: SignupIn):
    with Session(engine) as sess:
        statement = select(User).where(User.college_id == payload.collegeId)
        existing = sess.exec(statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="User exists")
        user = User(
            college_id=payload.collegeId,
            password_hash=get_password_hash(payload.password),
            role=payload.role or "student",
            state=payload.state,
            district=payload.district,
            institute_name=payload.instituteName,
            pincode=payload.pincode,
            language=payload.language or "en"
        )
        sess.add(user)
        sess.commit()
        sess.refresh(user)
        token = create_access_token({"college_id": user.college_id, "role": user.role})
        return {"token": token, "user": {"collegeId": user.college_id, "role": user.role}}

@app.post("/api/auth/login")
def login(payload: LoginIn):
    with Session(engine) as sess:
        statement = select(User).where(User.college_id == payload.collegeId)
        user = sess.exec(statement).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        token = create_access_token({"college_id": user.college_id, "role": user.role})
        return {"token": token, "user": {"collegeId": user.college_id, "role": user.role}}

@app.post("/api/test/submit")
def submit_test(payload: TestSubmitIn, current_user: User = Depends(get_current_user)):
    answers = payload.answers
    if not isinstance(answers, list) or len(answers) == 0:
        raise HTTPException(status_code=400, detail="Answers must be a non-empty list")
    score = sum(int(x) for x in answers)
    if score <= 5:
        severity = "low"
    elif score <= 12:
        severity = "mild"
    else:
        severity = "high"
    flagged = severity == "high"
    with Session(engine) as sess:
        tr = TestResult(
            college_id=current_user.college_id,
            answers=",".join(str(int(x)) for x in answers),
            score=score,
            severity=severity,
            flagged=flagged
        )
        sess.add(tr)
        sess.commit()
        sess.refresh(tr)
    return {"ok": True, "test": tr}

@app.get("/api/helplines")
def helplines():
    data = [
        {"name":"Kashmir Suicide Prevention Helpline (example)","number":"+91-0000000000","notes":"24/7"},
        {"name":"Mental Health Helpline (India)","number":"08046110007","notes":"AIIMS/NCERT list - check local numbers"},
        {"name":"Text-based support (Example)","number":"text HELLO to 56789","notes":"Text support"}
    ]
    return {"helplines": data}

@app.get("/api/management/reports")
def management_reports(current_user: User = Depends(get_current_user)):
    if current_user.role != "management":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    with Session(engine) as sess:
        rows = sess.exec(select(TestResult).order_by(TestResult.created_at.desc()).limit(500)).all()
        return {"count": len(rows), "recent": rows}

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

@app.post("/api/chat")
async def chat_proxy(payload: ChatIn, current_user: User = Depends(get_current_user)):
    message = payload.message or ""
    if OPENAI_KEY:
        async with httpx.AsyncClient(timeout=20) as client:
            url = "https://api.openai.com/v1/chat/completions"
            body = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a calm, empathetic student mental-health assistant."},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
            try:
                r = await client.post(url, json=body, headers=headers)
                r.raise_for_status()
                j = r.json()
                text = j["choices"][0]["message"]["content"]
                return {"response": text}
            except Exception as e:
                return {"response": "Sorry — the AI provider failed. Try again later."}
    msg = message.lower()
    if "breath" in msg or "breathing" in msg:
        return {"response": "Try: inhale 4s, hold 4s, exhale 6s. Repeat for 1-2 minutes."}
    if "anx" in msg or "panic" in msg or "worri" in msg:
        return {"response": "I understand. Would you like grounding techniques or step-by-step breathing?"}
    return {"response": "I hear you. Tell me more or choose 'breathing' if you'd like an exercise."}

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import os, requests, asyncio

from database import engine, get_db, Base
import models, auth
import garmin_service
import payment_service
import firebase_auth as fb

app = FastAPI(title="WellBeing Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_TOKEN = os.getenv("HF_TOKEN", "")

@app.on_event("startup")
def startup():
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception:
        pass  # pgvector not available, skip
    Base.metadata.create_all(bind=engine)
    # Start keep-alive background task
    asyncio.create_task(keep_alive())

async def keep_alive():
    """Ping self every 5 minutes to prevent HF Space from sleeping."""
    space_url = os.getenv("SPACE_URL", "")
    if not space_url:
        return
    while True:
        await asyncio.sleep(300)  # 5 minutes
        try:
            requests.get(f"{space_url}/", timeout=10)
        except:
            pass

# ── Schemas ────────────────────────────────────────────────

class RegisterSchema(BaseModel):
    email: str
    username: str
    password: str

class FirebaseLoginSchema(BaseModel):
    id_token: str
    email: str
    username: Optional[str] = None

class WellbeingSchema(BaseModel):
    mood: int
    energy: int
    stress: int
    sleep_hours: float
    notes: Optional[str] = ""

class JournalSchema(BaseModel):
    title: str
    body: Optional[str] = ""
    mood: Optional[str] = "neutral"

class TodoSchema(BaseModel):
    title: str
    category: Optional[str] = "Wellness"
    priority: Optional[str] = "medium"

class TrackingSchema(BaseModel):
    date: Optional[str] = None
    sleep: Optional[float] = 0
    exercise: Optional[float] = 0
    water: Optional[int] = 0
    heart_rate: Optional[int] = 0
    meditation: Optional[float] = 0

class AnalyzeSchema(BaseModel):
    text: str

class CheckoutItem(BaseModel):
    name: str
    price: float
    quantity: int = 1

class CheckoutSchema(BaseModel):
    items: List[CheckoutItem]
    total: float

# ── Auth ───────────────────────────────────────────────────

@app.post("/auth/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=data.email,
        username=data.username,
        hashed_pw=auth.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not auth.verify_password(form.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

@app.get("/auth/me")
def me(current_user: models.User = Depends(auth.get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "username": current_user.username}

@app.post("/auth/firebase")
def firebase_login(data: FirebaseLoginSchema, db: Session = Depends(get_db)):
    """Login/register via Firebase ID token."""
    user_info = fb.verify_firebase_token(data.id_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    email = user_info.get("email") or data.email
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        # Auto-register on first login
        username = data.username or email.split("@")[0]
        user = models.User(
            email=email,
            username=username,
            hashed_pw=auth.hash_password(os.urandom(32).hex()),  # random pw, not used
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = auth.create_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "username": user.username}

# ── Wellbeing Entries ──────────────────────────────────────

@app.post("/entries")
def add_entry(data: WellbeingSchema, db: Session = Depends(get_db),
              current_user: models.User = Depends(auth.get_current_user)):
    entry = models.WellbeingEntry(user_id=current_user.id, **data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@app.get("/entries")
def get_entries(db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.WellbeingEntry).filter(
        models.WellbeingEntry.user_id == current_user.id
    ).order_by(models.WellbeingEntry.created_at.desc()).all()

@app.get("/entries/summary")
def get_summary(db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    entries = db.query(models.WellbeingEntry).filter(
        models.WellbeingEntry.user_id == current_user.id
    ).all()
    if not entries:
        return {"summary": None}
    n = len(entries)
    return {"summary": {
        "total_entries": n,
        "avg_mood":    round(sum(e.mood for e in entries) / n, 2),
        "avg_energy":  round(sum(e.energy for e in entries) / n, 2),
        "avg_stress":  round(sum(e.stress for e in entries) / n, 2),
        "avg_sleep":   round(sum(e.sleep_hours for e in entries) / n, 2),
    }}

# ── Journal ────────────────────────────────────────────────

@app.post("/journal")
def add_journal(data: JournalSchema, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    entry = models.JournalEntry(user_id=current_user.id, **data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@app.get("/journal")
def get_journal(db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.JournalEntry).filter(
        models.JournalEntry.user_id == current_user.id
    ).order_by(models.JournalEntry.created_at.desc()).all()

@app.delete("/journal/{entry_id}")
def delete_journal(entry_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(entry)
    db.commit()
    return {"status": "deleted"}

# ── To-Do ──────────────────────────────────────────────────

@app.post("/todos")
def add_todo(data: TodoSchema, db: Session = Depends(get_db),
             current_user: models.User = Depends(auth.get_current_user)):
    todo = models.Todo(user_id=current_user.id, **data.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@app.get("/todos")
def get_todos(db: Session = Depends(get_db),
              current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Todo).filter(
        models.Todo.user_id == current_user.id
    ).order_by(models.Todo.created_at.desc()).all()

@app.patch("/todos/{todo_id}/done")
def complete_todo(todo_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(auth.get_current_user)):
    todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id, models.Todo.user_id == current_user.id
    ).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Not found")
    todo.done = True
    db.commit()
    return todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id, models.Todo.user_id == current_user.id
    ).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(todo)
    db.commit()
    return {"status": "deleted"}

# ── Tracking ───────────────────────────────────────────────

@app.post("/tracking")
def save_tracking(data: TrackingSchema, db: Session = Depends(get_db),
                  current_user: models.User = Depends(auth.get_current_user)):
    today = data.date or str(date.today())
    existing = db.query(models.TrackingEntry).filter(
        models.TrackingEntry.user_id == current_user.id,
        models.TrackingEntry.date == today
    ).first()
    if existing:
        for k, v in data.model_dump(exclude={"date"}).items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing
    entry = models.TrackingEntry(user_id=current_user.id, date=today, **data.model_dump(exclude={"date"}))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@app.get("/tracking/today")
def get_tracking_today(db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    today = str(date.today())
    entry = db.query(models.TrackingEntry).filter(
        models.TrackingEntry.user_id == current_user.id,
        models.TrackingEntry.date == today
    ).first()
    return entry or {"sleep": 0, "exercise": 0, "water": 0, "heart_rate": 0, "meditation": 0}

# ── AI Analyze ─────────────────────────────────────────────

@app.post("/analyze")
def analyze(data: AnalyzeSchema):
    if not HF_TOKEN:
        return {"analysis": [[{"label": "neutral", "score": 1.0}]]}
    try:
        url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
        resp = requests.post(url, headers={"Authorization": f"Bearer {HF_TOKEN}"},
                             json={"inputs": data.text}, timeout=15)
        if resp.status_code != 200:
            return {"analysis": [[{"label": "neutral", "score": 1.0}]]}
        return {"analysis": resp.json()}
    except:
        return {"analysis": [[{"label": "neutral", "score": 1.0}]]}

@app.get("/")
def root():
    return {"status": "ok"}

# ── Garmin ─────────────────────────────────────────────────

@app.get("/garmin/today")
def garmin_today(current_user: models.User = Depends(auth.get_current_user)):
    data = garmin_service.get_today_stats()
    if "error" in data:
        raise HTTPException(status_code=503, detail=data["error"])
    return data

@app.post("/garmin/sync")
def garmin_sync(db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    """Fetch from Garmin and save to tracking DB."""
    data = garmin_service.get_today_stats()
    if "error" in data:
        raise HTTPException(status_code=503, detail=data["error"])

    today = str(date.today())
    existing = db.query(models.TrackingEntry).filter(
        models.TrackingEntry.user_id == current_user.id,
        models.TrackingEntry.date == today
    ).first()

    fields = {k: data.get(k, 0) for k in ["sleep", "exercise", "water", "heart_rate", "meditation"]}

    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    entry = models.TrackingEntry(user_id=current_user.id, date=today, **fields)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# ── Payment ────────────────────────────────────────────────

@app.post("/payment/checkout")
def checkout(data: CheckoutSchema,
             current_user: models.User = Depends(auth.get_current_user)):
    if not payment_service.MIDTRANS_SERVER_KEY:
        raise HTTPException(status_code=503, detail="Payment not configured yet")
    customer = {"name": current_user.username, "email": current_user.email}
    result = payment_service.create_transaction(
        [item.model_dump() for item in data.items],
        customer,
        data.total,
    )
    return result

@app.post("/payment/notification")
def payment_notification(notification: dict):
    if not payment_service.MIDTRANS_SERVER_KEY:
        raise HTTPException(status_code=503, detail="Payment not configured yet")
    result = payment_service.verify_notification(notification)
    return {"status": result.get("transaction_status")}

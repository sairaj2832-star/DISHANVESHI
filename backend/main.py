# ==========================================================
# Dishanveshi Backend API
# Version: v1.0.0
# Stack: FastAPI + JWT + Async SQLAlchemy
# ==========================================================

from fastapi import (
    FastAPI, Depends, HTTPException, status, Query
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Annotated, List
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os

# ----------------- Internal Imports -----------------
import models
import schemas
import CRUD
import services
import security
from database import init_db, async_session
from security import SECRET_KEY, ALGORITHM

# ==========================================================
# APP METADATA
# ==========================================================
API_VERSION = "v1.0.0"
APP_NAME = "Dishanveshi – Travel Intelligence API"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==========================================================
# LIFESPAN (Startup / Shutdown)
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Dishanveshi API...")
    await init_db()
    print("✅ Database initialized")
    yield
    print("🛑 Shutting down Dishanveshi API...")

# ==========================================================
# APP INIT
# ==========================================================
app = FastAPI(
    title=APP_NAME,
    version=API_VERSION,
    lifespan=lifespan
)

# ==========================================================
# CORS
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# DATABASE DEPENDENCY
# ==========================================================
async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()

AsyncDB = Annotated[AsyncSession, Depends(get_db)]

# ==========================================================
# AUTH UTIL
# ==========================================================
async def get_current_user(
    db: AsyncDB,
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = await CRUD.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ==========================================================
# HEALTH + ROOT
# ==========================================================
@app.get("/api/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": API_VERSION
    }

@app.get("/", tags=["system"])
async def serve_frontend():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"message": "Dishanveshi API is running"}

# ==========================================================
# AUTH ROUTES
# ==========================================================
@app.post("/api/auth/register", response_model=schemas.User, tags=["auth"])
async def register_user(user: schemas.UserCreate, db: AsyncDB):
    existing = await CRUD.get_user_by_email(db, email=user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await CRUD.create_user(db, user)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login", response_model=schemas.Token)
async def login(req: LoginRequest, db: AsyncDB):
    user = await CRUD.get_user_by_email(db, email=req.email)
    if not user or not security.verify_password(
        req.password, user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = security.create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ==========================================================
# AI + PLACES
# ==========================================================
class AIRequest(BaseModel):
    mood: str
    places_list: str

class LocationSearch(BaseModel):
    lat: float
    lng: float
    type: str

@app.post("/api/ai/recommend", tags=["ai"])
async def ai_recommend(
    req: AIRequest,
    user = Depends(get_current_user)
):
    advice = await services.get_ai_recommendation(
        req.mood, req.places_list
    )
    return {"recommendation": advice}

@app.post("/api/places/search", tags=["places"])
async def search_places(
    search: LocationSearch,
    user = Depends(get_current_user)
):
    query = "restaurant" if search.type == "food" else "hotel"
    return await services.get_google_places(
        search.lat, search.lng, query
    )

# ==========================================================
# ITINERARY
# ==========================================================
@app.post(
    "/api/itinerary",
    response_model=schemas.ItineraryResponse,
    tags=["itinerary"]
)
async def generate_itinerary(
    req: schemas.ItineraryRequest,
    user = Depends(get_current_user)
):
    plan = await services.generate_itinerary(
        destination=req.destination,
        days=req.days,
        travel_type=req.travel_type,
        budget=req.budget,
        mood=req.mood,
        include_pois=req.include_pois
    )
    return {
        "destination": req.destination,
        "plan": plan
    }

@app.post("/api/itinerary/save", tags=["itinerary"])
async def save_itinerary(
    req: schemas.ItinerarySaveRequest,
    db: AsyncDB,
    user = Depends(get_current_user)
):
    saved = await CRUD.save_itinerary(
        db=db,
        user_id=user.id,
        destination=req.destination,
        days=req.days,
        plan=req.plan
    )
    return {"message": "Itinerary saved", "id": saved.id}

@app.get(
    "/api/itinerary/my",
    response_model=List[schemas.ItineraryDB],
    tags=["itinerary"]
)
async def my_itineraries(
    db: AsyncDB,
    user = Depends(get_current_user)
):
    return await CRUD.get_user_itineraries(db, user.id)

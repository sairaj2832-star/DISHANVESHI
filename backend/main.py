from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm 
from contextlib import asynccontextmanager
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from schemas import ItineraryRequest, ItineraryResponse
from fastapi.responses import FileResponse 
import os 
from fastapi import Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from security import SECRET_KEY, ALGORITHM
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Import our modules
import models
import CRUD
import schemas
import security
import services 
from database import init_db, async_session

# --- Lifespan Function ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting up...")
    await init_db() 
    print("Database initialized.")
    yield 
    print("Server shutting down...")

# --- Database Dependency ---
async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()

AsyncDb = Annotated[AsyncSession, Depends(get_db)]

# --- FastAPI App ---
app = FastAPI(
    title="TravelMate API",
    lifespan=lifespan 
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Models ---
class LocationSearch(BaseModel):
    lat: float
    lng: float
    type: str 

class AIRequest(BaseModel):
    mood: str
    places_list: str

# --- API Endpoints ---

@app.get("/api/health")
def read_health():
    return {"status": "ok"}

# --- NEW: SERVE THE FRONTEND (The Magic Part) ---
@app.get("/")
async def read_root():
    # This tells Python: "When someone opens the website, give them the HTML file"
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "index.html not found"}

# --- Auth Endpoints ---
@app.post("/api/auth/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: AsyncDb):
    db_user = await CRUD.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await CRUD.create_user(db, user=user)

@app.post("/api/auth/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncDb
):
    user = await CRUD.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- TravelMate Endpoints ---

@app.post("/api/places/search")
async def search_places(search: LocationSearch):
    query = "restaurant" if search.type == "food" else "hotel"
    places = await services.get_google_places(search.lat, search.lng, query)
    return places

@app.post("/api/ai/recommend")
async def ask_gemini(request: AIRequest):
    advice = await services.get_ai_recommendation(request.mood, request.places_list)
    return {"recommendation": advice}

class ItineraryRequest(BaseModel):
    destination: str
    days: int
    travel_type: str
    budget: str
    mood: str
    include_pois: bool = True   # new

@app.post("/api/itinerary", response_model=ItineraryResponse)
async def generate_user_itinerary(request: ItineraryRequest):
    plan = await services.generate_itinerary(
        destination=request.destination,
        days=request.days,
        travel_type=request.travel_type,
        budget=request.budget,
        mood=request.mood,
        include_pois=request.include_pois
    )
    return {"destination": request.destination, "plan": plan}
async def get_current_user(db: AsyncDb,token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await CRUD.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
@app.post("/api/itinerary/save")
async def save_itinerary(
    db: AsyncDb,
    request: schemas.ItinerarySaveRequest,
    user = Depends(get_current_user)
):
    saved = await CRUD.save_itinerary(
        db, user_id=user.id,
        destination=request.destination,
        days=request.days,
        plan=request.plan
    )
    return {"message": "Itinerary saved", "id": saved.id}
@app.get("/api/itinerary/my", response_model=list[schemas.ItineraryDB])
async def get_my_itineraries(db: AsyncDb,user = Depends(get_current_user)):
    items = await CRUD.get_user_itineraries(db, user.id)
    return items
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "https://your-site.netlify.app",   # add your Netlify domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

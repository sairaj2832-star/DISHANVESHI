from pydantic import BaseModel, EmailStr
from datetime import datetime


# --- User Schemas (from before) ---

class UserBase(BaseModel):
    """
    This is the base schema. It's not used directly.
    """
    email: EmailStr # A special type from Pydantic that validates the email format.

class UserCreate(UserBase):
    """
    This is the schema for *creating* a user.
    It expects an email and a password.
    """
    password: str

class User(UserBase):
    """
    This is the schema for *returning* a user from the API.
    It includes the ID and email, but securely hides the password.
    """
    id: int

    class Config:
        from_attributes = True

# --- NEW: Token Schemas (Moved to the correct file) ---

class Token(BaseModel):
    """
    This is the schema for the token response.
    It's what we send back to the user when they log in.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    This is the schema for the data *inside* the token.
    We will just store the user's email.
    """
    email: str | None = None
class ItineraryRequest(BaseModel):
    destination: str
    days: int
    travel_type: str  # e.g., "relaxing", "adventure", "cultural"
    budget: str       # e.g., "low", "medium", "high"
    mood: str         # optional mood like "tired", "excited"
class ItineraryDay(BaseModel):
    day: int
    summary: str

class ItineraryResponse(BaseModel):
    destination: str
    plan: list[ItineraryDay]
class ItinerarySaveRequest(BaseModel):
    destination: str
    days: int
    plan: list  

class ItineraryDB(BaseModel):
    id: int
    destination: str
    days: int
    plan_json: str
    created_at: datetime

    class Config:
        from_attributes = True

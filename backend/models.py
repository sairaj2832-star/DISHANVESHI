from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    """
    This is the User model, which defines the 'users' table in our database.
    """
    __tablename__ = "users"
    # Define the columns for the 'users' table
    id = Column(Integer, primary_key=True, index=True, nullable= False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    destination = Column(String, index=True)
    days = Column(Integer)
    plan_json = Column(Text)  # store JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    # We can add more fields here later, like:
    # is_active = Column(Boolean, default=True)
    # first_name = Column(String, index=True)
    # last_name = Column(String, index=True)
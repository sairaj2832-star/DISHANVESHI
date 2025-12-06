from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
import schemas
import security
import json
from models import Itinerary

async def get_user_by_email(db: AsyncSession, email: str):
    """
    Looks up a user in the database by their email address.
    Returns the user model if found, None otherwise.
    """
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: schemas.UserCreate):
    """
    Creates a new user in the database.
    This involves hashing the password and saving the new user model.
    """
    # Get the hashed password from our security helper
    hashed_password = security.get_password_hash(user.password)
    
    # Create a new User *model* (the database version of a user)
    # Note: We are NOT saving the plain text password.
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password
    )
    
    # Add the new user object to the database session
    db.add(db_user)
    
    # Commit the changes (save them to the database file)
    await db.commit()
    
    # Refresh the object to get the new ID from the database
    await db.refresh(db_user)
    
    return db_user

async def save_itinerary(db, user_id: int, destination: str, days: int, plan: list):
    new_itinerary = Itinerary(
        user_id=user_id,
        destination=destination,
        days=days,
        plan_json=json.dumps(plan)
    )
    db.add(new_itinerary)
    await db.commit()
    await db.refresh(new_itinerary)
    return new_itinerary

async def get_user_itineraries(db, user_id: int):
    result = await db.execute(
        select(Itinerary).where(Itinerary.user_id == user_id)
    )
    return result.scalars().all()
import os 
from sqlalchemy.orm import declarative_base
# database.py (example)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./travel_app.db")
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
async def init_db():
    """
    A function to initialize the database and create all tables.
    """
    async with engine.begin() as conn:
        # This command creates all tables defined by models that inherit from Base
        # await conn.run_sync(Base.metadata.drop_all) # Use this to drop tables first if needed
        await conn.run_sync(Base.metadata.create_all)
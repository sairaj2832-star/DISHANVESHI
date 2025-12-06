<<<<<<< HEAD
# DISHANVESHI
=======
# inteligent-travel-guider
<!-- database.db file explanation -->
<!-- import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base -->
Explanation: We are importing our "toolkits."
create_async_engine: A tool that builds the main "engine" for our database connection. The "async" part means it's built to handle many connections at once, which is perfect for FastAPI.

async_sessionmaker: A tool that acts as a "ticket counter" to give out new database "conversations" (sessions) to each API request.

declarative_base: A "blueprint factory" that we will use to design our database tables using Python classes.

<!-- DATABASE_URL = "sqlite+aiosqlite:///./travel_app.db" -->
Explanation: This is the address of our database. It's like a connection string.

sqlite: We are using a SQLite database.

aiosqlite: This is the specific "driver" or "language" we'll use to speak to SQLite in an async way.

<!-- :///./travel_app.db: This is the file path. It means "look in the current directory (./) for a file named travel_app.db. If it doesn't exist, create it." -->

engine = create_async_engine(DATABASE_URL, echo=True)
Explanation: We are now building the main "Engine". This is the heart of our database connection. It manages the low-level details of talking to the travel_app.db file.

echo=True: This is a helpful setting for development. It tells SQLAlchemy to print out every single SQL command it runs to the terminal. You will see SELECT, INSERT, UPDATE commands in your log, which is fantastic for debugging.

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
Explanation: We are creating the "Ticket Counter" (a session factory). An API request can't just walk up and talk to the engine. It needs a temporary "pass" or "ticket" to have a private conversation with the database. This async_session is the factory that hands out those temporary passes (sessions).

bind=engine: We are telling the ticket counter which engine to use.

expire_on_commit=False: This is an important setting for FastAPI that tells the session not to throw away its data immediately after a commit, which gives us more flexibility.

Base = declarative_base()
Explanation: We are creating our "Blueprint Factory". Base is just a simple Python class, but it has superpowers. Any new class we create that "inherits" from Base (like our User class) will be automatically tracked by SQLAlchemy as a blueprint for a database table.


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
Explanation: This is our "Construction Crew" function. We'll run this function once when our server starts.

async with engine.begin() as conn:: This opens a direct, powerful connection to the database.

await conn.run_sync(Base.metadata.create_all): This is the magic command. It tells the construction crew: "Find every single blueprint that was made from our Base factory (like the User blueprint), and build the tables in the database if they don't already exist."


>>>>>>> 32a6436 (Initial commit - DISHANVESHI full project)

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine, async_sessionmaker,)
from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()
engine = None
SessionLocal = None
active_database = None


def _add_missing_task_columns(sync_connection):
    task_columns = {
        column["name"]
        for column in inspect(sync_connection).get_columns("tasks")
    }
    if "due_at" not in task_columns:
        sync_connection.execute(
            text("ALTER TABLE tasks ADD COLUMN due_at TIMESTAMP WITH TIME ZONE")
        )


async def initialize_database():
    global engine, SessionLocal, active_database

    # Fist, try to connect to the primary database
    try:
        postgres_engine = create_async_engine(settings.database_url, pool_pre_ping=True, echo=True)
        async with postgres_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        engine = postgres_engine
        active_database = "postgreSQL"
        print("Connected to PostgreSQL database.")
    except Exception as error:
        print(f"PostgreSQl unavailable: {error}")
        print("Falling back to SQLite database.")

        # If the primary database is unavailable, fall back to SQLite

        if "postgres_engine" in locals():
            await postgres_engine.dispose()

        engine = create_async_engine(settings.sqlite_fallback_url, pool_pre_ping=True, echo=True)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        active_database = "SQLite"
        print("Connected to SQLite database.")

    # Create the session factory for the selected database
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_add_missing_task_columns)

async def close_database():
    global engine
    if engine:
        await engine.dispose()
        print(f"Closed connection to {active_database} database.") 

async def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database session is not initialized. Call 'initialize_database()' first.")
    async with SessionLocal() as session:
        yield session
    
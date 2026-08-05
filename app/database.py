from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import event
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

# echo=False keeps the terminal clean; set True temporarily if you need to debug SQL
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# WAL mode lets reads happen while a write is in progress — matters for SQLite
# under real usage (many students loading the ballot while others are voting).
# This only applies when using SQLite; it's a no-op for Postgres.
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")  # wait up to 5s if the DB is locked, instead of erroring
        cursor.close()


async def init_db():
    """Creates all tables that don't exist yet. Safe to run every startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    """FastAPI dependency — gives each request its own DB session."""
    async with async_session() as session:
        yield session

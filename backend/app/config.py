from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

DATABASE_URL = "postgresql+asyncpg://opendatacube:opendatacubepassword@localhost:5436/opendatacube"

# Create an async engine for SQLModel to connect to the PostgreSQL database
engine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Function to initialize the database (create tables if they don't exist)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .models import Base


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment/.env")


# Synchronous SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)




def check_connection() -> int:
    """Run a simple SELECT 1 to verify DB connectivity."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return result.scalar_one()
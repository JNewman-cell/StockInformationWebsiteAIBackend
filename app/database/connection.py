"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://username:password@ep-spring-boat-af0qnegb-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"
)

# Create SQLAlchemy engine with error handling
engine = None
SessionLocal = None
db_available = False

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False  # Set to True for SQL query logging
    )
    
    # Test connection
    with engine.connect() as conn:
        pass
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_available = True
except Exception as e:
    print(f"⚠️  WARNING: Database connection failed: {e}")
    print("   Database operations will not be available.")
    print("   Please check your DATABASE_URL in .env")
    db_available = False


def get_db() -> Generator[Optional[Session], None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    Returns None if database is not available.
    
    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            if db is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            # Use db session here
            pass
    """
    if not db_available or SessionLocal is None:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

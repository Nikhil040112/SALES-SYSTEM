# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# 🔴 CRITICAL: import ALL models so FKs resolve
from app.models.user import User
from app.models.lead import Lead          # ✅ THIS WAS MISSING
from app.models.call_log import CallLog
from app.models.call_follow_up import CallFollowUp

# 🔴 DEV-ONLY table creation
Base.metadata.create_all(bind=engine)
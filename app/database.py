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


# 🔴 CRITICAL: import models so SQLAlchemy knows them
from app.models.user import User
from app.models.call_log import CallLog
from app.models.call_follow_up import CallFollowUp


# 🔴 CRITICAL: create tables (dev-safe)
Base.metadata.create_all(bind=engine)
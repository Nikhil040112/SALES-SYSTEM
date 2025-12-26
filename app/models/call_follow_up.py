# app/models/call_follow_up.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CallFollowUp(Base):
    __tablename__ = "call_follow_ups"

    id = Column(Integer, primary_key=True)

    call_id = Column(
        Integer,
        ForeignKey("call_logs.id"),
        index=True,
        nullable=False
    )

    salesperson_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    outcome = Column(String, nullable=False)  # Connected / Busy / Not Picked / Purchased / Not Required
    remark = Column(String)

    follow_up_datetime = Column(DateTime, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to parent call
    call = relationship("CallLog", back_populates="follow_ups")
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True)

    call_id = Column(String, unique=True, index=True)

    # --------------------------------------------------
    # RELATIONS
    # --------------------------------------------------
    salesperson_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # ✅ NEW — LINK TO LEAD (FIRST CALL ONLY)
    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=True
    )

    # --------------------------------------------------
    # CUSTOMER / QUERY DETAILS
    # --------------------------------------------------
    query_source = Column(String)
    client_name = Column(String)
    contact_number = Column(String)
    query_product = Column(String)
    state = Column(String)

    # --------------------------------------------------
    # FIRST CALL OUTCOME (IMMUTABLE)
    # --------------------------------------------------
    call_outcome = Column(String)
    remark = Column(String)

    # ⛔ Deprecated — kept only for backward compatibility
    next_action = Column(String)
    follow_up_datetime = Column(DateTime)

    # --------------------------------------------------
    # STATUS / TIMESTAMPS
    # --------------------------------------------------
    status = Column(String, default="OPEN")  # OPEN / CLOSED
    completed_at = Column(DateTime)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # --------------------------------------------------
    # FOLLOW-UP RELATIONSHIP
    # --------------------------------------------------
    follow_ups = relationship(
        "CallFollowUp",
        back_populates="call",
        cascade="all, delete-orphan"
    )
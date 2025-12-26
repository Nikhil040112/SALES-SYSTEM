from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)

    client_name = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)

    query_source = Column(String)
    query_product = Column(String)
    state = Column(String)

    salesperson_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(
        String,
        default="NEW"   # NEW / CALLED / CLOSED
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------
    # One Lead → One First Call (CallLog)
    calls = relationship(
        "CallLog",
        backref="lead",
        primaryjoin="Lead.id == CallLog.lead_id"
    )
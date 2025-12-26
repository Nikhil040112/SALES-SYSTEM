from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.deps import get_current_user, get_db
from app.models.call_log import CallLog
from app.models.call_follow_up import CallFollowUp
from app.models.lead import Lead          # ✅ NEW
from app.models.user import User
import uuid

router = APIRouter(prefix="/calls", tags=["Calls"])


# ----------------------------
# CREATE LEAD OR FIRST CALL (PATCHED)
# ----------------------------
@router.post("/")
def create_call(
    data: dict,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    outcome = data.get("call_outcome")

    # =====================================================
    # CASE 1: NO OUTCOME → CREATE LEAD ONLY
    # =====================================================
    if not outcome:
        lead = Lead(
            client_name=data["client_name"],
            contact_number=data["contact_number"],
            query_source=data.get("query_source"),
            query_product=data.get("query_product"),
            state=data.get("state"),
            salesperson_id=user.id,
            status="NEW"
        )
        db.add(lead)
        db.commit()

        return {
            "message": "Lead created",
            "lead_id": lead.id
        }

    # =====================================================
    # CASE 2: OUTCOME PRESENT → FIRST CALL
    # =====================================================
    now = datetime.now()

    FOLLOW_UP_OUTCOMES = [
        "Connected",
        "Not Picked",
        "Busy",
        "Cut-In Between"
    ]

    status = "OPEN" if outcome in FOLLOW_UP_OUTCOMES else "CLOSED"

    follow_up_datetime_raw = data.pop("follow_up_datetime", None)
    follow_up_datetime = None

    if follow_up_datetime_raw:
        follow_up_datetime = datetime.fromisoformat(follow_up_datetime_raw)

    # 🔎 find or create lead
    lead = (
        db.query(Lead)
        .filter(
            Lead.contact_number == data["contact_number"],
            Lead.salesperson_id == user.id
        )
        .first()
    )

    if not lead:
        lead = Lead(
            client_name=data["client_name"],
            contact_number=data["contact_number"],
            query_source=data.get("query_source"),
            query_product=data.get("query_product"),
            state=data.get("state"),
            salesperson_id=user.id,
            status="CALLED"
        )
        db.add(lead)
        db.commit()

    # ❗ prevent duplicate first call
    existing_call = (
        db.query(CallLog)
        .filter(CallLog.lead_id == lead.id)
        .first()
    )
    if existing_call:
        raise HTTPException(
            status_code=400,
            detail="First call already logged for this lead"
        )

    call = CallLog(
        lead_id=lead.id,
        call_id=f"CALL-{uuid.uuid4().hex[:8].upper()}",
        salesperson_id=user.id,
        call_outcome=outcome,              # ✅ FIRST CALL ONLY
        status=status,
        follow_up_datetime=follow_up_datetime,
        client_name=data["client_name"],
        contact_number=data["contact_number"],
        query_source=data.get("query_source"),
        query_product=data.get("query_product"),
        state=data.get("state")
    )

    lead.status = "CALLED"

    db.add(call)
    db.commit()

    return {
        "message": "First call logged",
        "call_id": call.id
    }


# ----------------------------
# MY CALLS (UNCHANGED)
# ----------------------------
@router.get("/my")
def my_calls(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(CallLog)
        .filter(CallLog.salesperson_id == user.id)
        .order_by(CallLog.created_at.desc())
        .all()
    )

    return [
        {
            "id": c.id,
            "query_source": c.query_source,
            "client_name": c.client_name,
            "contact_number": c.contact_number,
            "query_product": c.query_product,
            "state": c.state,
            "call_outcome": c.call_outcome,
            "remark": c.remark,
            "status": c.status,
            "created_at": c.created_at,
            "follow_up_datetime": c.follow_up_datetime,
        }
        for c in rows
    ]

# ----------------------------
# ALL CALLS (SALESPERSON)
# ----------------------------
@router.get("/all-mine")
def all_my_calls(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    calls = (
        db.query(CallLog)
        .filter(CallLog.salesperson_id == user.id)
        .order_by(CallLog.created_at.desc())
        .all()
    )

    return [
        {
            "id": c.id,
            "client_name": c.client_name,
            "contact_number": c.contact_number,
            "query_source": c.query_source,
            "query_product": c.query_product,
            "state": c.state,
            "call_outcome": c.call_outcome,
            "status": c.status,
            "created_at": c.created_at,
            "follow_up_datetime": c.follow_up_datetime
        }
        for c in calls
    ]


# ----------------------------
# FOLLOW-UPS (PATCHED – READ FROM call_follow_ups)
# ----------------------------
@router.get("/follow-ups")
def get_follow_ups(user=Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now()
    result = []

    # ------------------------------------
    # 1️⃣ FIRST CALLS REQUIRING FOLLOW-UP
    # ------------------------------------
    first_calls = (
        db.query(CallLog)
        .filter(
            CallLog.salesperson_id == user.id,
            CallLog.status == "OPEN",   # ✅ IMPORTANT
            CallLog.call_outcome.in_([
                "Connected",
                "Busy",
                "Not Picked",
                "Cut-In Between"
            ])
        )
        .all()
    )

    for call in first_calls:
        has_followup = (
            db.query(CallFollowUp)
            .filter(CallFollowUp.call_id == call.id)
            .first()
        )
        if has_followup:
            continue

        is_overdue = call.follow_up_datetime and call.follow_up_datetime < now

        result.append({
            "id": call.id,
            "client_name": call.client_name,
            "call_outcome": call.call_outcome,
            "follow_up_datetime": call.follow_up_datetime,
            "is_overdue": is_overdue
        })

    # ------------------------------------
    # 2️⃣ ACTUAL FOLLOW-UPS (OPEN CALLS ONLY)
    # ------------------------------------
    followups = (
        db.query(CallFollowUp, CallLog)
        .join(CallLog, CallLog.id == CallFollowUp.call_id)
        .filter(
            CallFollowUp.salesperson_id == user.id,
            CallLog.status == "OPEN"    # ✅ IMPORTANT
        )
        .order_by(CallFollowUp.follow_up_datetime.asc())
        .all()
    )

    for f, call in followups:
        is_overdue = f.follow_up_datetime and f.follow_up_datetime < now

        result.append({
            "id": call.id,
            "client_name": call.client_name,
            "call_outcome": f.outcome,
            "follow_up_datetime": f.follow_up_datetime,
            "is_overdue": is_overdue
        })

    result.sort(key=lambda x: x["follow_up_datetime"] or datetime.max)
    return result

# ----------------------------
# ADD FOLLOW-UP
# ----------------------------
@router.post("/{call_id}/follow-up")
def add_follow_up(
    call_id: int,
    data: dict,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    call = db.query(CallLog).filter(CallLog.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    follow_dt = (
        datetime.fromisoformat(data["follow_up_datetime"])
        if data.get("follow_up_datetime")
        else None
    )

    # store follow-up action
    follow = CallFollowUp(
        call_id=call.id,
        salesperson_id=user.id,
        outcome=data.get("call_outcome"),
        remark=data.get("remark"),
        follow_up_datetime=follow_dt
    )
    db.add(follow)

    # ❌ DO NOT TOUCH call.call_outcome HERE

    if data.get("call_outcome") in ["Purchased", "Not Required"]:
        call.status = "CLOSED"
        call.completed_at = datetime.now()
        call.follow_up_datetime = None
    else:
        call.status = "OPEN"
        call.follow_up_datetime = follow_dt

    db.commit()
    return {"message": "Follow-up saved"}

# ----------------------------
# FOLLOW-UP HISTORY (FILTER CLOSURE)
# ----------------------------
@router.get("/{call_id}/follow-up-history")
def call_follow_up_history(
    call_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    call = db.query(CallLog).filter(CallLog.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404)

    if call.salesperson_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403)

    # ✅ IMPORTANT: DO NOT FILTER BY OUTCOME
    followups = (
        db.query(CallFollowUp)
        .filter(CallFollowUp.call_id == call.id)
        .order_by(CallFollowUp.created_at.asc())
        .all()
    )

    return {
        "call": {
            "id": call.id,
            "client_name": call.client_name,
            "contact_number": call.contact_number,
            "query_source": call.query_source,
            "query_product": call.query_product,
            "state": call.state,
            "first_call_outcome": call.call_outcome,
            "first_follow_up_datetime": call.follow_up_datetime,
            "created_at": call.created_at,
            "status": call.status
        },
        "followups": [
            {
                "outcome": f.outcome,
                "remark": f.remark,
                "follow_up_datetime": f.follow_up_datetime,
                "created_at": f.created_at
            }
            for f in followups
        ]
    }

# ----------------------------
# GET SINGLE CALL (UNCHANGED)
# ----------------------------
@router.get("/{call_id}")
def get_call(
    call_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    call = db.query(CallLog).filter(CallLog.id == call_id).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if user.role != "ADMIN" and call.salesperson_id != user.id:
        raise HTTPException(status_code=403)

    return {
        "id": call.id,
        "query_source": call.query_source,
        "client_name": call.client_name,
        "contact_number": call.contact_number,
        "query_product": call.query_product,
        "state": call.state,
        "call_outcome": call.call_outcome,
        "remark": call.remark,
    }


# ----------------------------
# UPDATE CALL (UNCHANGED)
# ----------------------------
@router.put("/{call_id}")
def update_call(
    call_id: int,
    data: dict,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    call = db.query(CallLog).filter(CallLog.id == call_id).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if call.salesperson_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=403)

    call.call_outcome = data.get("call_outcome", call.call_outcome)
    call.remark = data.get("remark", call.remark)

    if call.call_outcome in ["Not Required", "Purchased"]:
        call.status = "CLOSED"
        call.follow_up_datetime = None
        call.completed_at = datetime.now()

    db.commit()
    return {"message": "Call updated"}


# ----------------------------
# ADMIN VIEW (UNCHANGED)
# ----------------------------
@router.get("/")
def all_calls(
    salesperson_id: int | None = None,
    span: str | None = None,
    date: str | None = None,
    month: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin only")

    query = (
        db.query(
            CallLog,
            User.name.label("salesperson_name")
        )
        .join(User, User.id == CallLog.salesperson_id)
    )

    if salesperson_id:
        query = query.filter(CallLog.salesperson_id == salesperson_id)

    now = datetime.now()

    if span == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        query = query.filter(CallLog.created_at >= start, CallLog.created_at < end)

    elif span == "week":
        query = query.filter(CallLog.created_at >= now - timedelta(days=7))

    elif span == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(CallLog.created_at >= start)

    elif month:
        start = datetime.strptime(month + "-01", "%Y-%m-%d")
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        query = query.filter(CallLog.created_at >= start, CallLog.created_at < end)

    elif from_date and to_date:
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(CallLog.created_at >= start, CallLog.created_at < end)

    elif date:
        start = datetime.strptime(date, "%Y-%m-%d")
        end = start + timedelta(days=1)
        query = query.filter(CallLog.created_at >= start, CallLog.created_at < end)

    rows = query.all()

    return [
        {
            "id": c.id,
            "client_name": c.client_name,
            "query_product": c.query_product,
            "call_outcome": c.call_outcome,
            "status": c.status,
            "created_at": c.created_at,
            "salesperson_name": salesperson_name,
            "is_follow_up": c.status == "OPEN",
            "is_overdue": (
                c.status == "OPEN"
                and c.follow_up_datetime
                and c.follow_up_datetime < now
            )
        }
        for c, salesperson_name in rows
    ]

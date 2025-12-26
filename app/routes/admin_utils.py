from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date

from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.lead import Lead
from app.models.call_log import CallLog
from app.models.call_follow_up import CallFollowUp

router = APIRouter(prefix="/admin", tags=["Admin Utils"])


# ==================================================
# SALESPERSON LIST (UNCHANGED)
# ==================================================
@router.get("/salespersons")
def get_salespersons(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "ADMIN":
        return []

    rows = (
        db.query(User.id, User.name)
        .filter(User.role == "SALESPERSON")
        .order_by(User.name.asc())
        .all()
    )

    return [{"id": r.id, "name": r.name} for r in rows]


# ==================================================
# INTERNAL: DATE RANGE RESOLVER (EXTENDED)
# ==================================================
def resolve_date_range(
    *,
    single_date: str | None,
    month: str | None,
    from_date: str | None,
    to_date: str | None,
    span: str | None
):
    """
    Priority order:
    1. single_date (YYYY-MM-DD)
    2. month (YYYY-MM)
    3. from_date / to_date
    4. span (today / week / month)
    5. all time
    """
    now = datetime.now()
    start = None
    end = None

    # -------------------------------
    # 1️⃣ SINGLE DATE
    # -------------------------------
    if single_date:
        d = datetime.fromisoformat(single_date)
        start = d.replace(hour=0, minute=0, second=0, microsecond=0)
        end = d.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    # -------------------------------
    # 2️⃣ MONTH (YYYY-MM)
    # -------------------------------
    if month:
        year, mon = map(int, month.split("-"))
        start = datetime(year, mon, 1)
        if mon == 12:
            end = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
        else:
            end = datetime(year, mon + 1, 1) - timedelta(microseconds=1)
        return start, end

    # -------------------------------
    # 3️⃣ CUSTOM RANGE
    # -------------------------------
    if from_date:
        start = datetime.fromisoformat(from_date)

    if to_date:
        end = datetime.fromisoformat(to_date).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    if start or end:
        return start, end

    # -------------------------------
    # 4️⃣ SPAN PRESETS
    # -------------------------------
    if span == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif span == "week":
        start = now - timedelta(days=7)
        end = now
    elif span == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now

    return start, end


# ==================================================
# ADMIN KPI / OVERVIEW
# ==================================================
@router.get("/kpis")
def admin_kpis(
    salesperson_id: int | None = None,
    single_date: str | None = None,
    month: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    span: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403)

    start, end = resolve_date_range(
        single_date=single_date,
        month=month,
        from_date=from_date,
        to_date=to_date,
        span=span
    )

    lead_q = db.query(Lead)
    call_q = db.query(CallLog)
    followup_q = db.query(CallFollowUp)

    if salesperson_id:
        lead_q = lead_q.filter(Lead.salesperson_id == salesperson_id)
        call_q = call_q.filter(CallLog.salesperson_id == salesperson_id)
        followup_q = followup_q.filter(CallFollowUp.salesperson_id == salesperson_id)

    if start:
        lead_q = lead_q.filter(Lead.created_at >= start)
        call_q = call_q.filter(CallLog.created_at >= start)
        followup_q = followup_q.filter(CallFollowUp.created_at >= start)

    if end:
        lead_q = lead_q.filter(Lead.created_at <= end)
        call_q = call_q.filter(CallLog.created_at <= end)
        followup_q = followup_q.filter(CallFollowUp.created_at <= end)

    # --------------------------------
    # LEADS
    # --------------------------------
    total_leads = lead_q.count()
    new_leads = lead_q.filter(Lead.status == "NEW").count()
    called_leads = lead_q.filter(Lead.status == "CALLED").count()

    # --------------------------------
    # CALLS
    # --------------------------------
    total_calls = call_q.count()

    closed_calls = call_q.filter(
        CallLog.status == "CLOSED"
    ).count()

    # Purchased can be from FIRST CALL or FOLLOW-UP
    purchased_from_calls = call_q.filter(
        CallLog.call_outcome == "Purchased"
    ).count()

    purchased_from_followups = followup_q.filter(
        CallFollowUp.outcome == "Purchased"
    ).count()

    purchased = purchased_from_calls + purchased_from_followups

    # --------------------------------
    # FOLLOW-UPS
    # --------------------------------
    now = datetime.now()
    pending_followups = call_q.filter(
        CallLog.status == "OPEN",
        CallLog.follow_up_datetime != None,
        CallLog.follow_up_datetime <= now
    ).count()

    conversion_rate = (
        round((purchased / total_calls) * 100, 2)
        if total_calls else 0
    )

    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "called_leads": called_leads,
        "closed_leads": closed_calls,
        "total_calls": total_calls,
        "purchased": purchased,
        "pending_followups": pending_followups,
        "conversion_rate": conversion_rate
    }


# ==================================================
# ADMIN LEADS
# ==================================================
@router.get("/leads")
def admin_leads(
    salesperson_id: int | None = None,
    single_date: str | None = None,
    month: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    span: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403)

    start, end = resolve_date_range(
        single_date=single_date,
        month=month,
        from_date=from_date,
        to_date=to_date,
        span=span
    )

    q = db.query(Lead, User.name).join(User, User.id == Lead.salesperson_id)

    if salesperson_id:
        q = q.filter(Lead.salesperson_id == salesperson_id)

    if start:
        q = q.filter(Lead.created_at >= start)
    if end:
        q = q.filter(Lead.created_at <= end)

    rows = q.order_by(Lead.created_at.desc()).all()

    return [
        {
            "id": l.id,
            "client_name": l.client_name,
            "contact_number": l.contact_number,
            "query_source": l.query_source,
            "query_product": l.query_product,
            "state": l.state,
            "status": l.status,
            "created_at": l.created_at,
            "salesperson": salesperson_name
        }
        for l, salesperson_name in rows
    ]


# ==================================================
# ADMIN CALLS
# ==================================================
@router.get("/calls")
def admin_calls(
    salesperson_id: int | None = None,
    single_date: str | None = None,
    month: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    span: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403)

    start, end = resolve_date_range(
        single_date=single_date,
        month=month,
        from_date=from_date,
        to_date=to_date,
        span=span
    )

    q = db.query(CallLog, User.name).join(User, User.id == CallLog.salesperson_id)

    if salesperson_id:
        q = q.filter(CallLog.salesperson_id == salesperson_id)

    if start:
        q = q.filter(CallLog.created_at >= start)
    if end:
        q = q.filter(CallLog.created_at <= end)

    rows = q.order_by(CallLog.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "client_name": c.client_name,
            "contact_number": c.contact_number,
            "query_product": c.query_product,
            "call_outcome": c.call_outcome,
            "status": c.status,
            "follow_up_datetime": c.follow_up_datetime,
            "created_at": c.created_at,
            "salesperson": salesperson_name
        }
        for c, salesperson_name in rows
    ]


# ==================================================
# ADMIN PERFORMANCE CARDS (PER SALESPERSON)
# ==================================================
@router.get("/performance-cards")
def admin_performance_cards(
    span: str | None = None,
    single_date: str | None = None,
    month: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403)

    start, end = resolve_date_range(
        single_date=single_date,
        month=month,
        from_date=from_date,
        to_date=to_date,
        span=span
    )

    salespersons = db.query(User).filter(User.role == "SALESPERSON").all()
    out = []

    for sp in salespersons:
        lead_q = db.query(Lead).filter(Lead.salesperson_id == sp.id)
        call_q = db.query(CallLog).filter(CallLog.salesperson_id == sp.id)
        followup_q = db.query(CallFollowUp).filter(CallFollowUp.salesperson_id == sp.id)

        if start:
            lead_q = lead_q.filter(Lead.created_at >= start)
            call_q = call_q.filter(CallLog.created_at >= start)
            followup_q = followup_q.filter(CallFollowUp.created_at >= start)

        if end:
            lead_q = lead_q.filter(Lead.created_at <= end)
            call_q = call_q.filter(CallLog.created_at <= end)
            followup_q = followup_q.filter(CallFollowUp.created_at <= end)

        total_leads = lead_q.count()
        new_leads = lead_q.filter(Lead.status == "NEW").count()

        total_calls = call_q.count()

        purchased_calls = call_q.filter(
            CallLog.call_outcome == "Purchased"
        ).count()

        purchased_followups = followup_q.filter(
            CallFollowUp.outcome == "Purchased"
        ).count()

        purchased = purchased_calls + purchased_followups

        conversion = (
            round((purchased / total_calls) * 100, 2)
            if total_calls else 0
        )

        out.append({
            "salesperson": sp.name,
            "total_leads": total_leads,
            "new_leads": new_leads,
            "total_calls": total_calls,
            "purchased": purchased,
            "conversion_rate": conversion
        })

    return out
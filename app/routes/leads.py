from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_current_user, get_db
from app.models.lead import Lead

router = APIRouter(prefix="/leads", tags=["Leads"])


# ----------------------------
# GET MY LEADS (SALESPERSON)
# ----------------------------
@router.get("/my")
def my_leads(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leads = (
        db.query(Lead)
        .filter(Lead.salesperson_id == user.id)
        .order_by(Lead.created_at.desc())
        .all()
    )

    return [
        {
            "id": l.id,
            "client_name": l.client_name,
            "contact_number": l.contact_number,
            "query_source": l.query_source,
            "query_product": l.query_product,
            "state": l.state,
            "status": l.status,          # ✅ REQUIRED
            "created_at": l.created_at
        }
        for l in leads
    ]


# ----------------------------
# GET SINGLE LEAD
# ----------------------------
@router.get("/{lead_id}")
def get_lead(
    lead_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.salesperson_id != user.id:
        raise HTTPException(status_code=403)

    return {
        "id": lead.id,
        "client_name": lead.client_name,
        "contact_number": lead.contact_number,
        "query_source": lead.query_source,
        "query_product": lead.query_product,
        "state": lead.state,
        "status": lead.status,
        "created_at": lead.created_at
    }
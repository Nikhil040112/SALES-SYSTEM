from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.call_log import CallLog
from app.models.call_follow_up import CallFollowUp
from app.models.lead import Lead
from app.models.user import User
from app.utils.mailer import send_email
from app.utils.mail_templates import (
    followup_reminder,
    daily_summary
)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
IST = pytz.timezone("Asia/Kolkata")
CHECK_WINDOW_MINUTES = 5  # scheduler interval


# ==================================================
# PRE-OVERDUE FOLLOW-UP REMINDER (ONCE ONLY)
# ==================================================
def send_followup_reminders():
    """
    Rules:
    - Send reminder ONLY ONCE
    - If gap < 1 hour → 15 mins before follow-up
    - Else → 30 mins before follow-up
    """

    db: Session = SessionLocal()
    now = datetime.now(IST)
    window_end = now + timedelta(minutes=CHECK_WINDOW_MINUTES)

    # --------------------------------------------------
    # 1️⃣ FIRST CALL FOLLOW-UPS (CallLog)
    # --------------------------------------------------
    calls = (
        db.query(CallLog)
        .filter(
            CallLog.status == "OPEN",
            CallLog.follow_up_datetime.isnot(None),
            CallLog.follow_up_datetime > now
        )
        .all()
    )

    for call in calls:
        created_at = call.created_at
        follow_at = call.follow_up_datetime

        gap_minutes = (follow_at - created_at).total_seconds() / 60
        reminder_offset = 15 if gap_minutes < 60 else 30
        reminder_time = follow_at - timedelta(minutes=reminder_offset)

        # 🔐 trigger only once inside narrow window
        if reminder_time <= now < window_end:
            user = db.query(User).get(call.salesperson_id)

            send_email(
                to_email=user.email,
                subject="Upcoming Follow-up Reminder",
                html_content=followup_reminder(
                    user_name=user.name,
                    client_name=call.client_name,
                    follow_time=follow_at.strftime("%d %b %I:%M %p")
                )
            )

    # --------------------------------------------------
    # 2️⃣ ACTUAL FOLLOW-UPS (CallFollowUp)
    # --------------------------------------------------
    followups = (
        db.query(CallFollowUp, CallLog)
        .join(CallLog, CallLog.id == CallFollowUp.call_id)
        .filter(
            CallLog.status == "OPEN",
            CallFollowUp.follow_up_datetime.isnot(None),
            CallFollowUp.follow_up_datetime > now
        )
        .all()
    )

    for followup, call in followups:
        created_at = followup.created_at
        follow_at = followup.follow_up_datetime

        gap_minutes = (follow_at - created_at).total_seconds() / 60
        reminder_offset = 15 if gap_minutes < 60 else 30
        reminder_time = follow_at - timedelta(minutes=reminder_offset)

        if reminder_time <= now < window_end:
            user = db.query(User).get(followup.salesperson_id)

            send_email(
                to_email=user.email,
                subject="Upcoming Follow-up Reminder",
                html_content=followup_reminder(
                    user_name=user.name,
                    client_name=call.client_name,
                    follow_time=follow_at.strftime("%d %b %I:%M %p")
                )
            )

    db.close()


# ==================================================
# DAILY 8 PM SUMMARY (PER SALESPERSON)
# ==================================================
def send_daily_summary():
    db: Session = SessionLocal()

    salespersons = (
        db.query(User)
        .filter(User.role == "SALESPERSON")
        .all()
    )

    for user in salespersons:

        # -------------------------------
        # Pending Leads
        # -------------------------------
        leads = (
            db.query(Lead)
            .filter(
                Lead.salesperson_id == user.id,
                Lead.status.in_(["NEW", "CALLED"])
            )
            .all()
        )

        # -------------------------------
        # Pending / Overdue Follow-ups
        # -------------------------------
        followups = []

        # First-call follow-ups
        calls = (
            db.query(CallLog)
            .filter(
                CallLog.salesperson_id == user.id,
                CallLog.status == "OPEN",
                CallLog.follow_up_datetime.isnot(None)
            )
            .all()
        )

        for call in calls:
            followups.append({
                "client": call.client_name,
                "time": call.follow_up_datetime.strftime("%d %b %I:%M %p")
            })

        # Actual follow-ups
        fups = (
            db.query(CallFollowUp, CallLog)
            .join(CallLog, CallLog.id == CallFollowUp.call_id)
            .filter(
                CallFollowUp.salesperson_id == user.id,
                CallLog.status == "OPEN"
            )
            .all()
        )

        for f, call in fups:
            followups.append({
                "client": call.client_name,
                "time": f.follow_up_datetime.strftime("%d %b %I:%M %p")
            })

        send_email(
            to_email=user.email,
            subject="Daily Pending Summary – Sales Pro",
            html_content=daily_summary(
                user_name=user.name,
                leads=leads,
                followups=followups
            )
        )

    db.close()
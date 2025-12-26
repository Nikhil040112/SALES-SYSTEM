from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from app.routes import frontend, calls, auth_api, admin_utils, leads
from app.utils.scheduler import (
    send_followup_reminders,
    send_daily_summary
)
from app.config import TIMEZONE


app = FastAPI(title="Sales Call Reporting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/login")


app.include_router(frontend.router)
app.include_router(auth_api.router)
app.include_router(calls.router)
app.include_router(admin_utils.router)
app.include_router(leads.router)


# --------------------------------------------------
# SCHEDULER SETUP (NEW)
# --------------------------------------------------
scheduler = BackgroundScheduler(
    timezone=pytz.timezone(TIMEZONE)
)

# 🔔 Pre-overdue follow-up reminders
scheduler.add_job(
    send_followup_reminders,
    trigger="interval",
    minutes=5,
    id="followup_reminders",
    replace_existing=True
)

# 🌙 Daily 8 PM summary
scheduler.add_job(
    send_daily_summary,
    trigger="cron",
    hour=20,
    minute=0,
    id="daily_summary",
    replace_existing=True
)

scheduler.start()
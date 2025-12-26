from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Frontend"])
templates = Jinja2Templates(directory="frontend")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/call-details", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("call_details.html", {"request": request})

@router.get("/follow-ups")
def follow_ups_page(request: Request):
    return templates.TemplateResponse(
        "follow_up.html",
        {"request": request}
    )
@router.get("/all-calls")
def all_calls_page(request: Request):
    return templates.TemplateResponse(
        "all_calls.html",
        {"request": request}
    )

@router.get("/leads")
def leads_page(request: Request):
    return templates.TemplateResponse(
        "leads.html",
        {"request": request}
    )

@router.get("/admin-performance")
def admin_performance_page(request: Request):
    return templates.TemplateResponse(
        "admin_performance.html",
        {"request": request}
    )
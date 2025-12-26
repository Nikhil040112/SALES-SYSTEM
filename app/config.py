from dotenv import load_dotenv
import os

load_dotenv()

# -------------------------------------------------
# CORE APP SETTINGS (UNCHANGED)
# -------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# -------------------------------------------------
# MAIL SETTINGS (NEW)
# -------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

MAIL_FROM = os.getenv(
    "MAIL_FROM",
    "Sales Pro <no-reply@salespro.com>"
)

# -------------------------------------------------
# TIMEZONE (NEW)
# -------------------------------------------------
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
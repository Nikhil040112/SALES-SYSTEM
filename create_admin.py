from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password
from app.utils.enums import RoleEnum

db = SessionLocal()

admin = User(
    name="Admin",
    email="surjeetinternational789@gmail.com",
    password_hash=hash_password("Muskan1"),
    role=RoleEnum.ADMIN
)

db.add(admin)
db.commit()
db.close()

print("✅ Admin user created")
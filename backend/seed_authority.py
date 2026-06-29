import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models import Authority, AuthorityUser

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Kanpur city ID
KANPUR_CITY_ID = UUID("26484efc-20a0-4a15-8686-a724b161598d")

# Check if already seeded
existing = db.query(AuthorityUser).filter(AuthorityUser.email == "admin@kanpur.gov.in").first()
if existing:
    print("Authority user already seeded.")
    db.close()
    sys.exit(0)

# Create Authority
from uuid import uuid4
auth_id = uuid4()
authority = Authority(
    id=auth_id,
    name="Kanpur Municipal Corporation",
    type="municipal_corporation",
    city_id=KANPUR_CITY_ID,
    contact_email="contact@kanpur.gov.in",
    contact_phone="+915122560000",
    is_active=True,
)
db.add(authority)
db.commit()

# Create admin user
admin_id = uuid4()
admin = AuthorityUser(
    id=admin_id,
    authority_id=auth_id,
    email="admin@kanpur.gov.in",
    password_hash=get_password_hash("admin123"),
    name="Admin User",
    role="admin",
    is_active=True,
)
db.add(admin)
db.commit()

print(f"Seeded authority: {authority.name} ({auth_id})")
print(f"Seeded admin user: {admin.email} ({admin_id})")
print("Login with: admin@kanpur.gov.in / admin123")
db.close()
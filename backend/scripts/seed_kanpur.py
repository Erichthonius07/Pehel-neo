"""Seed Kanpur geography data for Pehel Neo."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.base import engine
from app.models import State, City, Ward, Authority, AuthorityUser
from app.core.security import get_password_hash

SEED_DATA = {
    "country": "India",
    "state": {"name": "Uttar Pradesh", "code": "UP"},
    "city": {"name": "Kanpur", "is_pilot": True, "center_lat": 26.4499, "center_lng": 80.3319},
    "wards": [
        {"name": "Civil Lines", "ward_number": "8", "center_lat": 26.4674, "center_lng": 80.3497},
        {"name": "Swaroop Nagar", "ward_number": "12", "center_lat": 26.4850, "center_lng": 80.3412},
        {"name": "Kidwai Nagar", "ward_number": "34", "center_lat": 26.4590, "center_lng": 80.3650},
        {"name": "Govind Nagar", "ward_number": "56", "center_lat": 26.4423, "center_lng": 80.3089},
        {"name": "Arya Nagar", "ward_number": "23", "center_lat": 26.4601, "center_lng": 80.3201},
    ],
    "authority": {"name": "Municipal Corporation – Kanpur", "type": "municipal"},
}

def seed():
    with Session(engine) as session:
        existing = session.query(State).filter(State.code == "UP").first()
        if existing:
            print("Kanpur data already seeded. Skipping.")
            return

        state = State(name=SEED_DATA["state"]["name"], code=SEED_DATA["state"]["code"])
        session.add(state)
        session.flush()
        print(f"Created state: {state.name} ({state.id})")

        city = City(state_id=state.id, name=SEED_DATA["city"]["name"], is_pilot=SEED_DATA["city"]["is_pilot"])
        session.add(city)
        session.flush()
        print(f"Created city: {city.name} ({city.id})")

        for ward_data in SEED_DATA["wards"]:
            ward = Ward(city_id=city.id, name=ward_data["name"], ward_number=ward_data["ward_number"])
            session.add(ward)
            print(f"  Created ward: {ward.name} ({ward.ward_number})")

        session.flush()

        authority = Authority(
            name=SEED_DATA["authority"]["name"],
            type=SEED_DATA["authority"]["type"],
            city_id=city.id,
            contact_email="admin@kanpurmc.org",
            contact_phone="+91-512-1234567",
            is_active=True,
        )
        session.add(authority)
        session.flush()
        print(f"Created authority: {authority.name} ({authority.id})")

        admin_user = AuthorityUser(
            authority_id=authority.id,
            email="admin@kanpurmc.org",
            password_hash=get_password_hash("admin123"),
            name="System Administrator",
            role="admin",
            is_active=True,
        )
        session.add(admin_user)
        print(f"Created admin user: {admin_user.email} (role: {admin_user.role})")

        session.commit()
        print("\nSeed complete! Kanpur geography + authority admin ready.")

if __name__ == "__main__":
    seed()

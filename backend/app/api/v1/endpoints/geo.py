from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db.base import get_db
from app.api.deps import get_current_citizen

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/cities")
def list_cities(db: Session = Depends(get_db)):
    """List all cities."""
    from app.models import City
    cities = db.query(City).options(joinedload(City.state)).all()
    return [{"id": str(c.id), "name": c.name, "state": c.state.name if c.state else None} for c in cities]


@router.get("/cities/{city_id}")
def get_city(city_id: str, db: Session = Depends(get_db)):
    """Get city by ID with ward count."""
    from app.models import City, Ward
    from uuid import UUID
    
    city = db.query(City).options(joinedload(City.state)).filter(City.id == UUID(city_id)).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    ward_count = db.query(Ward).filter(Ward.city_id == city.id).count()
    
    return {
        "id": str(city.id),
        "name": city.name,
        "state": city.state.name if city.state else None,
        "ward_count": ward_count,
    }


@router.get("/cities/{city_id}/wards")
def get_city_wards(city_id: str, db: Session = Depends(get_db)):
    """Get all wards for a city."""
    from app.models import Ward
    from uuid import UUID
    
    wards = db.query(Ward).filter(Ward.city_id == UUID(city_id)).all()
    return [
        {
            "id": str(w.id),
            "name": w.name,
            "ward_number": w.ward_number,
        }
        for w in wards
    ]


@router.get("/wards/{ward_id}")
def get_ward(ward_id: str, db: Session = Depends(get_db)):
    """Get ward by ID."""
    from app.models import Ward
    from uuid import UUID
    
    ward = db.query(Ward).filter(Ward.id == UUID(ward_id)).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    return {
        "id": str(ward.id),
        "name": ward.name,
        "ward_number": ward.ward_number,
        "city_id": str(ward.city_id),
    }

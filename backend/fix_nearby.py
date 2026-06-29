with open('app/api/v1/endpoints/feed.py', 'r', encoding='utf-8') as f:
    content = f.read()

nearby_endpoint = '''

@router.get("/nearby", response_model=List[IssueListResponse])
def get_nearby_issues(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(1000, ge=100, le=10000),
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get issues within a radius of given lat/lng. Public."""
    from sqlalchemy import func
    from app.models import Issue
    from math import radians, cos, sin, asin, sqrt
    
    # Rough bounding box filter first (1 degree ~ 111km)
    deg_radius = radius_meters / 111000.0
    min_lat = lat - deg_radius
    max_lat = lat + deg_radius
    min_lng = lng - deg_radius
    max_lng = lng + deg_radius
    
    query = db.query(Issue).filter(
        Issue.geo_lat >= min_lat,
        Issue.geo_lat <= max_lat,
        Issue.geo_lng >= min_lng,
        Issue.geo_lng <= max_lng,
    )
    
    if category:
        query = query.filter(Issue.category == category)
    
    # Exclude closed/resolved
    query = query.filter(Issue.state.notin_(["closed", "resolved_confirmed"]))
    
    issues = query.order_by(Issue.priority_score.desc(), Issue.created_at.desc()).all()
    
    # Haversine distance filter
    def haversine(lat1, lng1, lat2, lng2):
        R = 6371000  # meters
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        dphi = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlng/2)**2
        return 2 * R * asin(sqrt(a))
    
    result = []
    for issue in issues:
        dist = haversine(lat, lng, float(issue.geo_lat), float(issue.geo_lng))
        if dist <= radius_meters:
            result.append(issue)
            if len(result) >= limit:
                break
    
    return result
'''

content = content.rstrip() + nearby_endpoint + '\n'

with open('app/api/v1/endpoints/feed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added nearby endpoint to feed.py')
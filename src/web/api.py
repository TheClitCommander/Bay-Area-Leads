"""
FastAPI backend for the Property Finder web interface
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..interface.property_finder import PropertyFinder
from ..services.db_service import DatabaseService

app = FastAPI(
    title="Property Finder",
    description="A beautiful interface for finding and analyzing properties",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
finder = PropertyFinder()
db = DatabaseService()

class SearchResponse(BaseModel):
    """Clean, consistent response format"""
    results: List[dict]
    total: int
    page: int
    has_more: bool

@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number"),
    filters: Optional[str] = Query(None, description="JSON encoded filters")
) -> SearchResponse:
    """Smart search endpoint that handles everything"""
    try:
        results = finder.quick_find(q)
        return SearchResponse(
            results=results[(page-1)*10:page*10],
            total=len(results),
            page=page,
            has_more=len(results) > page*10
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/{property_id}")
async def get_property(property_id: int):
    """Get detailed property information"""
    try:
        details = finder.get_property_details(property_id)
        if not details:
            raise HTTPException(status_code=404, detail="Property not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/{property_id}/preview")
async def get_preview(property_id: int):
    """Get quick property preview"""
    try:
        preview = finder.get_property_preview(property_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Property not found")
        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/{property_id}/suggestions")
async def get_suggestions(property_id: int):
    """Get smart suggestions for a property"""
    try:
        suggestions = finder.get_smart_suggestions(property_id)
        if not suggestions:
            raise HTTPException(status_code=404, detail="Property not found")
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map/properties")
async def get_map_properties(
    bounds: str = Query(..., description="Map bounds: lat1,lng1,lat2,lng2"),
    filters: Optional[str] = Query(None, description="JSON encoded filters")
):
    """Get properties within map bounds"""
    try:
        lat1, lng1, lat2, lng2 = map(float, bounds.split(","))
        properties = finder.find_in_bounds(lat1, lng1, lat2, lng2)
        return {"properties": properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/saved-searches")
async def get_saved_searches():
    """Get user's saved searches"""
    try:
        searches = [
            {
                "id": 1,
                "name": "Downtown Brunswick",
                "query": "downtown brunswick",
                "filters": {"max_price": 500000},
                "last_run": datetime.now().isoformat()
            }
        ]
        return {"searches": searches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/market-trends")
async def get_market_trends(
    area: Optional[str] = Query(None, description="Area to analyze"),
    timeframe: str = Query("1y", description="Timeframe: 1m, 3m, 6m, 1y, 5y")
):
    """Get market trend analytics"""
    try:
        trends = {
            "median_price": [
                {"date": "2023-01", "value": 300000},
                {"date": "2023-02", "value": 305000},
                # ... more data points
            ],
            "inventory": [
                {"date": "2023-01", "value": 150},
                {"date": "2023-02", "value": 160},
                # ... more data points
            ]
        }
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

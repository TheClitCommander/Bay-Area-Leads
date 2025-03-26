"""
Sample data for testing Brunswick data collectors and reporters
"""
from datetime import datetime, timedelta

# Sample business data
SAMPLE_BUSINESSES = [
    {
        "id": "BUS001",
        "name": "Brunswick Cafe",
        "type": "RESTAURANT",
        "address": "123 Maine Street, Brunswick, ME 04011",
        "founding_date": "2020-01-15",
        "license_status": "ACTIVE",
        "license_number": "BL123456",
        "health_inspection": 1,
        "food_license": 1,
        "neighborhood": "Downtown",
        "last_updated": "2025-02-01"
    },
    {
        "id": "BUS002",
        "name": "Coastal Inn",
        "type": "LODGING",
        "address": "456 Pleasant Street, Brunswick, ME 04011",
        "founding_date": "2018-06-20",
        "license_status": "ACTIVE",
        "license_number": "BL234567",
        "health_inspection": 1,
        "food_license": 0,
        "neighborhood": "Pleasant Street",
        "last_updated": "2025-01-15"
    },
    {
        "id": "BUS003",
        "name": "Maine Street Books",
        "type": "RETAIL",
        "address": "789 Maine Street, Brunswick, ME 04011",
        "founding_date": "2015-03-10",
        "license_status": "ACTIVE",
        "license_number": "BL345678",
        "health_inspection": 0,
        "food_license": 0,
        "neighborhood": "Downtown",
        "last_updated": "2025-02-10"
    }
]

# Sample property data
SAMPLE_PROPERTIES = [
    {
        "id": "PROP001",
        "map_lot": "123-A-45",
        "address": "123 Maine Street, Brunswick, ME 04011",
        "type": "COMMERCIAL",
        "zoning": "C1",
        "assessment": 500000,
        "neighborhood": "Downtown",
        "permit_status": "ACTIVE",
        "permit_type": "RENOVATION",
        "permit_value": 75000,
        "last_updated": "2025-02-01"
    },
    {
        "id": "PROP002",
        "map_lot": "234-B-67",
        "address": "456 Pleasant Street, Brunswick, ME 04011",
        "type": "COMMERCIAL",
        "zoning": "C2",
        "assessment": 750000,
        "neighborhood": "Pleasant Street",
        "permit_status": "ACTIVE",
        "permit_type": "NEW_CONSTRUCTION",
        "permit_value": 250000,
        "last_updated": "2025-01-15"
    },
    {
        "id": "PROP003",
        "map_lot": "345-C-89",
        "address": "789 Maine Street, Brunswick, ME 04011",
        "type": "COMMERCIAL",
        "zoning": "C1",
        "assessment": 450000,
        "neighborhood": "Downtown",
        "permit_status": "ACTIVE",
        "permit_type": "CHANGE_OF_USE",
        "permit_value": 25000,
        "last_updated": "2025-02-10"
    }
]

# Sample license data
SAMPLE_LICENSES = [
    {
        "id": "LIC001",
        "business_id": "BUS001",
        "license_number": "BL123456",
        "type": "FOOD_SERVICE",
        "issue_date": "2024-01-15",
        "expiration_date": "2025-01-14",
        "status": "ACTIVE"
    },
    {
        "id": "LIC002",
        "business_id": "BUS002",
        "license_number": "BL234567",
        "type": "LODGING",
        "issue_date": "2024-06-20",
        "expiration_date": "2025-06-19",
        "status": "ACTIVE"
    },
    {
        "id": "LIC003",
        "business_id": "BUS003",
        "license_number": "BL345678",
        "type": "RETAIL",
        "issue_date": "2024-03-10",
        "expiration_date": "2025-03-09",
        "status": "ACTIVE"
    }
]

# Sample historical data (last 12 months)
def generate_historical_data():
    historical = {
        "businesses": [],
        "properties": []
    }
    
    now = datetime.now()
    
    for i in range(12):
        period_start = now - timedelta(days=30 * (i + 1))
        period_end = now - timedelta(days=30 * i)
        
        # Add period information
        period_data = {
            "period": i,
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat(),
            "total": len(SAMPLE_BUSINESSES) - i % 3,  # Simulate growth
            "new_businesses": i % 2,  # Simulate new business creation
            "avg_value": 500000 + i * 10000  # Simulate value growth
        }
        
        historical["businesses"].append(period_data)
        
    return historical

# Generate test data
TEST_DATA = {
    "businesses": SAMPLE_BUSINESSES,
    "properties": SAMPLE_PROPERTIES,
    "licenses": SAMPLE_LICENSES,
    "historical": generate_historical_data()
}

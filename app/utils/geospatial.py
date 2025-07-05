from typing import List, Dict


async def get_nearby_reports(db, latitude: float, longitude: float, max_distance: float = 1000) -> List[Dict]:
    return await db.reports.find({
        "location.coordinates": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "$maxDistance": max_distance
            }
        }
    }).to_list(None)


async def get_reports_in_polygon(db, polygon_coordinates: List[List[List[float]]]) -> List[Dict]:
    return await db.reports.find({
        "location.coordinates": {
            "$geoWithin": {
                "$geometry": {
                    "type": "Polygon",
                    "coordinates": polygon_coordinates
                }
            }
        }
    }).to_list(None)

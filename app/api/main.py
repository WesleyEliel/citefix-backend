from fastapi import APIRouter

from app.api.v1.routes import reports, settings, comments, zones, notifications, auth, votes
from app.api.v1.routes import users, interventions, analytics

api_router = APIRouter()

version = "v1"

api_router.include_router(auth.router, prefix=f"/api/{version}/auth", tags=["Authentification"])
api_router.include_router(users.router, prefix=f"/api/{version}/users", tags=["Utilisateurs"])
api_router.include_router(reports.router, prefix=f"/api/{version}/reports", tags=["Signalements"])
api_router.include_router(interventions.router, prefix=f"/api/{version}/interventions", tags=["Interventions"])
api_router.include_router(comments.router, prefix=f"/api/{version}/comments", tags=["Commentaires"])
api_router.include_router(notifications.router, prefix=f"/api/{version}/notifications", tags=["Notifications"])
api_router.include_router(votes.router, prefix=f"/api/{version}/votes", tags=["Votes"])
api_router.include_router(zones.router, prefix=f"/api/{version}/zones", tags=["Zones"])
api_router.include_router(analytics.router, prefix=f"/api/{version}/analytics", tags=["analytics"])
api_router.include_router(settings.router, prefix=f"/api/{version}/settings", tags=["Paramètres"])

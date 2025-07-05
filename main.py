import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.configs import settings
from app.db.mongodb import connect_to_db, close_db_connection


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


# if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
#     sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    docs_url="/"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_db_client():
    await connect_to_db()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_db_connection()


app.include_router(api_router, prefix="")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
